import React, { useState } from 'react';
import { CheckCircle, Circle, ChevronRight, Upload, Zap } from 'lucide-react';
import api from '../lib/api';

const STEPS = ['Register', 'Setup', 'Import Data', 'Go Live'];

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null);
  const [msg, setMsg] = useState('');

  // Step forms state
  const [reg, setReg] = useState({ company_name: '', admin_email: '', admin_password: '', vat_number: '', country: 'SA' });
  const [csvEntity, setCsvEntity] = useState('customers');
  const [csvText, setCsvText] = useState('');

  const call = async (fn) => { setBusy(true); setMsg(''); try { await fn(); } catch (e) { setMsg(e.response?.data?.error || e.message || 'Error'); } finally { setBusy(false); }};

  const handleRegister = () => call(async () => {
    await api.post('/tenants/onboarding/register/', reg);
    setStep(1);
  });

  const handleSetup = () => call(async () => {
    await api.post('/tenants/onboarding/setup/', { options: { seed_coa: true, create_warehouse: true, seed_currencies: true, seed_compliance: true }});
    setStep(2);
  });

  const handleImport = () => call(async () => {
    await api.post('/tenants/onboarding/import-data/', { entity: csvEntity, csv: csvText });
    setStep(3);
  });

  const handleCheckStatus = () => call(async () => {
    const { data } = await api.get('/tenants/onboarding/status/');
    setStatus(data);
  });

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      {/* Progress */}
      <div className="flex items-center gap-2">
        {STEPS.map((s, i) => (
          <React.Fragment key={s}>
            <div className={`flex items-center gap-1.5 text-sm font-medium
                ${i < step ? 'text-green-600' : i === step ? 'text-indigo-600' : 'text-gray-400'}`}>
              {i < step
                ? <CheckCircle size={16} />
                : <Circle size={16} />}
              {s}
            </div>
            {i < STEPS.length - 1 && <ChevronRight size={14} className="text-gray-300" />}
          </React.Fragment>
        ))}
      </div>

      {/* Step panels */}
      {step === 0 && (
        <div className="rounded-2xl border bg-white p-6 space-y-4 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800">Create your account</h2>
          {['company_name', 'admin_email', 'admin_password', 'vat_number'].map(k => (
            <input key={k} value={reg[k]} onChange={e => setReg(r => ({...r, [k]: e.target.value}))}
              placeholder={k.replace(/_/g,' ')} type={k.includes('password') ? 'password' : 'text'}
              className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          ))}
          <button onClick={handleRegister} disabled={busy}
            className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
            {busy ? 'Creating…' : 'Create account'}
          </button>
        </div>
      )}

      {step === 1 && (
        <div className="rounded-2xl border bg-white p-6 space-y-4 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800">Setup your workspace</h2>
          <p className="text-sm text-gray-500">We'll create your chart of accounts, default warehouse, supported Gulf currencies, and compliance framework starters automatically.</p>
          <button onClick={handleSetup} disabled={busy}
            className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
            {busy ? 'Setting up…' : 'Run setup'}
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="rounded-2xl border bg-white p-6 space-y-4 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800">Import existing data</h2>
          <select value={csvEntity} onChange={e => setCsvEntity(e.target.value)}
            className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
            {['customers','suppliers','items'].map(e => <option key={e}>{e}</option>)}
          </select>
          <textarea value={csvText} onChange={e => setCsvText(e.target.value)} rows={6}
            placeholder="Paste CSV here — e.g.&#10;name,vat,email&#10;Acme Corp,300111,acme@co.com"
            className="w-full rounded-lg border px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <div className="flex gap-3">
            <button onClick={handleImport} disabled={busy}
              className="flex-1 rounded-lg bg-indigo-600 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
              <Upload size={14} className="mr-1.5 inline" />{busy ? 'Importing…' : 'Import'}
            </button>
            <button onClick={() => setStep(3)} className="rounded-lg border px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50">
              Skip
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="rounded-2xl border bg-white p-6 space-y-4 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800">You're ready to go!</h2>
          <button onClick={handleCheckStatus} disabled={busy}
            className="rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700">
            <Zap size={14} className="mr-1.5 inline" />{busy ? 'Checking…' : 'Check readiness'}
          </button>
          {status && (
            <div className="space-y-2 mt-4">
              <div className={`text-sm font-semibold ${status.ready ? 'text-green-600' : 'text-amber-600'}`}>
                {status.ready ? '✓ Ready for production' : `${Math.round(status.readiness_score * 100)}% complete`}
              </div>
              {Object.entries(status.checks).map(([k, v]) => (
                <div key={k} className="flex items-center gap-2 text-sm">
                  {v ? <CheckCircle size={14} className="text-green-500" /> : <Circle size={14} className="text-gray-300" />}
                  <span className={v ? 'text-gray-700' : 'text-gray-400'}>{k.replace(/_/g,' ')}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {msg && <p className="text-sm text-red-600 bg-red-50 rounded-lg p-3">{msg}</p>}
    </div>
  );
}
