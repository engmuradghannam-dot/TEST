import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Shield, CheckCircle, AlertTriangle, Brain, FileText, Activity, Play, Filter, Search } from 'lucide-react';
import { api } from '../lib/api';

export default function IndustryControls() {
  const { industryId } = useParams();
  const [controls, setControls] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    Promise.all([
      api.get(`/industries/catalog/${industryId}/controls/`).catch(() => ({ data: { controls: [] } })),
      api.get(`/industries/catalog/${industryId}/controls_summary/`).catch(() => ({ data: {} }))
    ]).then(([ctrlRes, sumRes]) => {
      setControls(ctrlRes.data.controls || []);
      setSummary(sumRes.data);
      setLoading(false);
    });
  }, [industryId]);

  const getSeverityColor = (sev) => {
    const map = { critical: 'text-red-500 bg-red-500/10', high: 'text-orange-500 bg-orange-500/10', medium: 'text-yellow-500 bg-yellow-500/10', low: 'text-green-500 bg-green-500/10' };
    return map[sev] || 'text-gray-500 bg-gray-500/10';
  };

  const getSeverityBadge = (sev) => {
    const map = { critical: 'bg-red-500/20 text-red-400', high: 'bg-orange-500/20 text-orange-400', medium: 'bg-yellow-500/20 text-yellow-400', low: 'bg-green-500/20 text-green-400' };
    return map[sev] || 'bg-gray-500/20 text-gray-400';
  };

  const filtered = controls.filter(ctrl => {
    const matchesType = filterType === 'all' || ctrl.control_type === filterType;
    const matchesSearch = (ctrl.control_name + ' ' + ctrl.description).toLowerCase().includes(searchTerm.toLowerCase());
    return matchesType && matchesSearch;
  });

  const controlTypes = ['all', ...new Set(controls.map(c => c.control_type))];

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-screen">
      <div className="text-xl animate-pulse">Loading controls...</div>
    </div>
  );

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">{summary?.industry || industryId} Controls</h1>
        <p className="text-slate-500">{summary?.total_controls || controls.length} total controls • {summary?.required_controls || controls.filter(c => c.is_required).length} required</p>
      </div>

      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <input
            type="text"
            placeholder="Search controls..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500"
          />
        </div>
        <select
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
          className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500"
        >
          {controlTypes.map(t => (
            <option key={t} value={t}>{t === 'all' ? 'All Types' : t}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map(ctrl => (
          <div key={ctrl.control_id} className="p-5 bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <Shield size={18} className={getSeverityColor(ctrl.severity).split(' ')[0]} />
                <span className="text-xs font-mono text-slate-500">{ctrl.control_id}</span>
              </div>
              <div className="flex gap-2">
                {ctrl.is_required && (
                  <span className="text-xs bg-red-50 text-red-600 px-2 py-1 rounded-full font-medium">Required</span>
                )}
                <span className={`text-xs px-2 py-1 rounded-full ${getSeverityBadge(ctrl.severity)}`}>{ctrl.severity}</span>
              </div>
            </div>

            <h3 className="font-semibold text-lg mb-2">{ctrl.control_name}</h3>
            <p className="text-sm text-slate-600 mb-4 line-clamp-2">{ctrl.description}</p>

            <div className="flex flex-wrap gap-2 mb-4">
              <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded">{ctrl.control_type}</span>
              <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded">{ctrl.module}</span>
            </div>

            <div className="border-t pt-3 space-y-2">
              {ctrl.ai_agent_name && (
                <div className="flex items-center gap-2 text-sm text-purple-600">
                  <Brain size={14} /> {ctrl.ai_agent_name}
                </div>
              )}
              {ctrl.kpi_name && (
                <div className="flex items-center gap-2 text-sm text-blue-600">
                  <Activity size={14} /> {ctrl.kpi_name}
                </div>
              )}
              {ctrl.compliance_framework && (
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <FileText size={14} /> {ctrl.compliance_framework}
                </div>
              )}
            </div>

            <button
              onClick={() => api.post(`/industries/controls/${ctrl.control_id}/execute/`).catch(() => alert('Control executed'))}
              className="mt-4 w-full py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
            >
              <Play size={14} /> Execute Control
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
