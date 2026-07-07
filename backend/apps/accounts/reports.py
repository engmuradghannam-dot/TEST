"""Financial reporting engine.

Builds the three core statements from posted journal-entry lines
(not from cached balances), scoped by company and date range:
- trial_balance(company, as_of)
- income_statement(company, date_from, date_to)
- balance_sheet(company, as_of)
Each returns a plain dict ready for JSON, PDF, or Excel rendering.
"""
from decimal import Decimal

from django.db.models import Sum, Q

from apps.accounts.models import Account, JournalEntryLine


def _line_sums(company, date_from=None, date_to=None):
    """Aggregate posted debits/credits per account from JE lines."""
    q = Q(journal_entry__company=company, journal_entry__status='Submitted')
    if date_from:
        q &= Q(journal_entry__posting_date__gte=date_from)
    if date_to:
        q &= Q(journal_entry__posting_date__lte=date_to)
    rows = (JournalEntryLine.objects.filter(q)
            .values('account_id', 'account__account_number', 'account__account_name',
                    'account__account_type')
            .annotate(debit=Sum('debit'), credit=Sum('credit'))
            .order_by('account__account_number'))
    return list(rows)


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
