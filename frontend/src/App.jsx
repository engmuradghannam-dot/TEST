import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import PurchaseOrders from './pages/PurchaseOrders'
import SalesOrders from './pages/SalesOrders'
import Employees from './pages/Employees'
import Companies from './pages/Companies'
import Suppliers from './pages/Suppliers'
import Customers from './pages/Customers'
import WorkOrders from './pages/WorkOrders'
import Items from './pages/Items'
import Teams from './pages/Teams'
import Tasks from './pages/Tasks'
import LeaveRequests from './pages/LeaveRequests'
import Payrolls from './pages/Payrolls'
import Assets from './pages/Assets'
import JournalEntries from './pages/JournalEntries'
import StockReconciliation from './pages/StockReconciliation'
import Budgets from './pages/Budgets'
import WarehousesBranches from './pages/WarehousesBranches'
import Projects from './pages/Projects'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="purchase-orders" element={<PurchaseOrders />} />
        <Route path="sales-orders" element={<SalesOrders />} />
        <Route path="employees" element={<Employees />} />
        <Route path="companies" element={<Companies />} />
        <Route path="suppliers" element={<Suppliers />} />
        <Route path="customers" element={<Customers />} />
        <Route path="work-orders" element={<WorkOrders />} />
        <Route path="items" element={<Items />} />
        <Route path="teams" element={<Teams />} />
        <Route path="tasks" element={<Tasks />} />
        <Route path="leave-requests" element={<LeaveRequests />} />
        <Route path="payrolls" element={<Payrolls />} />
        <Route path="assets" element={<Assets />} />
        <Route path="accounts" element={<JournalEntries />} />
        <Route path="stock-reconciliation" element={<StockReconciliation />} />
        <Route path="budgets" element={<Budgets />} />
        <Route path="warehouses" element={<WarehousesBranches />} />
        <Route path="projects" element={<Projects />} />
        <Route path="*" element={<div className="p-10 text-center text-gray-500">الصفحة غير موجودة</div>} />
      </Route>
    </Routes>
  )
}

export default App
