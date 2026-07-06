import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { assets } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Plus, X, Box } from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

const STATUS_STYLES = {
  Draft: 'bg-yellow-100 text-yellow-700',
  Submitted: 'bg-blue-100 text-blue-700',
  'In Maintenance': 'bg-orange-100 text-orange-700',
  Disposed: 'bg-gray-100 text-gray-500',
}

function NewAssetModal({ onClose }) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [form, setForm] = useState({
    asset_name: '', asset_code: '', purchase_date: '', purchase_value: '',
    salvage_value: 0, depreciation_method: 'Straight Line', depreciation_rate: '',
  })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => assets.create({ ...data, company: user?.company }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['assets'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">أصل جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-600 mb-1">اسم الأصل</label>
            <input required value={form.asset_name} onChange={(e) => setForm({ ...form, asset_name: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">كود الأصل</label>
            <input required value={form.asset_code} onChange={(e) => setForm({ ...form, asset_code: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="AST-001" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">تاريخ الشراء</label>
            <input type="date" value={form.purchase_date} onChange={(e) => setForm({ ...form, purchase_date: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">قيمة الشراء</label>
              <input required type="number" step="0.01" value={form.purchase_value}
                onChange={(e) => setForm({ ...form, purchase_value: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">قيمة الإنقاذ</label>
              <input type="number" step="0.01" value={form.salvage_value}
                onChange={(e) => setForm({ ...form, salvage_value: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">طريقة الإهلاك</label>
              <select value={form.depreciation_method} onChange={(e) => setForm({ ...form, depreciation_method: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="Straight Line">القسط الثابت</option>
                <option value="Declining Balance">الرصيد المتناقص</option>
                <option value="None">بدون إهلاك</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">معدل الإهلاك السنوي %</label>
              <input type="number" step="0.01" value={form.depreciation_rate}
                onChange={(e) => setForm({ ...form, depreciation_rate: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <button type="submit" disabled={createMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
            {createMutation.isPending ? 'جارِ الإنشاء...' : 'إنشاء الأصل'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default function Assets() {
  const { data, isLoading } = useQuery({ queryKey: ['assets'], queryFn: () => assets.list() })
  const [showNew, setShowNew] = useState(false)

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">الأصول الثابتة</h2>
          <p className="text-gray-500 text-sm">الإهلاك المتراكم والقيمة الدفترية محسوبين تلقائيًا حسب طريقة الإهلاك</p>
        </div>
        <button onClick={() => setShowNew(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> أصل جديد
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الأصل</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">قيمة الشراء</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الإهلاك المتراكم</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">القيمة الدفترية</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الحالة</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data?.results?.map((asset) => (
              <tr key={asset.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-blue-600 flex items-center gap-2">
                  <Box size={16} className="text-gray-400" /> {asset.asset_name} <span className="text-xs text-gray-400">({asset.asset_code})</span>
                </td>
                <td className="px-6 py-4 text-gray-700">{asset.purchase_value}</td>
                <td className="px-6 py-4 text-orange-600">{Number(asset.accumulated_depreciation).toFixed(2)}</td>
                <td className="px-6 py-4 font-semibold text-gray-800">{Number(asset.book_value).toFixed(2)}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLES[asset.status] || 'bg-gray-100 text-gray-700'}`}>{asset.status}</span>
                </td>
              </tr>
            ))}
            {!data?.results?.length && (
              <tr><td colSpan={5} className="text-center text-gray-400 py-8">لا يوجد أصول بعد</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showNew && <NewAssetModal onClose={() => setShowNew(false)} />}
    </div>
  )
}
