import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { payrolls, employees } from '../lib/api'
import { Plus, Wallet } from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

const STATUS_STYLES = {
  Draft: 'bg-yellow-100 text-yellow-700',
  Approved: 'bg-blue-100 text-blue-700',
  Paid: 'bg-green-100 text-green-700',
  Cancelled: 'bg-gray-100 text-gray-500',
}

export default function Payrolls() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['payrolls'], queryFn: () => payrolls.list() })
  const { data: empData } = useQuery({ queryKey: ['employees'], queryFn: () => employees.list() })
  const [form, setForm] = useState({ employee: '', pay_period_start: '', pay_period_end: '', basic_salary: '' })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => payrolls.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payrolls'] })
      setForm({ employee: '', pay_period_start: '', pay_period_end: '', basic_salary: '' })
      setError('')
    },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const updateStatus = useMutation({
    mutationFn: ({ id, status }) => payrolls.update(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payrolls'] }),
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const employeeName = (id) => {
    const e = empData?.results?.find((emp) => emp.id === id)
    return e ? `${e.first_name} ${e.last_name}` : id
  }

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">الرواتب</h2>
        <p className="text-gray-500 text-sm">صافي الراتب يُحسب تلقائيًا، والنظام يمنع تكرار فترة رواتب متراكبة لنفس الموظف</p>
      </div>

      {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-4 border border-red-200">{error}</div>}

      <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }}
        className="bg-white rounded-xl shadow-sm border p-4 mb-6 grid grid-cols-2 md:grid-cols-5 gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-500 mb-1">الموظف</label>
          <select required value={form.employee} onChange={(e) => setForm({ ...form, employee: e.target.value })}
            className="w-full border rounded-lg px-2 py-1.5 text-sm">
            <option value="">اختر</option>
            {empData?.results?.map((e) => <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">بداية الفترة</label>
          <input required type="date" value={form.pay_period_start} onChange={(e) => setForm({ ...form, pay_period_start: e.target.value })}
            className="w-full border rounded-lg px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">نهاية الفترة</label>
          <input required type="date" value={form.pay_period_end} onChange={(e) => setForm({ ...form, pay_period_end: e.target.value })}
            className="w-full border rounded-lg px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">الراتب الأساسي</label>
          <input required type="number" step="0.01" value={form.basic_salary} onChange={(e) => setForm({ ...form, basic_salary: e.target.value })}
            className="w-full border rounded-lg px-2 py-1.5 text-sm" />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm flex items-center gap-2 justify-center hover:bg-blue-700">
          <Plus size={16} /> إنشاء
        </button>
      </form>

      <div className="bg-white rounded-xl shadow-sm divide-y">
        {data?.results?.map((p) => (
          <div key={p.id} className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Wallet size={18} className="text-gray-400" />
              <div>
                <p className="font-medium text-gray-800">{employeeName(p.employee)}</p>
                <p className="text-xs text-gray-500">{p.pay_period_start} إلى {p.pay_period_end}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-left">
                <p className="text-xs text-gray-400">صافي الراتب</p>
                <p className="font-semibold">{p.net_salary} {p.currency}</p>
              </div>
              <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_STYLES[p.status]}`}>{p.status}</span>
              {p.status === 'Draft' && (
                <button onClick={() => updateStatus.mutate({ id: p.id, status: 'Approved' })}
                  className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-lg hover:bg-blue-100">اعتماد</button>
              )}
              {p.status === 'Approved' && (
                <button onClick={() => updateStatus.mutate({ id: p.id, status: 'Paid' })}
                  className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-lg hover:bg-green-100">تأكيد الدفع</button>
              )}
            </div>
          </div>
        ))}
        {!data?.results?.length && <p className="text-gray-400 text-center py-8">لا يوجد سجلات رواتب بعد</p>}
      </div>
    </div>
  )
}
