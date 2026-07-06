import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { warehouses, branches } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Plus, X, Warehouse as WarehouseIcon, Building } from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

function NewBranchModal({ onClose }) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => branches.create({ ...data, company: user?.company }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['branches'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">فرع جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate({ name }) }} className="space-y-3">
          <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="اسم الفرع"
            className="w-full border rounded-lg px-3 py-2 text-sm" />
          <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700">إنشاء</button>
        </form>
      </div>
    </div>
  )
}

function NewWarehouseModal({ onClose }) {
  const queryClient = useQueryClient()
  const { data: branchData } = useQuery({ queryKey: ['branches'], queryFn: () => branches.list() })
  const [form, setForm] = useState({ name: '', code: '', branch: '', warehouse_type: 'Main' })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => warehouses.create(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['warehouses'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">مستودع جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="اسم المستودع"
            className="w-full border rounded-lg px-3 py-2 text-sm" />
          <input required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="كود المستودع (فريد)"
            className="w-full border rounded-lg px-3 py-2 text-sm" />
          <select required value={form.branch} onChange={(e) => setForm({ ...form, branch: e.target.value })}
            className="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="">اختر فرع</option>
            {branchData?.results?.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
          <select value={form.warehouse_type} onChange={(e) => setForm({ ...form, warehouse_type: e.target.value })}
            className="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="Main">رئيسي</option>
            <option value="Transit">ترانزيت</option>
            <option value="Returns">مرتجعات</option>
            <option value="Damaged">تالف</option>
          </select>
          <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700">إنشاء</button>
        </form>
      </div>
    </div>
  )
}

export default function WarehousesBranches() {
  const { data: branchData, isLoading: bLoading } = useQuery({ queryKey: ['branches'], queryFn: () => branches.list() })
  const { data: warehouseData, isLoading: wLoading } = useQuery({ queryKey: ['warehouses'], queryFn: () => warehouses.list() })
  const [showNewBranch, setShowNewBranch] = useState(false)
  const [showNewWarehouse, setShowNewWarehouse] = useState(false)

  if (bLoading || wLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">الفروع والمستودعات</h2>
        <p className="text-gray-500 text-sm">المستودعات مرتبطة بالفروع، والرصيد الحالي محسوب حي من حركات المخزون</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-bold text-gray-700 flex items-center gap-2"><Building size={18} /> الفروع</h3>
            <button onClick={() => setShowNewBranch(true)} className="text-sm bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg flex items-center gap-1 hover:bg-blue-100">
              <Plus size={14} /> فرع جديد
            </button>
          </div>
          <div className="bg-white rounded-xl shadow-sm divide-y">
            {branchData?.results?.map((b) => (
              <div key={b.id} className="p-3 text-sm">{b.name}</div>
            ))}
            {!branchData?.results?.length && <p className="p-4 text-gray-400 text-sm text-center">لا يوجد فروع بعد</p>}
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-bold text-gray-700 flex items-center gap-2"><WarehouseIcon size={18} /> المستودعات</h3>
            <button onClick={() => setShowNewWarehouse(true)} className="text-sm bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg flex items-center gap-1 hover:bg-blue-100">
              <Plus size={14} /> مستودع جديد
            </button>
          </div>
          <div className="bg-white rounded-xl shadow-sm divide-y">
            {warehouseData?.results?.map((w) => (
              <div key={w.id} className="p-3 flex justify-between items-center text-sm">
                <span>{w.name} <span className="text-xs text-gray-400">({w.code})</span></span>
                <span className="font-semibold">{w.current_stock}</span>
              </div>
            ))}
            {!warehouseData?.results?.length && <p className="p-4 text-gray-400 text-sm text-center">لا يوجد مستودعات بعد</p>}
          </div>
        </div>
      </div>

      {showNewBranch && <NewBranchModal onClose={() => setShowNewBranch(false)} />}
      {showNewWarehouse && <NewWarehouseModal onClose={() => setShowNewWarehouse(false)} />}
    </div>
  )
}
