"""Financial reporting engine.

Builds the three core statements from posted journal-entry lines
(not from cached balances), scoped by company and date range:
- trial_balance(company, as_of)
- income_statement(company, date_from, date_to)
- balance_sheet(company, as_of)
Each returns a plain dict ready for JSON, PDF, or Excel rendering.
"""
from decimal import Decimal

from decimal import Decimal
from django.db.models import Sum, Q, Count
from apps.accounts.models import JournalEntry
import django.db.models as models

from apps.accounts.models import Account, JournalEntryLine


def _line_sums(company, date_from=None, date_to=None):
    """Aggregate posted debits/credits per account.
    Handles both multi-line entries (JournalEntryLine) and two-account shortcut
    entries (JournalEntry.debit_account / credit_account / amount)."""
    from django.db.models import Count

    # -- multi-line entries --
    q = Q(journal_entry__company=company, journal_entry__status='Submitted')
    if date_from:
        q &= Q(journal_entry__posting_date__gte=date_from)
    if date_to:
        q &= Q(journal_entry__posting_date__lte=date_to)
    line_rows = list(JournalEntryLine.objects.filter(q)
        .values('account_id', 'account__account_number', 'account__account_name',
                'account__account_type')
        .annotate(debit=Sum('debit'), credit=Sum('credit')))

    # -- shortcut entries (no lines) --
    from apps.accounts.models import JournalEntry as JE
    qb = Q(company=company, status='Submitted',
           debit_account__isnull=False, credit_account__isnull=False)
    if date_from:
        qb &= Q(posting_date__gte=date_from)
    if date_to:
        qb &= Q(posting_date__lte=date_to)
    shortcut_jes = JE.objects.filter(qb).annotate(lc=Count('lines')).filter(lc=0)

    extra = {}
    for je in shortcut_jes:
        for is_debit, acc in [(True, je.debit_account), (False, je.credit_account)]:
            if acc is None:
                continue
            key = acc.pk
            extra.setdefault(key, {
                'account_id': key,
                'account__account_number': acc.account_number,
                'account__account_name': acc.account_name,
                'account__account_type': acc.account_type,
                'debit': Decimal('0'), 'credit': Decimal('0'),
            })
            if is_debit:
                extra[key]['debit'] += Decimal(str(je.amount or 0))
            else:
                extra[key]['credit'] += Decimal(str(je.amount or 0))

    # merge
    merged = {r['account_id']: {
        'account_id': r['account_id'],
        'account__account_number': r['account__account_number'],
        'account__account_name': r['account__account_name'],
        'account__account_type': r['account__account_type'],
        'debit': r['debit'] or Decimal('0'),
        'credit': r['credit'] or Decimal('0'),
    } for r in line_rows}
    for k, v in extra.items():
        if k in merged:
            merged[k]['debit'] += v['debit']
            merged[k]['credit'] += v['credit']
        else:
            merged[k] = v
    return sorted(merged.values(), key=lambda x: x['account__account_number'] or '')


def trial_balance(company, as_of=None) -> dict:
    rows = _line_sums(company, date_to=as_of)
    out, total_debit, total_credit = [], Decimal('0'), Decimal('0')
    for r in rows:
        debit, credit = r['debit'] or 0, r['credit'] or 0
        net = debit - credit
        row_debit = net if net > 0 else Decimal('0')
        row_credit = -net if net < 0 else Decimal('0')
        total_debit += row_debit
        total_credit += row_credit
        out.append({
            'code': r['account__account_number'], 'account': r['account__account_name'],
            'type': r['account__account_type'],
            'debit': row_debit, 'credit': row_credit,
        })
    return {
        'report': 'trial_balance', 'as_of': str(as_of) if as_of else 'all',
        'rows': out,
        'total_debit': total_debit, 'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
    }


def income_statement(company, date_from, date_to) -> dict:
    rows = _line_sums(company, date_from, date_to)
    income, expenses = [], []
    total_income = total_expense = Decimal('0')
    for r in rows:
        net = (r['credit'] or 0) - (r['debit'] or 0)   # credit-normal for income
        item = {'code': r['account__account_number'], 'account': r['account__account_name']}
        if r['account__account_type'] == 'Income':
            item['amount'] = net
            income.append(item)
            total_income += net
        elif r['account__account_type'] == 'Expense':
            item['amount'] = -net
            expenses.append(item)
            total_expense += -net
    return {
        'report': 'income_statement',
        'period': {'from': str(date_from), 'to': str(date_to)},
        'income': income, 'expenses': expenses,
        'total_income': total_income, 'total_expense': total_expense,
        'net_profit': total_income - total_expense,
    }


def balance_sheet(company, as_of=None) -> dict:
    rows = _line_sums(company, date_to=as_of)
    sections = {'Asset': [], 'Liability': [], 'Equity': []}
    totals = {'Asset': Decimal('0'), 'Liability': Decimal('0'),
              'Equity': Decimal('0')}
    pl_net = Decimal('0')
    for r in rows:
        debit, credit = r['debit'] or 0, r['credit'] or 0
        atype = r['account__account_type']
        if atype == 'Asset':
            amount = debit - credit
        elif atype in ('Liability', 'Equity'):
            amount = credit - debit
        elif atype in ('Income', 'Expense'):
            pl_net += (credit - debit)
            continue
        else:
            continue
        sections[atype].append({'code': r['account__account_number'],
                                'account': r['account__account_name'],
                                'amount': amount})
        totals[atype] += amount

    # current-period result flows into equity until formally closed
    if pl_net:
        sections['Equity'].append({'code': '', 'account':
                                   'Current period result (unclosed)',
                                   'amount': pl_net})
        totals['Equity'] += pl_net

    return {
        'report': 'balance_sheet', 'as_of': str(as_of) if as_of else 'all',
        'assets': sections['Asset'], 'liabilities': sections['Liability'],
        'equity': sections['Equity'],
        'total_assets': totals['Asset'],
        'total_liabilities_equity': totals['Liability'] + totals['Equity'],
        'is_balanced': totals['Asset'] == totals['Liability'] + totals['Equity'],
    }
