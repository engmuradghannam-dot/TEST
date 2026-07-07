import React, { useState, useEffect } from 'react';
import { Shield, AlertCircle, CheckCircle, Clock, FileText, TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react';
import { api } from '../lib/api';

export default function ComplianceDashboard() {
  const [frameworks, setFrameworks] = useState([]);
  const [records, setRecords] = useState([]);
  const [updates, setUpdates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/compliance/frameworks/').catch(() => ({ data: { results: [] } })),
      api.get('/compliance/company-records/').catch(() => ({ data: { results: [] } })),
      api.get('/compliance/regulatory-updates/').catch(() => ({ data: { results: [] } }))
    ]).then(([fw, rec, upd]) => {
      setFrameworks(fw.data.results || fw.data || []);
      setRecords(rec.data.results || rec.data || []);
      setUpdates(upd.data.results || upd.data || []);
      setLoading(false);
    });
  }, []);

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-screen">
      <div className="text-xl animate-pulse">Loading compliance data...</div>
    </div>
  );

  const overallScore = records.length > 0
    ? (records.reduce((a, r) => a + parseFloat(r.compliance_score || 0), 0) / records.length).toFixed(1)
    : 0;

  const statusColors = {
    compliant: 'bg-green-100 text-green-700',
    non_compliant: 'bg-red-100 text-red-700',
    in_progress: 'bg-blue-100 text-blue-700',
    not_started: 'bg-gray-100 text-gray-700',
    under_review: 'bg-yellow-100 text-yellow-700'
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Compliance Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="p-6 bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="text-sm text-slate-500 mb-1">Overall Score</div>
          <div className="text-3xl font-bold text-blue-600">{overallScore}%</div>
          <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-blue-600 rounded-full" style={{width: `${overallScore}%`}} />
          </div>
        </div>
        <div className="p-6 bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="text-sm text-slate-500 mb-1">Active Frameworks</div>
          <div className="text-3xl font-bold text-green-600">{records.length}</div>
        </div>
        <div className="p-6 bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="text-sm text-slate-500 mb-1">Compliant</div>
          <div className="text-3xl font-bold text-emerald-600">
            {records.filter(r => r.status === 'compliant').length}
          </div>
        </div>
        <div className="p-6 bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="text-sm text-slate-500 mb-1">At Risk</div>
          <div className="text-3xl font-bold text-red-600">
            {records.filter(r => r.status === 'non_compliant').length}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Shield size={20} /> Compliance Frameworks
          </h2>
          <div className="space-y-3">
            {frameworks.map(fw => (
              <div key={fw.framework_id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
                <div>
                  <div className="font-medium">{fw.name}</div>
                  <div className="text-sm text-slate-500">{fw.category} • {fw.requirement_count} requirements</div>
                </div>
                <button className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  Activate
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <AlertCircle size={20} /> Regulatory Updates
          </h2>
          <div className="space-y-3">
            {updates.slice(0, 5).map(u => (
              <div key={u.id} className={`p-4 rounded-lg border ${u.is_read ? 'bg-slate-50 border-slate-200' : 'bg-blue-50 border-blue-200'}`}>
                <div className="flex items-center gap-2 mb-1">
                  <AlertCircle size={14} className={u.impact_level === 'critical' ? 'text-red-500' : 'text-blue-500'} />
                  <span className="font-medium text-sm">{u.title}</span>
                </div>
                <div className="text-xs text-slate-500">{u.framework_name} • Effective {u.effective_date}</div>
              </div>
            ))}
            {updates.length === 0 && (
              <div className="text-center text-slate-400 py-8">No regulatory updates</div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <BarChart3 size={20} /> Company Compliance Records
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Framework</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Status</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Score</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Last Assessment</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {records.map(r => (
                <tr key={r.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4 font-medium">{r.framework_name}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${statusColors[r.status] || 'bg-gray-100'}`}>
                      {r.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-600 rounded-full" style={{width: `${r.compliance_score}%`}} />
                      </div>
                      <span className="text-sm">{r.compliance_score}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-sm text-slate-500">{r.last_assessment_date || 'Never'}</td>
                  <td className="py-3 px-4">
                    <button className="text-sm text-blue-600 hover:text-blue-800">Run Assessment</button>
                  </td>
                </tr>
              ))}
              {records.length === 0 && (
                <tr><td colSpan={5} className="text-center py-8 text-slate-400">No compliance records found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
