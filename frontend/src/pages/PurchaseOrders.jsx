import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { purchaseOrders, purchaseOrderItems, suppliers, warehouses, items as itemsApi } from '../lib/api'
import { Plus, X, Package, CheckCircle2, Truck } from 'lucide-react'

const STATUS_STYLES = {
  Draft: 'bg-yellow-100 text-yellow-700',
  Submitted: 'bg-blue-100 text-blue-700',
  Received: 'bg-green-100 text-green-700',
  Cancelled: 'bg-gray-100 text-gray-500',
}

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

function NewPOModal({ onClose }) {
  const queryClient = useQueryClient()
  const { data: supplierData } = useQuery({ queryKey: ['suppliers'], queryFn: () => suppliers.list() })
  const { data: warehouseData } = useQuery({ queryKey: ['warehouses'], queryFn: () => warehouses.list() })
  const [form, setForm] = useState({ po_number: '', supplier: '', warehouse: '', transaction_date: new Date().toISOString().slice(0, 10) })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => purchaseOrders.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] })
      onClose()
    },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">أمر شراء جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form
          onSubmit={(e) => { e.preventDefault(); createMutation.mutate({ ...form, company: supplierData?.results?.[0]?.company }) }}
          className="space-y-3"
        >
          <div>
            <label className="block text-sm text-gray-600 mb-1">رقم الأمر</label>
            <input required value={form.po_number} onChange={(e) => setForm({ ...form, po_number: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="PO-2026-001" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">المورد</label>
            <select required value={form.supplier} onChange={(e) => setForm({ ...form, supplier: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">اختر مورد</option>
              {supplierData?.results?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">المستودع</label>
            <select value={form.warehouse} onChange={(e) => setForm({ ...form, warehouse: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">بدون تحديد الآن</option>
              {warehouseData?.results?.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
            <p className="text-xs text-gray-400 mt-1">لازم تحدد مستودع قبل ما تعمل "استلام" للأمر.</p>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">تاريخ الأمر</label>
            <input type="date" required value={form.transaction_date}
              onChange={(e) => setForm({ ...form, transaction_date: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <button type="submit" disabled={createMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
            {createMutation.isPending ? 'جارِ الإنشاء...' : 'إنشاء الأمر'}
          </button>
        </form>
      </div>
    </div>
  )
}

function POPanel({ po, onClose }) {
  const queryClient = useQueryClient()
  const { data: itemLines } = useQuery({
    queryKey: ['po-items', po.id],
    queryFn: () => purchaseOrderItems.list({ purchase_order: po.id }),
  })
  const { data: itemsData } = useQuery({ queryKey: ['items'], queryFn: () => itemsApi.list() })
  const [lineForm, setLineForm] = useState({ item: '', qty: '', rate: '' })
  const [error, setError] = useState('')

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['po-items', po.id] })
    queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] })
  }

  const addLine = useMutation({
    mutationFn: (data) => purchaseOrderItems.create({ ...data, purchase_order: po.id }),
    onSuccess: () => { invalidate(); setLineForm({ item: '', qty: '', rate: '' }); setError('') },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const transition = useMutation({
    mutationFn: (status) => purchaseOrders.update(po.id, { status }),
    onSuccess: invalidate,
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const isDraft = po.status === 'Draft'
  const isSubmitted = po.status === 'Submitted'

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-bold text-gray-800">{po.po_number}</h3>
            <span className={`inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[po.status]}`}>{po.status}</span>
          </div>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>

        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}

        <div className="grid grid-cols-3 gap-3 text-sm mb-4 bg-gray-50 rounded-lg p-3">
          <div><span className="text-gray-400">الكمية</span><div className="font-semibold">{po.total_qty}</div></div>
          <div><span className="text-gray-400">الإجمالي</span><div className="font-semibold">{po.total_amount} {po.currency}</div></div>
          <div><span className="text-gray-400">الصافي</span><div className="font-semibold">{po.grand_total} {po.currency}</div></div>
        </div>

        <h4 className="font-semibold text-gray-700 mb-2 flex items-center gap-2"><Package size={16} /> الأصناف</h4>
        <table className="w-full text-sm mb-3">
          <thead>
            <tr className="text-gray-400 text-xs">
              <th className="text-right py-1">الصنف</th>
              <th className="text-right py-1">الكمية</th>
              <th className="text-right py-1">السعر</th>
              <th className="text-right py-1">الإجمالي</th>
            </tr>
          </thead>
          <tbody>
            {itemLines?.results?.map((line) => (
              <tr key={line.id} className="border-t">
                <td className="py-2">{itemsData?.results?.find((i) => i.id === line.item)?.item_name || line.item}</td>
                <td className="py-2">{line.qty}</td>
                <td className="py-2">{line.rate}</td>
                <td className="py-2 font-medium">{line.amount}</td>
              </tr>
            ))}
            {!itemLines?.results?.length && (
              <tr><td colSpan={4} className="text-center text-gray-400 py-4">لا يوجد أصناف بعد</td></tr>
            )}
          </tbody>
        </table>

        {isDraft && (
          <form
            onSubmit={(e) => { e.preventDefault(); addLine.mutate({ item: lineForm.item, qty: lineForm.qty, rate: lineForm.rate }) }}
            className="flex gap-2 mb-4"
          >
            <select required value={lineForm.item} onChange={(e) => setLineForm({ ...lineForm, item: e.target.value })}
              className="flex-1 border rounded-lg px-2 py-1.5 text-sm">
              <option value="">اختر صنف</option>
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
        )}

        <div className="flex gap-2 justify-end pt-3 border-t">
          {isDraft && (
            <button onClick={() => transition.mutate('Submitted')}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
              <CheckCircle2 size={16} /> اعتماد الأمر
            </button>
          )}
          {isSubmitted && (
            <button onClick={() => transition.mutate('Received')}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700">
              <Truck size={16} /> تأكيد الاستلام (يحدّث المخزون)
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default function PurchaseOrders() {
  const { data, isLoading } = useQuery({ queryKey: ['purchaseOrders'], queryFn: () => purchaseOrders.list() })
  const { data: supplierData } = useQuery({ queryKey: ['suppliers'], queryFn: () => suppliers.list() })
  const [showNew, setShowNew] = useState(false)
  const [selectedPO, setSelectedPO] = useState(null)

  const supplierName = (id) => supplierData?.results?.find((s) => s.id === id)?.name || id

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">أوامر الشراء</h2>
          <p className="text-gray-500 text-sm">إدارة أوامر الشراء من الموردين ومتابعة الاستلام</p>
        </div>
        <button onClick={() => setShowNew(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> أمر شراء جديد
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">رقم الأمر</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">المورد</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">التاريخ</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الإجمالي</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الحالة</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data?.results?.map((po) => (
              <tr key={po.id} onClick={() => setSelectedPO(po)} className="hover:bg-gray-50 cursor-pointer">
                <td className="px-6 py-4 font-medium text-blue-600">{po.po_number}</td>
                <td className="px-6 py-4 text-gray-700">{supplierName(po.supplier)}</td>
                <td className="px-6 py-4 text-gray-600 text-sm">{po.transaction_date}</td>
                <td className="px-6 py-4 font-medium">{po.grand_total} {po.currency}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLES[po.status] || 'bg-gray-100 text-gray-700'}`}>{po.status}</span>
                </td>
              </tr>
            ))}
            {!data?.results?.length && (
              <tr><td colSpan={5} className="text-center text-gray-400 py-8">لا يوجد أوامر شراء بعد</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showNew && <NewPOModal onClose={() => setShowNew(false)} />}
      {selectedPO && <POPanel po={selectedPO} onClose={() => setSelectedPO(null)} />}
    </div>
  )
}
