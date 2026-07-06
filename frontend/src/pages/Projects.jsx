import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projects, milestones, risks, issues, changeRequests } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import {
  Plus, X, FolderKanban, Flag, ShieldAlert, Bug, GitPullRequestArrow, AlertTriangle,
} from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

const RISK_LEVEL_STYLES = {
  Critical: 'bg-red-100 text-red-700',
  High: 'bg-orange-100 text-orange-700',
  Medium: 'bg-yellow-100 text-yellow-700',
  Low: 'bg-green-100 text-green-700',
}
const CR_STATUS_STYLES = {
  Pending: 'bg-yellow-100 text-yellow-700',
  Approved: 'bg-blue-100 text-blue-700',
  Rejected: 'bg-red-100 text-red-600',
  Implemented: 'bg-green-100 text-green-700',
}

function NewProjectModal({ onClose }) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [form, setForm] = useState({ project_name: '', project_code: '', budget: '' })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => projects.create({ ...data, company: user?.company }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['projects'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">مشروع جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <input required value={form.project_name} onChange={(e) => setForm({ ...form, project_name: e.target.value })}
            placeholder="اسم المشروع" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <input required value={form.project_code} onChange={(e) => setForm({ ...form, project_code: e.target.value })}
            placeholder="كود المشروع (فريد)" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <input type="number" step="0.01" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })}
            placeholder="الميزانية" className="w-full border rounded-lg px-3 py-2 text-sm" />
          <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700">إنشاء</button>
        </form>
      </div>
    </div>
  )
}

function RisksTab({ project }) {
  const queryClient = useQueryClient()
  const { data } = useQuery({ queryKey: ['risks', project.id], queryFn: () => risks.list({ project: project.id }) })
  const [form, setForm] = useState({ title: '', probability: 3, impact: 3 })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => risks.create({ ...data, project: project.id }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['risks', project.id] }); setForm({ title: '', probability: 3, impact: 3 }) },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div>
      {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
      <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="flex flex-wrap gap-2 mb-4">
        <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
          placeholder="عنوان الخطر" className="flex-1 min-w-[160px] border rounded-lg px-2 py-1.5 text-sm" />
        <select value={form.probability} onChange={(e) => setForm({ ...form, probability: e.target.value })}
          className="border rounded-lg px-2 py-1.5 text-sm">
          {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>احتمالية {n}</option>)}
        </select>
        <select value={form.impact} onChange={(e) => setForm({ ...form, impact: e.target.value })}
          className="border rounded-lg px-2 py-1.5 text-sm">
          {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>تأثير {n}</option>)}
        </select>
        <button type="submit" className="bg-blue-600 text-white px-3 rounded-lg text-sm hover:bg-blue-700">إضافة</button>
      </form>
      <div className="space-y-2">
        {data?.results?.map((r) => (
          <div key={r.id} className="flex items-center justify-between bg-white border rounded-lg p-3">
            <span className="text-sm">{r.title}</span>
            <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${RISK_LEVEL_STYLES[r.risk_level]}`}>
              {r.risk_level} ({r.risk_score})
            </span>
          </div>
        ))}
        {!data?.results?.length && <p className="text-gray-400 text-sm text-center py-6">لا يوجد مخاطر مسجلة</p>}
      </div>
    </div>
  )
}

function IssuesTab({ project }) {
  const queryClient = useQueryClient()
  const { data } = useQuery({ queryKey: ['issues', project.id], queryFn: () => issues.list({ project: project.id }) })
  const [title, setTitle] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => issues.create({ ...data, project: project.id }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['issues', project.id] }); setTitle('') },
  })
  const updateStatus = useMutation({
    mutationFn: ({ id, status }) => issues.update(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['issues', project.id] }),
  })

  return (
    <div>
      <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate({ title }) }} className="flex gap-2 mb-4">
        <input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="مشكلة جديدة"
          className="flex-1 border rounded-lg px-2 py-1.5 text-sm" />
        <button type="submit" className="bg-blue-600 text-white px-3 rounded-lg text-sm hover:bg-blue-700">إضافة</button>
      </form>
      <div className="space-y-2">
        {data?.results?.map((i) => (
          <div key={i.id} className="flex items-center justify-between bg-white border rounded-lg p-3">
            <span className="text-sm">{i.title} <span className="text-xs text-gray-400">({i.severity})</span></span>
            <select value={i.status} onChange={(e) => updateStatus.mutate({ id: i.id, status: e.target.value })}
              className="text-xs border rounded-lg px-2 py-1">
              <option value="Open">مفتوحة</option>
              <option value="In Progress">قيد المعالجة</option>
              <option value="Resolved">تم الحل</option>
              <option value="Closed">مغلقة</option>
            </select>
          </div>
        ))}
        {!data?.results?.length && <p className="text-gray-400 text-sm text-center py-6">لا يوجد مشاكل مسجلة</p>}
      </div>
    </div>
  )
}

function MilestonesTab({ project }) {
  const queryClient = useQueryClient()
  const { data } = useQuery({ queryKey: ['milestones', project.id], queryFn: () => milestones.list({ project: project.id }) })
  const [form, setForm] = useState({ name: '', due_date: '' })

  const createMutation = useMutation({
    mutationFn: (data) => milestones.create({ ...data, project: project.id }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['milestones', project.id] }); setForm({ name: '', due_date: '' }) },
  })

  return (
    <div>
      <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="flex gap-2 mb-4">
        <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="اسم المعلم"
          className="flex-1 border rounded-lg px-2 py-1.5 text-sm" />
        <input required type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })}
          className="border rounded-lg px-2 py-1.5 text-sm" />
        <button type="submit" className="bg-blue-600 text-white px-3 rounded-lg text-sm hover:bg-blue-700">إضافة</button>
      </form>
      <div className="space-y-2">
        {data?.results?.map((m) => (
          <div key={m.id} className="flex items-center justify-between bg-white border rounded-lg p-3">
            <span className="flex items-center gap-2 text-sm"><Flag size={14} className="text-gray-400" /> {m.name}</span>
            <span className="flex items-center gap-2 text-xs text-gray-500">
              {m.due_date}
              {m.is_overdue && <span className="flex items-center gap-1 text-red-600 font-medium"><AlertTriangle size={12} /> متأخر</span>}
            </span>
          </div>
        ))}
        {!data?.results?.length && <p className="text-gray-400 text-sm text-center py-6">لا يوجد معالم بعد</p>}
      </div>
    </div>
  )
}

function ChangeRequestsTab({ project }) {
  const queryClient = useQueryClient()
  const { data } = useQuery({ queryKey: ['changeRequests', project.id], queryFn: () => changeRequests.list({ project: project.id }) })
  const [title, setTitle] = useState('')
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => changeRequests.create({ ...data, project: project.id }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['changeRequests', project.id] }); setTitle('') },
  })
  const transition = useMutation({
    mutationFn: ({ id, status }) => changeRequests.update(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['changeRequests', project.id] }),
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div>
      {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
      <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate({ title }) }} className="flex gap-2 mb-4">
        <input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="طلب تغيير جديد"
          className="flex-1 border rounded-lg px-2 py-1.5 text-sm" />
        <button type="submit" className="bg-blue-600 text-white px-3 rounded-lg text-sm hover:bg-blue-700">إضافة</button>
      </form>
      <div className="space-y-2">
        {data?.results?.map((cr) => (
          <div key={cr.id} className="flex items-center justify-between bg-white border rounded-lg p-3">
            <span className="text-sm">{cr.title}</span>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${CR_STATUS_STYLES[cr.status]}`}>{cr.status}</span>
              {cr.status === 'Pending' && (
                <>
                  <button onClick={() => transition.mutate({ id: cr.id, status: 'Approved' })}
                    className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-lg hover:bg-green-100">موافقة</button>
                  <button onClick={() => transition.mutate({ id: cr.id, status: 'Rejected' })}
                    className="text-xs bg-red-50 text-red-600 px-2 py-1 rounded-lg hover:bg-red-100">رفض</button>
                </>
              )}
              {cr.status === 'Approved' && (
                <button onClick={() => transition.mutate({ id: cr.id, status: 'Implemented' })}
                  className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-lg hover:bg-blue-100">تنفيذ</button>
              )}
            </div>
          </div>
        ))}
        {!data?.results?.length && <p className="text-gray-400 text-sm text-center py-6">لا يوجد طلبات تغيير بعد</p>}
      </div>
    </div>
  )
}

