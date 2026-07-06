import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { leads, opportunities } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Plus, X, UserPlus, Target } from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

const LEAD_STATUS_STYLES = {
  Open: 'bg-gray-100 text-gray-600',
  Replied: 'bg-blue-100 text-blue-700',
  Opportunity: 'bg-purple-100 text-purple-700',
  Quotation: 'bg-yellow-100 text-yellow-700',
  Lost: 'bg-red-100 text-red-600',
  Converted: 'bg-green-100 text-green-700',
}

function NewLeadModal({ onClose }) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [form, setForm] = useState({ lead_name: '', organization: '', email: '', phone: '', source: '' })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => leads.create({ ...data, company: user?.company }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['leads'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">عميل محتمل جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <input required value={form.lead_name} onChange={(e) => setForm({ ...form, lead_name: e.target.value })}
            placeholder="اسم العميل المحتمل" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <input value={form.organization} onChange={(e) => setForm({ ...form, organization: e.target.value })}
            placeholder="الجهة/الشركة" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
            placeholder="البريد الإلكتروني" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
            placeholder="الهاتف" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <input value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })}
            placeholder="مصدر العميل (موقع، إحالة...)" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700">إنشاء</button>
        </form>
      </div>
    </div>
  )
}

function NewOpportunityModal({ leadsData, onClose }) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [form, setForm] = useState({ opportunity_name: '', lead: '', customer_name: '', expected_amount: '', probability: 50 })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => opportunities.create({ ...data, company: user?.company }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['opportunities'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">فرصة بيعية جديدة</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <input required value={form.opportunity_name} onChange={(e) => setForm({ ...form, opportunity_name: e.target.value })}
            placeholder="اسم الفرصة" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <select value={form.lead} onChange={(e) => setForm({ ...form, lead: e.target.value })}
            className="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="">بدون ربط بعميل محتمل</option>
            {leadsData?.results?.map((l) => <option key={l.id} value={l.id}>{l.lead_name}</option>)}
          </select>
          <input value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
            placeholder="اسم العميل" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <input required type="number" step="0.01" value={form.expected_amount}
            onChange={(e) => setForm({ ...form, expected_amount: e.target.value })}
            placeholder="القيمة المتوقعة" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <div>
            <label className="block text-xs text-gray-500 mb-1">احتمالية الإغلاق: {form.probability}%</label>
            <input type="range" min="0" max="100" value={form.probability}
              onChange={(e) => setForm({ ...form, probability: e.target.value })} className="w-full" />
          </div>
          <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700">إنشاء</button>
        </form>
      </div>
    </div>
  )
}

export default function CRM() {
  const queryClient = useQueryClient()
  const { data: leadsData, isLoading: leadsLoading } = useQuery({ queryKey: ['leads'], queryFn: () => leads.list() })
  const { data: oppData, isLoading: oppLoading } = useQuery({ queryKey: ['opportunities'], queryFn: () => opportunities.list() })
  const [showNewLead, setShowNewLead] = useState(false)
  const [showNewOpp, setShowNewOpp] = useState(false)

  const updateLeadStatus = useMutation({
    mutationFn: ({ id, status }) => leads.update(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['leads'] }),
  })

  if (leadsLoading || oppLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  const pipelineValue = oppData?.results?.reduce((sum, o) => sum + Number(o.expected_amount || 0) * (Number(o.probability || 0) / 100), 0) || 0

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">إدارة علاقات العملاء</h2>
          <p className="text-gray-500 text-sm">القيمة المرجحة لخط الأنابيب: {pipelineValue.toLocaleString()} SAR</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowNewLead(true)} className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-gray-200">
            <UserPlus size={18} /> عميل محتمل
          </button>
          <button onClick={() => setShowNewOpp(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
            <Target size={18} /> فرصة بيعية
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="font-semibold text-gray-700 mb-3">العملاء المحتملون</h3>
          <div className="bg-white rounded-xl shadow-sm divide-y">
            {leadsData?.results?.map((lead) => (
              <div key={lead.id} className="p-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{lead.lead_name}</p>
                  <p className="text-xs text-gray-400">{lead.organization}</p>
                </div>
                <select value={lead.status} onChange={(e) => updateLeadStatus.mutate({ id: lead.id, status: e.target.value })}
                  className={`text-xs font-medium px-2 py-1 rounded-full border-0 ${LEAD_STATUS_STYLES[lead.status]}`}>
                  <option value="Open">مفتوح</option>
                  <option value="Replied">تم الرد</option>
                  <option value="Opportunity">فرصة</option>
                  <option value="Quotation">عرض سعر</option>
                  <option value="Lost">خسارة</option>
                  <option value="Converted">تحول لعميل</option>
                </select>
              </div>
            ))}
            {!leadsData?.results?.length && <p className="p-4 text-gray-400 text-sm text-center">لا يوجد عملاء محتملون بعد</p>}
          </div>
        </div>

        <div>
          <h3 className="font-semibold text-gray-700 mb-3">الفرص البيعية</h3>
          <div className="bg-white rounded-xl shadow-sm divide-y">
            {oppData?.results?.map((opp) => (
              <div key={opp.id} className="p-3">
                <div className="flex justify-between items-center">
                  <p className="text-sm font-medium">{opp.opportunity_name}</p>
                  <span className="text-sm font-semibold text-blue-600">{opp.expected_amount} SAR</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-1.5 mt-2">
                  <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: `${opp.probability}%` }} />
                </div>
                <p className="text-xs text-gray-400 mt-1">احتمالية الإغلاق: {opp.probability}%</p>
              </div>
            ))}
            {!oppData?.results?.length && <p className="p-4 text-gray-400 text-sm text-center">لا يوجد فرص بيعية بعد</p>}
          </div>
        </div>
      </div>

      {showNewLead && <NewLeadModal onClose={() => setShowNewLead(false)} />}
      {showNewOpp && <NewOpportunityModal leadsData={leadsData} onClose={() => setShowNewOpp(false)} />}
    </div>
  )
}
