import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import {
  LayoutDashboard, Workflow, Brain, Puzzle, TrendingUp,
  Settings, Menu, X, MessageSquare, Bot, Sparkles,
  BookOpen, Boxes, ShoppingCart, Receipt, Factory, Users2, Contact2,
  FolderKanban, Building2, PencilRuler, BarChart3,
} from 'lucide-react';
import AIAssistant from './components/AIAssistant';
import WorkflowBuilder from './pages/WorkflowBuilder';
import AgentDashboard from './pages/AgentDashboard';
import PluginMarketplace from './pages/PluginMarketplace';
import SelfImprovementDashboard from './pages/SelfImprovementDashboard';
import FinancialReports from './pages/FinancialReports';
import AICommandCenter from './pages/AICommandCenter';
import ScreenBuilder from './pages/ScreenBuilder';
import JournalEntries from './pages/JournalEntries';
import Budgets from './pages/Budgets';
import Items from './pages/Items';
import StockReconciliation from './pages/StockReconciliation';
import WarehousesBranches from './pages/WarehousesBranches';
import PurchaseOrders from './pages/PurchaseOrders';
import Suppliers from './pages/Suppliers';
import SalesOrders from './pages/SalesOrders';
import Customers from './pages/Customers';
import WorkOrders from './pages/WorkOrders';
import Employees from './pages/Employees';
import Payrolls from './pages/Payrolls';
import LeaveRequests from './pages/LeaveRequests';
import Teams from './pages/Teams';
import CRM from './pages/CRM';
import Projects from './pages/Projects';
import Tasks from './pages/Tasks';
import TimeTracking from './pages/TimeTracking';
import Assets from './pages/Assets';
import Companies from './pages/Companies';

import IndustrySelector from './pages/IndustrySelector';
import IndustryControls from './pages/IndustryControls';
import ComplianceDashboard from './pages/ComplianceDashboard';
import KPIDashboard from './pages/KPIDashboard';
function Sidebar({ isOpen, toggleSidebar }) {
  const menuItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { group: 'Finance' },
    { path: '/finance/reports', label: 'Financial Reports', icon: BarChart3 },
    { path: '/finance/journal-entries', label: 'Journal Entries', icon: BookOpen },
    { path: '/finance/budgets', label: 'Budgets', icon: Receipt },
    { group: 'Operations' },
    { path: '/inventory/items', label: 'Items', icon: Boxes },
    { path: '/inventory/reconciliation', label: 'Stock Reconciliation', icon: Boxes },
    { path: '/inventory/warehouses', label: 'Warehouses & Branches', icon: Building2 },
    { path: '/buying/orders', label: 'Purchase Orders', icon: ShoppingCart },
    { path: '/buying/suppliers', label: 'Suppliers', icon: Contact2 },
    { path: '/selling/orders', label: 'Sales Orders', icon: Receipt },
    { path: '/selling/customers', label: 'Customers', icon: Users2 },
    { path: '/manufacturing/work-orders', label: 'Work Orders', icon: Factory },
    { group: 'People' },
    { path: '/hr/employees', label: 'Employees', icon: Users2 },
    { path: '/hr/payrolls', label: 'Payrolls', icon: Receipt },
    { path: '/hr/leave-requests', label: 'Leave Requests', icon: Users2 },
    { path: '/hr/teams', label: 'Teams', icon: Users2 },
    { group: 'Growth' },
    { path: '/crm', label: 'CRM', icon: Contact2 },
    { path: '/projects', label: 'Projects', icon: FolderKanban },
    { path: '/projects/tasks', label: 'Tasks', icon: FolderKanban },
    { path: '/projects/time', label: 'Time Tracking', icon: FolderKanban },
    { path: '/assets', label: 'Assets', icon: Building2 },
    { group: 'Platform' },
    { path: '/workflows', label: 'Workflow Builder', icon: Workflow },
    { path: '/screens', label: 'Screen Builder', icon: PencilRuler },
    { path: '/agents', label: 'AI Agents', icon: Brain },
    { path: '/plugins', label: 'Plugin Marketplace', icon: Puzzle },
    { path: '/improvements', label: 'Self-Improvement', icon: TrendingUp },
    { path: '/ai-command', label: 'AI Command Center', icon: Sparkles },
    { path: '/companies', label: 'Companies', icon: Building2 },
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={toggleSidebar}
        />
      )}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 bg-white border-r border-gray-200 flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-gray-900">Nexus CE-ERP</span>
            </div>
            <button onClick={toggleSidebar} className="lg:hidden text-gray-500">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto p-4 space-y-1">
          {menuItems.map((item, idx) =>
            item.group ? (
              <p key={`g-${idx}`}
                className="px-3 pt-4 pb-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                {item.group}
              </p>
            ) : (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => window.innerWidth < 1024 && toggleSidebar()}
                className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 hover:text-indigo-600 transition-colors"
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            )
          )}
        </nav>
        <div className="p-4 border-t border-gray-200">
          <div className="bg-gradient-to-r from-indigo-50 to-violet-50 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-medium text-indigo-900">CE-ERP OS v2.0</span>
            </div>
            <p className="text-xs text-indigo-600/70">Cognitive ERP with AI</p>
          </div>
        </div>
      </aside>
    </>
  );
}

