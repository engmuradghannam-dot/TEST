import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workOrders, boms, bomItems, items as itemsApi, warehouses } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Plus, X, Factory, CheckCircle2, PlayCircle, Layers } from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

const STATUS_STYLES = {
  Draft: 'bg-yellow-100 text-yellow-700',
  'In Progress': 'bg-blue-100 text-blue-700',
  Completed: 'bg-green-100 text-green-700',
  Cancelled: 'bg-gray-100 text-gray-500',
}

function NewBOMModal({ onClose }) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const { data: itemsData } = useQuery({ queryKey: ['items'], queryFn: () => itemsApi.list() })
  const [form, setForm] = useState({ item: '', bom_name: '', operating_cost: 0, labor_cost: 0 })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => boms.create({ ...data, company: user?.company }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['boms'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">قائمة مواد جديدة (BOM)</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-600 mb-1">اسم القائمة</label>
            <input required value={form.bom_name} onChange={(e) => setForm({ ...form, bom_name: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">المنتج النهائي</label>
            <select required value={form.item} onChange={(e) => setForm({ ...form, item: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">اختر منتج</option>
              {itemsData?.results?.map((i) => <option key={i.id} value={i.id}>{i.item_name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">تكلفة تشغيل</label>
              <input type="number" step="0.01" value={form.operating_cost}
                onChange={(e) => setForm({ ...form, operating_cost: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">تكلفة عمالة</label>
              <input type="number" step="0.01" value={form.labor_cost}
                onChange={(e) => setForm({ ...form, labor_cost: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <button type="submit" disabled={createMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
            {createMutation.isPending ? 'جارِ الإنشاء...' : 'إنشاء القائمة'}
          </button>
          <p className="text-xs text-gray-400 text-center">تقدر تضيف المواد الخام بعد إنشاء القائمة من صفحة التفاصيل.</p>
        </form>
      </div>
    </div>
  )
}

function NewWOModal({ onClose }) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const { data: bomData } = useQuery({ queryKey: ['boms'], queryFn: () => boms.list() })
  const { data: warehouseData } = useQuery({ queryKey: ['warehouses'], queryFn: () => warehouses.list() })
  const [form, setForm] = useState({ wo_number: '', bom: '', item_to_manufacture: '', qty_to_produce: '', warehouse: '' })
  const [error, setError] = useState('')

  const selectedBom = bomData?.results?.find((b) => String(b.id) === String(form.bom))

  const createMutation = useMutation({
    mutationFn: (data) => workOrders.create({ ...data, company: user?.company, item_to_manufacture: selectedBom?.item }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['workOrders'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">أمر إنتاج جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-600 mb-1">رقم الأمر</label>
            <input required value={form.wo_number} onChange={(e) => setForm({ ...form, wo_number: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="WO-2026-001" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">قائمة المواد (BOM)</label>
            <select required value={form.bom} onChange={(e) => setForm({ ...form, bom: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">اختر BOM</option>
              {bomData?.results?.map((b) => <option key={b.id} value={b.id}>{b.bom_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">المستودع</label>
            <select required value={form.warehouse} onChange={(e) => setForm({ ...form, warehouse: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">اختر مستودع</option>
              {warehouseData?.results?.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">الكمية المطلوب إنتاجها</label>
            <input required type="number" step="0.01" value={form.qty_to_produce}
              onChange={(e) => setForm({ ...form, qty_to_produce: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <button type="submit" disabled={createMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
            {createMutation.isPending ? 'جارِ الإنشاء...' : 'إنشاء أمر الإنتاج'}
          </button>
        </form>
      </div>
    </div>
  )
}

function BOMPanel({ bom, onClose }) {
  const queryClient = useQueryClient()
  const { data: lines } = useQuery({ queryKey: ['bom-items', bom.id], queryFn: () => bomItems.list({ bom: bom.id }) })
  const { data: itemsData } = useQuery({ queryKey: ['items'], queryFn: () => itemsApi.list() })
  const [lineForm, setLineForm] = useState({ item: '', qty: '', rate: '' })
  const [error, setError] = useState('')

  const addLine = useMutation({
    mutationFn: (data) => bomItems.create({ ...data, bom: bom.id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bom-items', bom.id] })
      queryClient.invalidateQueries({ queryKey: ['boms'] })
      setLineForm({ item: '', qty: '', rate: '' })
      setError('')
    },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">{bom.bom_name}</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}

        <p className="text-sm text-gray-500 mb-3">التكلفة الإجمالية: <span className="font-semibold text-gray-800">{bom.total_cost}</span></p>

        <table className="w-full text-sm mb-3">
          <thead><tr className="text-gray-400 text-xs"><th className="text-right py-1">المادة الخام</th><th className="text-right py-1">الكمية</th><th className="text-right py-1">السعر</th></tr></thead>
          <tbody>
            {lines?.results?.map((l) => (
              <tr key={l.id} className="border-t">
                <td className="py-2">{itemsData?.results?.find((i) => i.id === l.item)?.item_name || l.item}</td>
                <td className="py-2">{l.qty}</td>
                <td className="py-2">{l.rate}</td>
              </tr>
            ))}
            {!lines?.results?.length && <tr><td colSpan={3} className="text-center text-gray-400 py-4">لا يوجد مواد خام بعد</td></tr>}
          </tbody>
        </table>

        <form onSubmit={(e) => { e.preventDefault(); addLine.mutate(lineForm) }} className="flex gap-2">
          <select required value={lineForm.item} onChange={(e) => setLineForm({ ...lineForm, item: e.target.value })}
            className="flex-1 border rounded-lg px-2 py-1.5 text-sm">
            <option value="">اختر مادة خام</option>
            {itemsData?.results?.map((i) => <option key={i.id} value={i.id}>{i.item_name}</option>)}
          </select>
          <input required type="number" step="0.01" placeholder="الكمية" value={lineForm.qty}
            onChange={(e) => setLineForm({ ...lineForm, qty: e.target.value })}
            className="w-24 border rounded-lg px-2 py-1.5 text-sm" />
          <input required type="number" step="0.01" placeholder="السعر" value={lineForm.rate}
            onChange={(e) => setLineForm({ ...lineForm, rate: e.target.value })}
            className="w-24 border rounded-lg px-2 py-1.5 text-sm" />
          <button type="submit" className="bg-blue-600 text-white px-3 rounded-lg text-sm hover:bg-blue-700">إضافة</button>
        </form>
      </div>
    </div>
  )
}

export default function WorkOrders() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['workOrders'], queryFn: () => workOrders.list() })
  const { data: bomData } = useQuery({ queryKey: ['boms'], queryFn: () => boms.list() })
  const [showNewWO, setShowNewWO] = useState(false)
  const [showNewBOM, setShowNewBOM] = useState(false)
  const [selectedBOM, setSelectedBOM] = useState(null)
  const [error, setError] = useState('')

  const transition = useMutation({
    mutationFn: ({ id, status }) => workOrders.update(id, { status }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['workOrders'] }); queryClient.invalidateQueries({ queryKey: ['items'] }) },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const bomName = (id) => bomData?.results?.find((b) => b.id === id)?.bom_name || '—'

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">أوامر الإنتاج</h2>
          <p className="text-gray-500 text-sm">إتمام الإنتاج يستهلك المواد الخام تلقائيًا وينتج الصنف النهائي بالمخزون</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowNewBOM(true)} className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-gray-200">
            <Layers size={18} /> BOM جديدة
          </button>
          <button onClick={() => setShowNewWO(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
            <Plus size={18} /> أمر إنتاج جديد
          </button>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-4 border border-red-200">{error}</div>}

      {!!bomData?.results?.length && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-500 mb-2">قوائم المواد (BOM) — اضغط لإدارة المواد الخام</h3>
          <div className="flex flex-wrap gap-2">
            {bomData.results.map((b) => (
              <button key={b.id} onClick={() => setSelectedBOM(b)}
                className="flex items-center gap-1.5 bg-white border rounded-lg px-3 py-1.5 text-sm hover:bg-gray-50">
                <Layers size={14} className="text-gray-400" /> {b.bom_name}
                <span className="text-xs text-gray-400">({b.total_cost})</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">رقم الأمر</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">BOM</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الكمية</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">المنتج</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الحالة</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data?.results?.map((wo) => (
              <tr key={wo.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-blue-600 flex items-center gap-2">
                  <Factory size={16} className="text-gray-400" /> {wo.wo_number}
                </td>
                <td className="px-6 py-4 text-gray-600 text-sm">{bomName(wo.bom)}</td>
                <td className="px-6 py-4 text-gray-700">{wo.produced_qty} / {wo.qty_to_produce}</td>
                <td className="px-6 py-4 text-gray-500 text-sm">{wo.item_to_manufacture}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLES[wo.status] || 'bg-gray-100'}`}>{wo.status}</span>
                </td>
                <td className="px-6 py-4">
                  {wo.status === 'Draft' && (
                    <button onClick={() => transition.mutate({ id: wo.id, status: 'In Progress' })}
                      className="flex items-center gap-1 text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-lg hover:bg-blue-100">
                      <PlayCircle size={14} /> بدء التنفيذ
                    </button>
                  )}
                  {wo.status === 'In Progress' && (
                    <button onClick={() => transition.mutate({ id: wo.id, status: 'Completed' })}
                      className="flex items-center gap-1 text-xs bg-green-50 text-green-700 px-2 py-1 rounded-lg hover:bg-green-100">
                      <CheckCircle2 size={14} /> إتمام الإنتاج
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {!data?.results?.length && (
              <tr><td colSpan={6} className="text-center text-gray-400 py-8">لا يوجد أوامر إنتاج بعد</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showNewBOM && <NewBOMModal onClose={() => setShowNewBOM(false)} />}
      {showNewWO && <NewWOModal onClose={() => setShowNewWO(false)} />}
      {selectedBOM && <BOMPanel bom={selectedBOM} onClose={() => setSelectedBOM(null)} />}
    </div>
  )
}
