import React, { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, ShoppingCart, Package, Users, Building2,
  Factory, Briefcase, BarChart3, Settings, Menu, X,
  Warehouse, Landmark, Contact, FolderKanban, Box, FileText,
  UsersRound, CheckSquare, CalendarDays, Wallet, LogOut, ClipboardList, PiggyBank, Target,
  Timer, Brain, Columns3, GitGraph
} from 'lucide-react'

const menuItems = [
  { label: 'الرئيسية', icon: LayoutDashboard, path: '/' },
  { label: 'الشركات', icon: Building2, path: '/companies' },
  { label: 'أوامر الشراء', icon: ShoppingCart, path: '/purchase-orders' },
  { label: 'أوامر البيع', icon: FileText, path: '/sales-orders' },
  { label: 'الموردين', icon: Warehouse, path: '/suppliers' },
  { label: 'العملاء', icon: Contact, path: '/customers' },
  { label: 'إدارة العملاء (CRM)', icon: Target, path: '/crm' },
  { label: 'المخزون', icon: Package, path: '/items' },
  { label: 'جرد المخزون', icon: ClipboardList, path: '/stock-reconciliation' },
  { label: 'الفروع والمستودعات', icon: Warehouse, path: '/warehouses-branches' },
  { label: 'أوامر الإنتاج', icon: Factory, path: '/work-orders' },
  { label: 'الموظفين', icon: Users, path: '/employees' },
  { label: 'الفرق', icon: UsersRound, path: '/teams' },
  { label: 'المهام', icon: CheckSquare, path: '/tasks' },
  { label: 'الإجازات', icon: CalendarDays, path: '/leave-requests' },
  { label: 'الرواتب', icon: Wallet, path: '/payrolls' },
  { label: 'المشاريع', icon: FolderKanban, path: '/projects' },
  { label: 'تتبع الوقت', icon: Timer, path: '/time-tracking' },
  { label: 'المساعد الذكي', icon: Brain, path: '/ai-assistant' },
  { label: 'الأصول', icon: Box, path: '/assets' },
  { label: 'الحسابات', icon: Landmark, path: '/accounts' },
  { label: 'الميزانيات', icon: PiggyBank, path: '/budgets' },
  { label: 'التقارير', icon: BarChart3, path: '/reports' },
  { label: 'القطاعات', icon: B2, path: '/industries' },
  { label: 'الامتثال', icon: Shield, path: '/compliance' },
  { label: 'مؤشرات الأداء', icon: Activity, path: '/kpi' },
  { label: 'الإعدادات', icon: Settings, path: '/settings' },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const location = useLocation()
  const { user, logout } = useAuth()

  return (
    <div className="flex h-screen bg-gray-50" dir="rtl">
      {/* Sidebar */}
      <aside
        className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-white border-l transition-all duration-300 flex flex-col`}
      >
        <div className="p-4 flex items-center justify-between border-b">
          {sidebarOpen && (
            <h1 className="text-xl font-bold text-blue-600">Nexus ERP</h1>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto py-2">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/')
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon size={20} />
                {sidebarOpen && <span className="text-sm">{item.label}</span>}
              </Link>
            )
          })}
        </nav>
        <div className="p-4 border-t">
          <button
            onClick={logout}
            className="flex items-center gap-3 px-4 py-2 w-full text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut size={20} />
            {sidebarOpen && <span className="text-sm">تسجيل الخروج</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
