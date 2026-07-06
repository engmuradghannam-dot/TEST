import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { budgets, accounts } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Plus, X, PiggyBank } from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

function NewBudgetModal({ onClose }) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const { data: accountData } = useQuery({ queryKey: ['accounts'], queryFn: () => accounts.list() })
  const [form, setForm] = useState({
    name: '', fiscal_year: '2026', account: '', budget_amount: '', actual_amount: 0,
    start_date: '2026-01-01', end_date: '2026-12-31',
  })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => budgets.create({ ...data, company: user?.company }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['budgets'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">ميزانية جديدة</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-600 mb-1">اسم الميزانية</label>
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="ميزانية التشغيل 2026" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">الحساب</label>
            <select required value={form.account} onChange={(e) => setForm({ ...form, account: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">اختر حساب</option>
              {accountData?.results?.map((a) => <option key={a.id} value={a.id}>{a.account_number} - {a.account_name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">المبلغ المخطط</label>
              <input required type="number" step="0.01" value={form.budget_amount}
                onChange={(e) => setForm({ ...form, budget_amount: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">الفعلي حتى الآن</label>
              <input type="number" step="0.01" value={form.actual_amount}
                onChange={(e) => setForm({ ...form, actual_amount: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">من تاريخ</label>
              <input type="date" required value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">إلى تاريخ</label>
              <input type="date" required value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <button type="submit" disabled={createMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
            {createMutation.isPending ? 'جارِ الإنشاء...' : 'إنشاء الميزانية'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default function Budgets() {
  const { data, isLoading } = useQuery({ queryKey: ['budgets'], queryFn: () => budgets.list() })
  const { data: accountData } = useQuery({ queryKey: ['accounts'], queryFn: () => accounts.list() })
  const [showNew, setShowNew] = useState(false)

  const accountName = (id) => accountData?.results?.find((a) => a.id === id)?.account_name || id

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">الميزانيات</h2>
          <p className="text-gray-500 text-sm">الانحراف عن الميزانية محسوب تلقائيًا (الفعلي - المخطط)</p>
        </div>
        <button onClick={() => setShowNew(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> ميزانية جديدة
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data?.results?.map((b) => {
          const over = Number(b.variance) > 0
          return (
            <div key={b.id} className="bg-white rounded-xl shadow-sm border p-5">
              <div className="flex items-center gap-2 mb-1">
                <PiggyBank className="text-blue-600" size={20} />
                <h3 className="font-bold text-gray-800">{b.name}</h3>
              </div>
              <p className="text-xs text-gray-400 mb-3">{accountName(b.account)} — {b.fiscal_year}</p>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div><span className="text-gray-400 block">المخطط</span><span className="font-semibold">{b.budget_amount}</span></div>
                <div><span className="text-gray-400 block">الفعلي</span><span className="font-semibold">{b.actual_amount}</span></div>
                <div>
                  <span className="text-gray-400 block">الانحراف</span>
                  <span className={`font-semibold ${over ? 'text-red-600' : 'text-green-600'}`}>
                    {b.variance} ({Number(b.variance_percentage).toFixed(1)}%)
                  </span>
                </div>
              </div>
            </div>
          )
        })}
        {!data?.results?.length && <p className="text-gray-400 col-span-2 text-center py-8">لا يوجد ميزانيات بعد</p>}
      </div>

      {showNew && <NewBudgetModal onClose={() => setShowNew(false)} />}
    </div>
  )
}