function ProjectPanel({ project, onClose }) {
  const [tab, setTab] = useState('milestones')
  const tabs = [
    { key: 'milestones', label: 'المعالم', icon: Flag },
    { key: 'risks', label: 'المخاطر', icon: ShieldAlert },
    { key: 'issues', label: 'المشاكل', icon: Bug },
    { key: 'changes', label: 'طلبات التغيير', icon: GitPullRequestArrow },
  ]

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-bold text-gray-800">{project.project_name}</h3>
            <p className="text-xs text-gray-400">نسبة الإنجاز: {project.progress_percent}%</p>
          </div>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>

        <div className="flex gap-1 border-b mb-4">
          {tabs.map((t) => {
            const Icon = t.icon
            return (
              <button key={t.key} onClick={() => setTab(t.key)}
                className={`flex items-center gap-1.5 px-3 py-2 text-sm border-b-2 -mb-px ${
                  tab === t.key ? 'border-blue-600 text-blue-600 font-medium' : 'border-transparent text-gray-500'
                }`}>
                <Icon size={14} /> {t.label}
              </button>
            )
          })}
        </div>

        {tab === 'milestones' && <MilestonesTab project={project} />}
        {tab === 'risks' && <RisksTab project={project} />}
        {tab === 'issues' && <IssuesTab project={project} />}
        {tab === 'changes' && <ChangeRequestsTab project={project} />}
      </div>
    </div>
  )
}

export default function Projects() {
  const { data, isLoading } = useQuery({ queryKey: ['projects'], queryFn: () => projects.list() })
  const [showNew, setShowNew] = useState(false)
  const [selected, setSelected] = useState(null)

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">المشاريع</h2>
          <p className="text-gray-500 text-sm">نسبة الإنجاز محسوبة تلقائيًا من نسبة المهام المكتملة</p>
        </div>
        <button onClick={() => setShowNew(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> مشروع جديد
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data?.results?.map((p) => (
          <div key={p.id} onClick={() => setSelected(p)} className="bg-white rounded-xl shadow-sm border p-5 cursor-pointer hover:shadow-md transition-shadow">
            <div className="flex items-center gap-2 mb-2">
              <FolderKanban className="text-blue-600" size={20} />
              <h3 className="font-bold text-gray-800">{p.project_name}</h3>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 mb-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${p.progress_percent}%` }} />
            </div>
            <p className="text-xs text-gray-500">{p.progress_percent}% مكتمل — الميزانية: {p.budget}</p>
          </div>
        ))}
        {!data?.results?.length && <p className="text-gray-400 col-span-2 text-center py-8">لا يوجد مشاريع بعد</p>}
      </div>

      {showNew && <NewProjectModal onClose={() => setShowNew(false)} />}
      {selected && <ProjectPanel project={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
