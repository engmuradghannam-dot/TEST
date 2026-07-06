import React, { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, ShoppingCart, Package, Users, Building2,
  Factory, Briefcase, BarChart3, Settings, Menu, X,
  Warehouse, Landmark, Contact, FolderKanban, Box, FileText,
  UsersRound, CheckSquare, CalendarDays, Wallet, LogOut, ClipboardList, PiggyBank
} from 'lucide-react'

const menuItems = [
  { label: 'الرئيسية', icon: LayoutDashboard, path: '/' },
  { label: 'الشركات', icon: Building2, path: '/companies' },
  { label: 'أوامر الشراء', icon: ShoppingCart, path: '/purchase-orders' },
  { label: 'أوامر البيع', icon: FileText, path: '/sales-orders' },
  { label: 'الموردين', icon: Warehouse, path: '/suppliers' },
  { label: 'العملاء', icon: Contact, path: '/customers' },
  { label: 'المخزون', icon: Package, path: '/items' },
  { label: 'جرد المخزون', icon: ClipboardList, path: '/stock-reconciliation' },
  { label: 'الفروع والمستودعات', icon: Warehouse, path: '/warehouses' },
  { label: 'أوامر الإنتاج', icon: Factory, path: '/work-orders' },
  { label: 'الموظفين', icon: Users, path: '/employees' },
  { label: 'الفرق', icon: UsersRound, path: '/teams' },
  { label: 'المهام', icon: CheckSquare, path: '/tasks' },
  { label: 'الإجازات', icon: CalendarDays, path: '/leave-requests' },
  { label: 'الرواتب', icon: Wallet, path: '/payrolls' },
  { label: 'المشاريع', icon: FolderKanban, path: '/projects' },
  { label: 'الأصول', icon: Box, path: '/assets' },
  { label: 'الحسابات', icon: Landmark, path: '/accounts' },
  { label: 'الميزانيات', icon: PiggyBank, path: '/budgets' },
  { label: 'التقارير', icon: BarChart3, path: '/reports' },
  { label: 'الإعدادات', icon: Settings, path: '/settings' },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const location = useLocation()
  const { user, logout } = useAuth()

  return (
    <div className="flex h-screen bg-gray-100" dir="rtl">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-white border-l transition-all duration-300 flex flex-col`}>
        <div className="h-16 flex items-center justify-between px-4 border-b">
          {sidebarOpen && <h1 className="text-xl font-bold text-blue-600">Nexus ERP</h1>}
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1 hover:bg-gray-100 rounded">
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto py-4">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 mx-2 rounded-lg transition-colors ${
                  isActive ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon size={20} />
                {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            )
          })}
        </nav>
        <div className="border-t p-3">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-red-600 hover:bg-red-50"
          >
            <LogOut size={20} />
            {sidebarOpen && <span className="text-sm font-medium">تسجيل الخروج{user?.email ? ` (${user.email})` : ''}</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
