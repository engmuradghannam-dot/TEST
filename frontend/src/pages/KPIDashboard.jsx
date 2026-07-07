import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, TrendingDown, Minus, Activity, Target, Gauge, BarChart3 } from 'lucide-react';
import api from '../lib/api';

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function KPIDashboard() {
  const [kpis, setKpis] = useState([]);
  const [widgets, setWidgets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/kpi/company-kpis/').catch(() => ({ data: { results: [] } })),
      api.get('/kpi/dashboard-widgets/').catch(() => ({ data: { results: [] } }))
    ]).then(([kpiRes, widgetRes]) => {
      setKpis(kpiRes.data.results || kpiRes.data || []);
      setWidgets(widgetRes.data.results || widgetRes.data || []);
      setLoading(false);
    });
  }, []);

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-screen">
      <div className="text-xl animate-pulse">Loading KPIs...</div>
    </div>
  );

  const getTrendIcon = (trend) => {
    if (trend === 'up') return <TrendingUp size={16} className="text-green-500" />;
    if (trend === 'down') return <TrendingDown size={16} className="text-red-500" />;
    return <Minus size={16} className="text-gray-500" />;
  };

  const getStatusColor = (status) => {
    const map = {
      'on_track': 'bg-green-100 text-green-700 border-green-200',
      'exceeded': 'bg-emerald-100 text-emerald-700 border-emerald-200',
      'at_risk': 'bg-yellow-100 text-yellow-700 border-yellow-200',
      'off_track': 'bg-red-100 text-red-700 border-red-200'
    };
    return map[status] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const categoryData = Object.entries(kpis.reduce((a, k) => {
    a[k.kpi_category] = (a[k.kpi_category] || 0) + 1;
    return a;
  }, {})).map(([name, value]) => ({ name, value }));

  const statusData = Object.entries(kpis.reduce((a, k) => {
    a[k.status] = (a[k.status] || 0) + 1;
    return a;
  }, {})).map(([name, value]) => ({ name: name.replace('_', ' '), value }));

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">KPI Dashboard</h1>
      <p className="text-slate-500 mb-8">Real-time performance metrics and analytics</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {kpis.slice(0, 8).map(kpi => (
          <div key={kpi.id} className={`p-5 bg-white rounded-xl border shadow-sm hover:shadow-md transition-shadow ${getStatusColor(kpi.status)}`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium uppercase opacity-70">{kpi.kpi_category}</span>
              {getTrendIcon(kpi.trend)}
            </div>
            <div className="text-2xl font-bold mb-1">
              {parseFloat(kpi.current_value).toFixed(2)} <span className="text-sm font-normal">{kpi.kpi_unit}</span>
            </div>
            <div className="text-sm opacity-70 mb-2">{kpi.kpi_name}</div>
            <div className="flex items-center gap-2 text-xs">
              <Target size={12} />
              <span>Target: {parseFloat(kpi.target_value || 0).toFixed(2)}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity size={18} /> Performance Trends
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={kpis.slice(0, 10).map(k => ({ name: k.kpi_name.substring(0, 15), value: parseFloat(k.current_value), target: parseFloat(k.target_value || 0) }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{fontSize: 11}} angle={-15} textAnchor="end" height={60} />
              <YAxis tick={{fontSize: 11}} />
              <Tooltip contentStyle={{borderRadius: 8, border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={{r: 4}} />
              <Line type="monotone" dataKey="target" stroke="#10b981" strokeDasharray="5 5" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 size={18} /> KPI by Category
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={categoryData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={5} dataKey="value">
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 space-y-1">
            {categoryData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-2 text-sm">
                <div className="w-3 h-3 rounded-full" style={{backgroundColor: COLORS[index % COLORS.length]}} />
                <span className="flex-1">{entry.name}</span>
                <span className="font-medium">{entry.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">All KPIs</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">KPI</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Category</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Current</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Target</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Trend</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Status</th>
              </tr>
            </thead>
            <tbody>
              {kpis.map(kpi => (
                <tr key={kpi.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4 font-medium">{kpi.kpi_name}</td>
                  <td className="py-3 px-4 text-sm text-slate-500">{kpi.kpi_category}</td>
                  <td className="py-3 px-4 font-medium">{parseFloat(kpi.current_value).toFixed(2)} {kpi.kpi_unit}</td>
                  <td className="py-3 px-4 text-sm text-slate-500">{parseFloat(kpi.target_value || 0).toFixed(2)}</td>
                  <td className="py-3 px-4">{getTrendIcon(kpi.trend)}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(kpi.status)}`}>
                      {kpi.status.replace('_', ' ')}
                    </span>
                  </td>
                </tr>
              ))}
              {kpis.length === 0 && (
                <tr><td colSpan={6} className="text-center py-8 text-slate-400">No KPIs configured</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
