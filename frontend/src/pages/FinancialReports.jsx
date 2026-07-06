import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import {
  Scale, TrendingUp, Landmark, Download, RefreshCw, CircleDollarSign,
} from 'lucide-react';
import api from '../lib/api';

/**
 * FinancialReports — trial balance, income statement, balance sheet
 * and live KPIs from /api/v1/accounts/reports/*.
 */

const fmt = (v) =>
  Number(v ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 });

function KPICard({ label, value, icon: Icon, tone = 'text-gray-800' }) {
  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="mb-1 text-sm text-gray-500">{label}</p>
          <h3 className={`text-2xl font-bold ${tone}`}>{value}</h3>
        </div>
        <div className="rounded-lg bg-indigo-50 p-3 text-indigo-600">
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}

function StatementTable({ rows, columns }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-200 text-left text-xs uppercase text-gray-400">
          {columns.map((c) => (
            <th key={c.key} className={`py-2 ${c.num ? 'text-right' : ''}`}>{c.label}</th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {rows.map((r, i) => (
          <tr key={i}>
            {columns.map((c) => (
              <td key={c.key}
                className={`py-2 ${c.num ? 'text-right font-mono' : 'text-gray-700'}`}>
                {c.num ? fmt(r[c.key]) : r[c.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const TABS = [
  { id: 'trial-balance', label: 'Trial Balance', icon: Scale },
  { id: 'income-statement', label: 'Income Statement', icon: TrendingUp },
  { id: 'balance-sheet', label: 'Balance Sheet', icon: Landmark },
];

export default function FinancialReports() {
  const [tab, setTab] = useState('trial-balance');
  const [kpis, setKpis] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async (which = tab) => {
    setLoading(true);
    try {
      const [k, d] = await Promise.all([
        api.get('/accounts/reports/kpis/'),
        api.get(`/accounts/reports/${which}/`),
      ]);
      setKpis(k.data);
      setData(d.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(tab); /* eslint-disable-next-line */ }, [tab]);

  const download = () => {
    window.open(`/api/v1/accounts/reports/${tab}/?format=xlsx`, '_blank');
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Financial Reports</h1>
          <p className="text-sm text-gray-500">
            Computed live from posted journal entries.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => load()}
            className="flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm hover:bg-gray-50">
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <button onClick={download}
            className="flex items-center gap-1 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700">
            <Download size={15} /> Export Excel
          </button>
        </div>
      </div>

      {kpis && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <KPICard label="Net profit (YTD)" value={fmt(kpis.net_profit_ytd)}
            icon={CircleDollarSign}
            tone={Number(kpis.net_profit_ytd) >= 0 ? 'text-emerald-600' : 'text-red-600'} />
          <KPICard label="Income (YTD)" value={fmt(kpis.total_income_ytd)} icon={TrendingUp} />
          <KPICard label="Expenses (YTD)" value={fmt(kpis.total_expense_ytd)} icon={Scale} />
          <KPICard label="Total assets" value={fmt(kpis.total_assets)} icon={Landmark} />
        </div>
      )}

      <div className="flex gap-1 border-b border-gray-200">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium
              ${tab === t.id
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      <div className="rounded-xl border bg-white p-5 shadow-sm">
        {!data ? (
          <p className="py-12 text-center text-sm text-gray-400">
            {loading ? 'Loading…' : 'No data yet — post journal entries first.'}
          </p>
        ) : tab === 'trial-balance' ? (
          <>
            <StatementTable rows={data.rows || []} columns={[
              { key: 'code', label: 'Code' },
              { key: 'account', label: 'Account' },
              { key: 'debit', label: 'Debit', num: true },
              { key: 'credit', label: 'Credit', num: true },
            ]} />
            <div className="mt-4 flex justify-between border-t border-gray-200 pt-3 text-sm font-semibold">
              <span className={data.is_balanced ? 'text-emerald-600' : 'text-red-600'}>
                {data.is_balanced ? 'Books are balanced' : 'OUT OF BALANCE'}
              </span>
              <span className="font-mono">
                {fmt(data.total_debit)} / {fmt(data.total_credit)}
              </span>
            </div>
          </>
        ) : tab === 'income-statement' ? (
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            <div>
              <h4 className="mb-2 text-sm font-semibold text-gray-600">Income</h4>
              <StatementTable rows={data.income || []} columns={[
                { key: 'account', label: 'Account' },
                { key: 'amount', label: 'Amount', num: true },
              ]} />
            </div>
            <div>
              <h4 className="mb-2 text-sm font-semibold text-gray-600">Expenses</h4>
              <StatementTable rows={data.expenses || []} columns={[
                { key: 'account', label: 'Account' },
                { key: 'amount', label: 'Amount', num: true },
              ]} />
            </div>
            <div className="md:col-span-2 border-t border-gray-200 pt-3 text-right text-sm font-semibold">
              Net profit:{' '}
              <span className={`font-mono ${Number(data.net_profit) >= 0
                ? 'text-emerald-600' : 'text-red-600'}`}>
                {fmt(data.net_profit)}
              </span>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {[['Assets', data.assets], ['Liabilities', data.liabilities],
              ['Equity', data.equity]].map(([name, rows]) => (
              <div key={name}>
                <h4 className="mb-2 text-sm font-semibold text-gray-600">{name}</h4>
                <StatementTable rows={rows || []} columns={[
                  { key: 'account', label: 'Account' },
                  { key: 'amount', label: 'Amount', num: true },
                ]} />
              </div>
            ))}
            <div className="md:col-span-3 border-t border-gray-200 pt-3 text-right text-sm font-semibold">
              {fmt(data.total_assets)} ={' '}{fmt(data.total_liabilities_equity)}{' '}
              <span className={data.is_balanced ? 'text-emerald-600' : 'text-red-600'}>
                {data.is_balanced ? '✓' : '✗'}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
