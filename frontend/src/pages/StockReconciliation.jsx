import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { stockReconciliations, stockReconciliationItems, warehouses, items as itemsApi } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Plus, X, ClipboardList, CheckCircle2 } from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

const STATUS_STYLES = {
  Draft: 'bg-yellow-100 text-yellow-700',
  Submitted: 'bg-green-100 text-green-700',
  Cancelled: 'bg-gray-100 text-gray-500',
}

function NewSRModal({ onClose }) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const { data: warehouseData } = useQuery({ queryKey: ['warehouses'], queryFn: () => warehouses.list() })
  const [form, setForm] = useState({ reconciliation_date: new Date().toISOString().slice(0, 10), warehouse: '', reason: 'Physical Count' })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => stockReconciliations.create({ ...data, company: user?.company }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['stockReconciliations'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">جرد مخزون جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-600 mb-1">المستودع</label>
            <select required value={form.warehouse} onChange={(e) => setForm({ ...form, warehouse: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">اختر مستودع</option>
              {warehouseData?.results?.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">تاريخ الجرد</label>
            <input type="date" required value={form.reconciliation_date}
              onChange={(e) => setForm({ ...form, reconciliation_date: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">السبب</label>
            <select value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="Physical Count">جرد فعلي دوري</option>
              <option value="Damage">تلف</option>
              <option value="Theft">فقدان/سرقة</option>
              <option value="System Error">خطأ بالنظام</option>
              <option value="Other">أخرى</option>
            </select>
          </div>
          <button type="submit" disabled={createMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
            {createMutation.isPending ? 'جارِ الإنشاء...' : 'إنشاء الجرد'}
          </button>
        </form>
      </div>
    </div>
  )
}

function SRPanel({ sr, onClose }) {
  const queryClient = useQueryClient()
  const { data: lines } = useQuery({
    queryKey: ['sr-items', sr.id],
    queryFn: () => stockReconciliationItems.list({ reconciliation: sr.id }),
  })
  const { data: itemsData } = useQuery({ queryKey: ['items'], queryFn: () => itemsApi.list() })
  const [lineForm, setLineForm] = useState({ item: '', system_quantity: '', actual_quantity: '', unit_cost: '' })
  const [error, setError] = useState('')

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['sr-items', sr.id] })
    queryClient.invalidateQueries({ queryKey: ['stockReconciliations'] })
    queryClient.invalidateQueries({ queryKey: ['items'] })
  }

  const addLine = useMutation({
    mutationFn: (data) => stockReconciliationItems.create({ ...data, reconciliation: sr.id }),
    onSuccess: () => { invalidate(); setLineForm({ item: '', system_quantity: '', actual_quantity: '', unit_cost: '' }); setError('') },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const submit = useMutation({
    mutationFn: () => stockReconciliations.update(sr.id, { status: 'Submitted' }),
    onSuccess: invalidate,
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const isDraft = sr.status === 'Draft'

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-bold text-gray-800">SR-{sr.id}</h3>
            <span className={`inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[sr.status]}`}>{sr.status}</span>
          </div>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>

        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}

        <table className="w-full text-sm mb-3">
          <thead>
            <tr className="text-gray-400 text-xs">
              <th className="text-right py-1">الصنف</th>
              <th className="text-right py-1">حسب النظام</th>
              <th className="text-right py-1">الفعلي بالجرد</th>
              <th className="text-right py-1">الفرق</th>
              <th className="text-right py-1">قيمة الفرق</th>
            </tr>
          </thead>
          <tbody>
            {lines?.results?.map((line) => (
              <tr key={line.id} className="border-t">
                <td className="py-2">{itemsData?.results?.find((i) => i.id === line.item)?.item_name || line.item}</td>
                <td className="py-2">{line.system_quantity}</td>
                <td className="py-2">{line.actual_quantity}</td>
                <td className={`py-2 font-medium ${line.difference < 0 ? 'text-red-600' : line.difference > 0 ? 'text-green-600' : ''}`}>{line.difference}</td>
                <td className="py-2">{line.total_difference_value}</td>
              </tr>
            ))}
            {!lines?.results?.length && (
              <tr><td colSpan={5} className="text-center text-gray-400 py-4">لا يوجد أصناف بعد</td></tr>
            )}
          </tbody>
        </table>

        {isDraft && (
          <form
            onSubmit={(e) => { e.preventDefault(); addLine.mutate(lineForm) }}
            className="flex flex-wrap gap-2 mb-4"
          >
            <select required value={lineForm.item} onChange={(e) => setLineForm({ ...lineForm, item: e.target.value })}
              className="flex-1 min-w-[140px] border rounded-lg px-2 py-1.5 text-sm">
              <option value="">اختر صنف</option>
              {itemsData?.results?.map((i) => <option key={i.id} value={i.id}>{i.item_name} (رصيد: {i.stock_quantity})</option>)}
            </select>
            <input required type="number" step="0.01" placeholder="حسب النظام" value={lineForm.system_quantity}
              onChange={(e) => setLineForm({ ...lineForm, system_quantity: e.target.value })}
              className="w-28 border rounded-lg px-2 py-1.5 text-sm" />
            <input required type="number" step="0.01" placeholder="الفعلي" value={lineForm.actual_quantity}
              onChange={(e) => setLineForm({ ...lineForm, actual_quantity: e.target.value })}
              className="w-24 border rounded-lg px-2 py-1.5 text-sm" />
            <input required type="number" step="0.01" placeholder="تكلفة الوحدة" value={lineForm.unit_cost}
              onChange={(e) => setLineForm({ ...lineForm, unit_cost: e.target.value })}
              className="w-24 border rounded-lg px-2 py-1.5 text-sm" />
            <button type="submit" className="bg-blue-600 text-white px-3 rounded-lg text-sm hover:bg-blue-700">إضافة</button>
          </form>
        )}

        {isDraft && (
          <div className="flex justify-end pt-3 border-t">
            <button onClick={() => submit.mutate()}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700">
              <CheckCircle2 size={16} /> اعتماد الجرد (يحدّث المخزون بالفروقات)
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function StockReconciliation() {
  const { data, isLoading } = useQuery({ queryKey: ['stockReconciliations'], queryFn: () => stockReconciliations.list() })
  const { data: warehouseData } = useQuery({ queryKey: ['warehouses'], queryFn: () => warehouses.list() })
  const [showNew, setShowNew] = useState(false)
  const [selected, setSelected] = useState(null)

  const warehouseName = (id) => warehouseData?.results?.find((w) => w.id === id)?.name || id

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">جرد المخزون</h2>
          <p className="text-gray-500 text-sm">اعتماد الجرد يحدّث رصيد المخزون تلقائيًا ليطابق العد الفعلي</p>
        </div>
        <button onClick={() => setShowNew(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> جرد جديد
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">المستودع</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">التاريخ</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">السبب</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">قيمة الفرق</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الحالة</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data?.results?.map((sr) => (
              <tr key={sr.id} onClick={() => setSelected(sr)} className="hover:bg-gray-50 cursor-pointer">
                <td className="px-6 py-4 font-medium text-blue-600 flex items-center gap-2">
                  <ClipboardList size={16} className="text-gray-400" /> {warehouseName(sr.warehouse)}
                </td>
                <td className="px-6 py-4 text-gray-600 text-sm">{sr.reconciliation_date}</td>
                <td className="px-6 py-4 text-gray-600 text-sm">{sr.reason}</td>
                <td className="px-6 py-4 font-medium">{sr.total_difference_value}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLES[sr.status] || 'bg-gray-100'}`}>{sr.status}</span>
                </td>
              </tr>
            ))}
            {!data?.results?.length && (
              <tr><td colSpan={5} className="text-center text-gray-400 py-8">لا يوجد سجلات جرد بعد</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showNew && <NewSRModal onClose={() => setShowNew(false)} />}
      {selected && <SRPanel sr={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
