import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { journalEntries, accounts } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Plus, X, BookText, CheckCircle2 } from 'lucide-react'

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
}

function NewEntryModal({ onClose }) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const { data: accountData } = useQuery({ queryKey: ['accounts'], queryFn: () => accounts.list() })
  const [form, setForm] = useState({
    entry_number: '', posting_date: new Date().toISOString().slice(0, 10),
    debit_account: '', credit_account: '', amount: '',
  })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => journalEntries.create({ ...data, company: user?.company }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['journalEntries'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">قيد يومية جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-600 mb-1">رقم القيد</label>
            <input required value={form.entry_number} onChange={(e) => setForm({ ...form, entry_number: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="JE-2026-001" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">تاريخ الترحيل</label>
            <input type="date" required value={form.posting_date} onChange={(e) => setForm({ ...form, posting_date: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">من حساب (مدين)</label>
            <select required value={form.debit_account} onChange={(e) => setForm({ ...form, debit_account: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">اختر حساب</option>
              {accountData?.results?.map((a) => <option key={a.id} value={a.id}>{a.account_number} - {a.account_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">إلى حساب (دائن)</label>
            <select required value={form.credit_account} onChange={(e) => setForm({ ...form, credit_account: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">اختر حساب</option>
              {accountData?.results?.map((a) => <option key={a.id} value={a.id}>{a.account_number} - {a.account_name}</option>)}
            </select>
            <p className="text-xs text-gray-400 mt-1">لازم يكون مختلف عن حساب المدين.</p>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">المبلغ</label>
            <input required type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <button type="submit" disabled={createMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
            {createMutation.isPending ? 'جارِ الإنشاء...' : 'إنشاء القيد'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default function JournalEntries() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['journalEntries'], queryFn: () => journalEntries.list() })
  const { data: accountData } = useQuery({ queryKey: ['accounts'], queryFn: () => accounts.list() })
  const [showNew, setShowNew] = useState(false)
  const [error, setError] = useState('')

  const submitMutation = useMutation({
    mutationFn: (id) => journalEntries.update(id, { status: 'Submitted' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['journalEntries'] }),
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const accountLabel = (id) => {
    const a = accountData?.results?.find((acc) => acc.id === id)
    return a ? `${a.account_number} - ${a.account_name}` : id
  }

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">قيود اليومية</h2>
          <p className="text-gray-500 text-sm">القيد لازم يكون بمبلغ موجب وحسابين مختلفين قبل ما تقدر تعتمده</p>
        </div>
        <button onClick={() => setShowNew(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> قيد جديد
        </button>
      </div>

      {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-4 border border-red-200">{error}</div>}

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">رقم القيد</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">مدين</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">دائن</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">المبلغ</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الحالة</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data?.results?.map((je) => (
              <tr key={je.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-blue-600 flex items-center gap-2">
                  <BookText size={16} className="text-gray-400" /> {je.entry_number}
                </td>
                <td className="px-6 py-4 text-gray-700 text-sm">{accountLabel(je.debit_account)}</td>
                <td className="px-6 py-4 text-gray-700 text-sm">{accountLabel(je.credit_account)}</td>
                <td className="px-6 py-4 font-medium">{je.amount} {je.currency}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLES[je.status] || 'bg-gray-100'}`}>{je.status}</span>
                </td>
                <td className="px-6 py-4">
                  {je.status === 'Draft' && (
                    <button onClick={() => submitMutation.mutate(je.id)}
                      className="flex items-center gap-1 text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-lg hover:bg-blue-100">
                      <CheckCircle2 size={14} /> اعتماد
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {!data?.results?.length && (
              <tr><td colSpan={6} className="text-center text-gray-400 py-8">لا يوجد قيود بعد</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showNew && <NewEntryModal onClose={() => setShowNew(false)} />}
    </div>
  )
}
