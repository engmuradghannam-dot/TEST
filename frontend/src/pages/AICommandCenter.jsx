import React, { useState } from 'react';
import toast from 'react-hot-toast';
import {
  Sparkles, ShieldCheck, Activity, Send, TrendingUp, Lock,
} from 'lucide-react';
import api from '../lib/api';

/**
 * AICommandCenter — Natural-Language ERP + AI/security control surface.
 * Type a request in Arabic or English ("اعمل تقرير الربحية للربع الثاني")
 * and the backend resolves it to a report/action via /ai/nl/.
 */
export default function AICommandCenter() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [audit, setAudit] = useState(null);

  const ask = async () => {
    if (!text.trim()) return;
    setBusy(true);
    try {
      const { data } = await api.post('/ai/nl/', { text });
      setResult(data);
      if (data.status === 'clarify') toast(data.message);
    } catch (e) {
      toast.error(e.response?.data?.message || 'Request failed');
    } finally {
      setBusy(false);
    }
  };

  const verifyAudit = async () => {
    try {
      const { data } = await api.get('/iam/audit/verify/');
      setAudit(data);
      toast[data.intact ? 'success' : 'error'](
        data.intact ? `Audit chain intact (${data.verified} entries)`
                    : `Chain broken: ${data.broken.length} issue(s)`);
    } catch {
      toast.error('Verification unavailable');
    }
  };

  const examples = [
    'اعمل تقرير الربحية للربع الثاني',
    'Show balance sheet for this year',
    'List suppliers',
    'Forecast sales',
  ];

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-indigo-600 p-2.5 text-white">
          <Sparkles size={22} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-800">AI Command Center</h1>
          <p className="text-sm text-gray-500">
            Ask in Arabic or English — the ERP resolves it for you.
          </p>
        </div>
      </div>

      <div className="rounded-2xl border bg-white p-4 shadow-sm">
        <div className="flex gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && ask()}
            placeholder="اكتب طلبك هنا…  /  Type your request…"
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm
                       focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={ask}
            disabled={busy}
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4
                       py-2.5 text-sm font-medium text-white hover:bg-indigo-700
                       disabled:opacity-50">
            <Send size={15} /> {busy ? '…' : 'Ask'}
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {examples.map((ex) => (
            <button
              key={ex}
              onClick={() => setText(ex)}
              className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1
                         text-xs text-gray-600 hover:bg-gray-100">
              {ex}
            </button>
          ))}
        </div>
      </div>

      {result && (
        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold
                          text-gray-700">
            <Activity size={16} className="text-indigo-600" />
            {result.type || result.status}
          </div>
          <pre className="max-h-96 overflow-auto rounded-lg bg-gray-50 p-4
                          text-xs text-gray-700">
            {JSON.stringify(result.data ?? result, null, 2)}
          </pre>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <div className="mb-3 flex items-center gap-2 font-semibold text-gray-700">
            <ShieldCheck size={18} className="text-emerald-600" />
            Immutable Audit
          </div>
          <p className="mb-3 text-sm text-gray-500">
            Verify the hash-chained, signed audit ledger.
          </p>
          <button
            onClick={verifyAudit}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium
                       text-white hover:bg-emerald-700">
            <Lock size={14} className="mr-1 inline" /> Verify chain
          </button>
          {audit && (
            <p className={`mt-3 text-sm ${audit.intact ? 'text-emerald-600'
                                                        : 'text-red-600'}`}>
              {audit.intact
                ? `✓ Intact — ${audit.verified} entries`
                : `✗ ${audit.broken.length} broken link(s)`}
            </p>
          )}
        </div>

        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <div className="mb-3 flex items-center gap-2 font-semibold text-gray-700">
            <TrendingUp size={18} className="text-indigo-600" />
            Predictive
          </div>
          <p className="mb-3 text-sm text-gray-500">
            Sales / demand / risk forecasting from your live data.
          </p>
          <button
            onClick={() => { setText('Forecast sales'); ask(); }}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium
                       text-white hover:bg-indigo-700">
            Run sales forecast
          </button>
        </div>
      </div>
    </div>
  );
}