function Dashboard() {
  const stats = [
    { label: 'Active Workflows', value: '24', change: '+12%', icon: Workflow, color: 'indigo' },
    { label: 'AI Predictions', value: '1,247', change: '+23%', icon: Brain, color: 'violet' },
    { label: 'Plugins Active', value: '8', change: '+2', icon: Puzzle, color: 'amber' },
    { label: 'System Health', value: '99.9%', change: '+0.1%', icon: TrendingUp, color: 'emerald' },
  ];

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">Welcome to Nexus Cognitive ERP OS</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-2xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className={`w-10 h-10 bg-${stat.color}-100 rounded-xl flex items-center justify-center`}>
                <stat.icon className={`w-5 h-5 text-${stat.color}-600`} />
              </div>
              <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
                {stat.change}
              </span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
            <div className="text-sm text-gray-500">{stat.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Recent AI Activity</h3>
          <div className="space-y-3">
            {[
              { action: 'Invoice classified', detail: 'INV-2024-001 → Utilities', time: '2m ago' },
              { action: 'Workflow generated', detail: 'Purchase approval workflow', time: '15m ago' },
              { action: 'Anomaly detected', detail: 'Unusual expense pattern', time: '1h ago' },
              { action: 'Demand forecast', detail: 'Q3 inventory prediction', time: '3h ago' },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <div>
                  <p className="text-sm font-medium text-gray-900">{item.action}</p>
                  <p className="text-xs text-gray-500">{item.detail}</p>
                </div>
                <span className="text-xs text-gray-400">{item.time}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">System Improvements</h3>
          <div className="space-y-3">
            {[
              { title: 'Optimize invoice workflow', status: 'approved', impact: 'High' },
              { title: 'Add auto-reorder logic', status: 'pending', impact: 'Medium' },
              { title: 'Database index tuning', status: 'deployed', impact: 'High' },
              { title: 'Enhance AI classification', status: 'suggested', impact: 'Medium' },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <div>
                  <p className="text-sm font-medium text-gray-900">{item.title}</p>
                  <p className="text-xs text-gray-500">Impact: {item.impact}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full
                  ${item.status === 'deployed' ? 'bg-green-100 text-green-700' :
                    item.status === 'approved' ? 'bg-indigo-100 text-indigo-700' :
                    item.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                    'bg-gray-100 text-gray-600'}`}>
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function SettingsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">AI Configuration</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Default AI Provider</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="openai">OpenAI GPT-4.1</option>
              <option value="anthropic">Anthropic Claude 3.5</option>
              <option value="google">Google Gemini</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
            <input type="range" min="0" max="1" step="0.1" defaultValue="0.7" className="w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
            <input type="number" defaultValue="2000" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [aiAssistantOpen, setAiAssistantOpen] = useState(false);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50 flex">
        <Toaster position="top-right" />
        <Sidebar isOpen={sidebarOpen} toggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

        <div className="flex-1 flex flex-col min-w-0">
          {/* Top bar */}
          <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between lg:hidden">
            <button onClick={() => setSidebarOpen(true)} className="text-gray-500">
              <Menu className="w-6 h-6" />
            </button>
            <span className="font-semibold text-gray-900">Nexus CE-ERP</span>
            <div className="w-6" />
          </header>

          {/* AI Assistant Toggle */}
          <button
            onClick={() => setAiAssistantOpen(!aiAssistantOpen)}
            className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-full shadow-lg hover:shadow-xl flex items-center justify-center z-50 hover:scale-105 transition-all"
          >
            <MessageSquare className="w-6 h-6" />
          </button>

          {/* AI Assistant Panel */}
          <AIAssistant isOpen={aiAssistantOpen} onClose={() => setAiAssistantOpen(false)} />

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/finance/reports" element={<FinancialReports />} />
              <Route path="/ai-command" element={<AICommandCenter />} />
              <Route path="/finance/journal-entries" element={<JournalEntries />} />
              <Route path="/finance/budgets" element={<Budgets />} />
              <Route path="/inventory/items" element={<Items />} />
              <Route path="/inventory/reconciliation" element={<StockReconciliation />} />
              <Route path="/inventory/warehouses" element={<WarehousesBranches />} />
              <Route path="/buying/orders" element={<PurchaseOrders />} />
              <Route path="/buying/suppliers" element={<Suppliers />} />
              <Route path="/selling/orders" element={<SalesOrders />} />
              <Route path="/selling/customers" element={<Customers />} />
              <Route path="/manufacturing/work-orders" element={<WorkOrders />} />
              <Route path="/hr/employees" element={<Employees />} />
              <Route path="/hr/payrolls" element={<Payrolls />} />
              <Route path="/hr/leave-requests" element={<LeaveRequests />} />
              <Route path="/hr/teams" element={<Teams />} />
              <Route path="/crm" element={<CRM />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/projects/tasks" element={<Tasks />} />
              <Route path="/projects/time" element={<TimeTracking />} />
              <Route path="/assets" element={<Assets />} />
              <Route path="/companies" element={<Companies />} />
              <Route path="/screens" element={<ScreenBuilder />} />
              <Route path="/workflows" element={<WorkflowBuilder />} />
              <Route path="/agents" element={<AgentDashboard />} />
              <Route path="/plugins" element={<PluginMarketplace />} />
              <Route path="/improvements" element={<SelfImprovementDashboard />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/industries" element={<IndustrySelector />} />
              <Route path="/industries/:industryId/controls" element={<IndustryControls />} />
              <Route path="/compliance" element={<ComplianceDashboard />} />
              <Route path="/kpi" element={<KPIDashboard />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

