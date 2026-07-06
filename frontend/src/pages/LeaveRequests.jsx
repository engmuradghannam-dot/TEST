import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { leaveRequests, employees } from '../lib/api'
import { Plus, CalendarDays } from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

const STATUS_STYLES = {
  Pending: 'bg-yellow-100 text-yellow-700',
  Approved: 'bg-green-100 text-green-700',
  Rejected: 'bg-red-100 text-red-600',
  Cancelled: 'bg-gray-100 text-gray-500',
}

export default function LeaveRequests() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['leaveRequests'], queryFn: () => leaveRequests.list() })
  const { data: empData } = useQuery({ queryKey: ['employees'], queryFn: () => employees.list() })
  const [form, setForm] = useState({ employee: '', leave_type: 'Annual', start_date: '', end_date: '', reason: '' })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => leaveRequests.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leaveRequests'] })
      setForm({ employee: '', leave_type: 'Annual', start_date: '', end_date: '', reason: '' })
      setError('')
    },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const updateStatus = useMutation({
    mutationFn: ({ id, status }) => leaveRequests.update(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['leaveRequests'] }),
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
        <h2 className="text-2xl font-bold text-gray-800">طلبات الإجازة</h2>
        <p className="text-gray-500 text-sm">النظام يرفض تلقائيًا أي طلب متراكب مع إجازة أخرى لنفس الموظف</p>
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
          <label className="block text-xs text-gray-500 mb-1">نوع الإجازة</label>
          <select value={form.leave_type} onChange={(e) => setForm({ ...form, leave_type: e.target.value })}
            className="w-full border rounded-lg px-2 py-1.5 text-sm">
            <option value="Annual">سنوية</option>
            <option value="Sick">مرضية</option>
            <option value="Unpaid">بدون راتب</option>
            <option value="Emergency">طارئة</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">من</label>
          <input required type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })}
            className="w-full border rounded-lg px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">إلى</label>
          <input required type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })}
            className="w-full border rounded-lg px-2 py-1.5 text-sm" />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm flex items-center gap-2 justify-center hover:bg-blue-700">
          <Plus size={16} /> تقديم طلب
        </button>
      </form>

      <div className="bg-white rounded-xl shadow-sm divide-y">
        {data?.results?.map((leave) => (
          <div key={leave.id} className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CalendarDays size={18} className="text-gray-400" />
              <div>
                <p className="font-medium text-gray-800">{employeeName(leave.employee)} — {leave.leave_type}</p>
                <p className="text-xs text-gray-500">{leave.start_date} إلى {leave.end_date} ({leave.duration_days} يوم)</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_STYLES[leave.status]}`}>{leave.status}</span>
              {leave.status === 'Pending' && (
                <>
                  <button onClick={() => updateStatus.mutate({ id: leave.id, status: 'Approved' })}
                    className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-lg hover:bg-green-100">قبول</button>
                  <button onClick={() => updateStatus.mutate({ id: leave.id, status: 'Rejected' })}
                    className="text-xs bg-red-50 text-red-600 px-2 py-1 rounded-lg hover:bg-red-100">رفض</button>
                </>
              )}
            </div>
          </div>
        ))}
        {!data?.results?.length && <p className="text-gray-400 text-center py-8">لا يوجد طلبات إجازة بعد</p>}
      </div>
    </div>
  )
}
