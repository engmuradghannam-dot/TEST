import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { projects, tasks, milestones, stakeholders, risks, issues, changeRequests } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import {
  Plus, X, Edit2, Trash2, Calendar, Users, AlertTriangle, CheckCircle2,
  Clock, TrendingUp, DollarSign, BarChart3, Target, FolderKanban,
  Columns, GitGraph, Brain, ChevronRight
} from 'lucide-react'

const STATUS_OPTIONS = [
  { value: 'Planning', label: 'تخطيط', color: 'bg-gray-100 text-gray-700' },
  { value: 'In Progress', label: 'قيد التنفيذ', color: 'bg-blue-100 text-blue-700' },
  { value: 'On Hold', label: 'معلق', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'Completed', label: 'مكتمل', color: 'bg-green-100 text-green-700' },
  { value: 'Cancelled', label: 'ملغي', color: 'bg-red-100 text-red-700' },
]

const PRIORITY_OPTIONS = [
  { value: 'Low', label: 'منخفض', color: 'bg-gray-100 text-gray-700' },
  { value: 'Medium', label: 'متوسط', color: 'bg-blue-100 text-blue-700' },
  { value: 'High', label: 'عالي', color: 'bg-orange-100 text-orange-700' },
  { value: 'Urgent', label: 'عاجل', color: 'bg-red-100 text-red-700' },
]

export default function Projects() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [showDetail, setShowDetail] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [form, setForm] = useState({
    project_name: '', project_code: '', status: 'Planning', priority: 'Medium',
    expected_start: '', expected_end: '', budget: '', estimated_cost: '',
    description: '', owner: '',
  })

  const { data, isLoading } = useQuery({ queryKey: ['projects'], queryFn: () => projects.list() })
  const { data: tasksData } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasks.list(),
    enabled: !!showDetail,
  })
  const { data: milestonesData } = useQuery({
    queryKey: ['milestones'],
    queryFn: () => milestones.list(),
    enabled: !!showDetail,
  })
  const { data: risksData } = useQuery({
    queryKey: ['risks'],
    queryFn: () => risks.list(),
    enabled: !!showDetail,
  })
  const { data: issuesData } = useQuery({
    queryKey: ['issues'],
    queryFn: () => issues.list(),
    enabled: !!showDetail,
  })
  const { data: stakeholdersData } = useQuery({
    queryKey: ['stakeholders'],
    queryFn: () => stakeholders.list(),
    enabled: !!showDetail,
  })
  const { data: changeRequestsData } = useQuery({
    queryKey: ['change-requests'],
    queryFn: () => changeRequests.list(),
    enabled: !!showDetail,
  })

  const createMutation = useMutation({
    mutationFn: projects.create,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['projects'] }); setShowForm(false); resetForm() },
  })
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => projects.update(id, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['projects'] }); setShowForm(false); setEditingId(null); resetForm() },
  })
  const deleteMutation = useMutation({
    mutationFn: (id) => projects.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
  })

  const resetForm = () => setForm({
    project_name: '', project_code: '', status: 'Planning', priority: 'Medium',
    expected_start: '', expected_end: '', budget: '', estimated_cost: '',
    description: '', owner: '',
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = { ...form, budget: form.budget ? parseFloat(form.budget) : 0, estimated_cost: form.estimated_cost ? parseFloat(form.estimated_cost) : 0 }
    if (editingId) updateMutation.mutate({ id: editingId, data: payload })
    else createMutation.mutate(payload)
  }

  const handleEdit = (item) => {
    setForm({
      project_name: item.project_name || '', project_code: item.project_code || '',
      status: item.status || 'Planning', priority: item.priority || 'Medium',
      expected_start: item.expected_start || '', expected_end: item.expected_end || '',
      budget: item.budget || '', estimated_cost: item.estimated_cost || '',
      description: item.description || '', owner: item.owner || '',
    })
    setEditingId(item.id)
    setShowForm(true)
  }

  const openDetail = (project) => {
    setShowDetail(project)
    setActiveTab('overview')
  }

  const projectTasks = tasksData?.results?.filter((t) => t.project === showDetail?.id) || []
  const projectMilestones = milestonesData?.results?.filter((m) => m.project === showDetail?.id) || []
  const projectRisks = risksData?.results?.filter((r) => r.project === showDetail?.id) || []
  const projectIssues = issuesData?.results?.filter((i) => i.project === showDetail?.id) || []
  const projectStakeholders = stakeholdersData?.results?.filter((s) => s.project === showDetail?.id) || []
  const projectChangeRequests = changeRequestsData?.results?.filter((cr) => cr.project === showDetail?.id) || []

  const completedTasks = projectTasks.filter((t) => t.status === 'Completed').length
  const totalTasks = projectTasks.length
  const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

  if (isLoading) {
    return (
      <div className="flex justify-center p-10">
        <div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div>
      </div>
    )
  }

  return (
    <div dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">إدارة المشاريع</h2>
          <p className="text-gray-500 text-sm">تخطيط وتنفيذ ومراقبة المشاريع</p>
        </div>
        <button
          onClick={() => { setShowForm(true); setEditingId(null); resetForm() }}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} /> مشروع جديد
        </button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">{editingId ? 'تعديل مشروع' : 'مشروع جديد'}</h3>
              <button onClick={() => setShowForm(false)}><X size={20} className="text-gray-400" /></button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input required value={form.project_name} onChange={(e) => setForm({ ...form, project_name: e.target.value })} placeholder="اسم المشروع" className="border rounded-lg px-3 py-2 text-sm" />
                <input value={form.project_code} onChange={(e) => setForm({ ...form, project_code: e.target.value })} placeholder="كود المشروع" className="border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="border rounded-lg px-3 py-2 text-sm">
                  {STATUS_OPTIONS.map((s) => (<option key={s.value} value={s.value}>{s.label}</option>))}
                </select>
                <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })} className="border rounded-lg px-3 py-2 text-sm">
                  {PRIORITY_OPTIONS.map((p) => (<option key={p.value} value={p.value}>{p.label}</option>))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <input type="date" value={form.expected_start} onChange={(e) => setForm({ ...form, expected_start: e.target.value })} placeholder="تاريخ البدء" className="border rounded-lg px-3 py-2 text-sm" />
                <input type="date" value={form.expected_end} onChange={(e) => setForm({ ...form, expected_end: e.target.value })} placeholder="تاريخ الانتهاء" className="border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <input type="number" step="0.01" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })} placeholder="الميزانية" className="border rounded-lg px-3 py-2 text-sm" />
                <input type="number" step="0.01" value={form.estimated_cost} onChange={(e) => setForm({ ...form, estimated_cost: e.target.value })} placeholder="التكلفة التقديرية" className="border rounded-lg px-3 py-2 text-sm" />
              </div>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="وصف المشروع" className="w-full border rounded-lg px-3 py-2 text-sm" rows={3} />
              <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">{editingId ? 'تحديث' : 'إنشاء'}</button>
            </form>
          </div>
        </div>
      )}

      {/* Detail View */}
      {showDetail && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-5xl p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <button onClick={() => setShowDetail(null)} className="p-2 hover:bg-gray-100 rounded-lg"><X size={20} /></button>
                <div>
                  <h3 className="text-xl font-bold">{showDetail.project_name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_OPTIONS.find(s => s.value === showDetail.status)?.color || 'bg-gray-100'}`}>
                      {STATUS_OPTIONS.find(s => s.value === showDetail.status)?.label || showDetail.status}
                    </span>
                    <span className="text-xs text-gray-400">{showDetail.project_code}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => navigate(`/kanban/${showDetail.id}`)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-50 text-purple-700 rounded-lg text-sm hover:bg-purple-100"
                >
                  <Columns size={16} /> Kanban
                </button>
                <button
                  onClick={() => navigate(`/gantt/${showDetail.id}`)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-sm hover:bg-blue-100"
                >
                  <GitGraph size={16} /> Gantt
                </button>
                <button
                  onClick={() => navigate('/ai-assistant')}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-blue-50 to-purple-50 text-blue-700 rounded-lg text-sm hover:from-blue-100 hover:to-purple-100"
                >
                  <Brain size={16} /> AI
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 mb-4 border-b pb-2 overflow-x-auto">
              {[
                { key: 'overview', label: 'نظرة عامة', icon: BarChart3 },
                { key: 'tasks', label: 'المهام', icon: CheckCircle2 },
                { key: 'milestones', label: 'المعالم', icon: Target },
                { key: 'risks', label: 'المخاطر', icon: AlertTriangle },
                { key: 'issues', label: 'المشاكل', icon: AlertTriangle },
                { key: 'stakeholders', label: 'أصحاب المصلحة', icon: Users },
                { key: 'changes', label: 'طلبات التغيير', icon: TrendingUp },
              ].map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm ${
                      activeTab === tab.key ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-500 hover:bg-gray-50'
                    }`}
                  >
                    <Icon size={14} /> {tab.label}
                  </button>
                )
              })}
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
              <div className="space-y-4">
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-white rounded-xl p-4 border">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center"><BarChart3 size={20} className="text-blue-600" /></div>
                      <div><p className="text-2xl font-bold">{progress}%</p><p className="text-xs text-gray-500">نسبة الإنجاز</p></div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-2"><div className="bg-blue-500 h-2 rounded-full" style={{ width: `${progress}%` }}></div></div>
                  </div>
                  <div className="bg-white rounded-xl p-4 border">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center"><CheckCircle2 size={20} className="text-green-600" /></div>
                      <div><p className="text-2xl font-bold">{completedTasks}/{totalTasks}</p><p className="text-xs text-gray-500">المهام المكتملة</p></div>
                    </div>
                  </div>
                  <div className="bg-white rounded-xl p-4 border">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center"><DollarSign size={20} className="text-amber-600" /></div>
                      <div><p className="text-2xl font-bold">{showDetail.actual_cost?.toLocaleString() || 0}</p><p className="text-xs text-gray-500">التكلفة الفعلية</p></div>
                    </div>
                  </div>
                  <div className="bg-white rounded-xl p-4 border">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center"><Target size={20} className="text-purple-600" /></div>
                      <div><p className="text-2xl font-bold">{projectMilestones.filter(m => m.status === 'Achieved').length}/{projectMilestones.length}</p><p className="text-xs text-gray-500">المعالم المحققة</p></div>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white rounded-xl p-4 border">
                    <h4 className="font-bold text-gray-800 mb-2">وصف المشروع</h4>
                    <p className="text-sm text-gray-600">{showDetail.description || 'لا يوجد وصف'}</p>
                  </div>
                  <div className="bg-white rounded-xl p-4 border">
                    <h4 className="font-bold text-gray-800 mb-2">معلومات إضافية</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between"><span className="text-gray-500">تاريخ البدء:</span><span>{showDetail.expected_start || '-'}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">تاريخ الانتهاء:</span><span>{showDetail.expected_end || '-'}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">الميزانية:</span><span>{showDetail.budget?.toLocaleString() || 0} ر.س</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">التكلفة التقديرية:</span><span>{showDetail.estimated_cost?.toLocaleString() || 0} ر.س</span></div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'tasks' && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-bold">المهام ({projectTasks.length})</h4>
                  <button onClick={() => navigate('/tasks')} className="text-sm text-blue-600 hover:underline">عرض الكل</button>
                </div>
                <div className="bg-white rounded-xl border divide-y">
                  {projectTasks.map((task) => (
                    <div key={task.id} className="p-3 flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">{task.subject}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${task.status === 'Completed' ? 'bg-green-100 text-green-700' : task.status === 'Working' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}>{task.status}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${PRIORITY_OPTIONS.find(p => p.value === task.priority)?.color || 'bg-gray-100'}`}>{PRIORITY_OPTIONS.find(p => p.value === task.priority)?.label || task.priority}</span>
                        </div>
                      </div>
                      <div className="text-xs text-gray-400">{task.assignee_name || 'غير معين'}</div>
                    </div>
                  ))}
                  {projectTasks.length === 0 && <p className="text-gray-400 text-center py-6">لا توجد مهام</p>}
                </div>
              </div>
            )}

            {activeTab === 'milestones' && (
              <div>
                <h4 className="font-bold mb-3">المعالم ({projectMilestones.length})</h4>
                <div className="space-y-2">
                  {projectMilestones.map((m) => (
                    <div key={m.id} className={`p-3 rounded-lg border ${m.is_overdue ? 'bg-red-50 border-red-200' : 'bg-white'}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Target size={16} className={m.status === 'Achieved' ? 'text-green-500' : m.is_overdue ? 'text-red-500' : 'text-gray-400'} />
                          <span className="font-medium text-sm">{m.name}</span>
                        </div>
                        <span className="text-xs text-gray-400">{m.due_date}</span>
                      </div>
                      {m.description && <p className="text-xs text-gray-500 mt-1">{m.description}</p>}
                    </div>
                  ))}
                  {projectMilestones.length === 0 && <p className="text-gray-400 text-center py-6">لا توجد معالم</p>}
                </div>
              </div>
            )}

            {activeTab === 'risks' && (
              <div>
                <h4 className="font-bold mb-3">المخاطر ({projectRisks.length})</h4>
                <div className="space-y-2">
                  {projectRisks.map((r) => (
                    <div key={r.id} className="bg-white p-3 rounded-lg border">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{r.title}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${r.risk_level === 'Critical' ? 'bg-red-100 text-red-700' : r.risk_level === 'High' ? 'bg-orange-100 text-orange-700' : 'bg-yellow-100 text-yellow-700'}`}>{r.risk_level}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">احتمالية: {r.probability}/5 | تأثير: {r.impact}/5</p>
                    </div>
                  ))}
                  {projectRisks.length === 0 && <p className="text-gray-400 text-center py-6">لا توجد مخاطر مسجلة</p>}
                </div>
              </div>
            )}

            {activeTab === 'issues' && (
              <div>
                <h4 className="font-bold mb-3">المشاكل ({projectIssues.length})</h4>
                <div className="space-y-2">
                  {projectIssues.map((i) => (
                    <div key={i.id} className="bg-white p-3 rounded-lg border">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{i.title}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${i.severity === 'Critical' ? 'bg-red-100 text-red-700' : i.severity === 'High' ? 'bg-orange-100 text-orange-700' : 'bg-yellow-100 text-yellow-700'}`}>{i.severity}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{i.description}</p>
                    </div>
                  ))}
                  {projectIssues.length === 0 && <p className="text-gray-400 text-center py-6">لا توجد مشاكل مسجلة</p>}
                </div>
              </div>
            )}

            {activeTab === 'stakeholders' && (
              <div>
                <h4 className="font-bold mb-3">أصحاب المصلحة ({projectStakeholders.length})</h4>
                <div className="grid grid-cols-2 gap-3">
                  {projectStakeholders.map((s) => (
                    <div key={s.id} className="bg-white p-3 rounded-lg border">
                      <p className="font-medium text-sm">{s.name}</p>
                      <p className="text-xs text-gray-500">{s.role} | {s.organization}</p>
                      <div className="flex gap-2 mt-2">
                        <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">تأثير: {s.influence}</span>
                        <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">اهتمام: {s.interest}</span>
                      </div>
                    </div>
                  ))}
                  {projectStakeholders.length === 0 && <p className="text-gray-400 text-center py-6 col-span-2">لا يوجد أصحاب مصلحة</p>}
                </div>
              </div>
            )}

            {activeTab === 'changes' && (
              <div>
                <h4 className="font-bold mb-3">طلبات التغيير ({projectChangeRequests.length})</h4>
                <div className="space-y-2">
                  {projectChangeRequests.map((cr) => (
                    <div key={cr.id} className="bg-white p-3 rounded-lg border">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{cr.title}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${cr.status === 'Approved' ? 'bg-green-100 text-green-700' : cr.status === 'Rejected' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>{cr.status}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{cr.description}</p>
                    </div>
                  ))}
                  {projectChangeRequests.length === 0 && <p className="text-gray-400 text-center py-6">لا توجد طلبات تغيير</p>}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Projects List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.results?.map((project) => {
          const status = STATUS_OPTIONS.find((s) => s.value === project.status)
          const priority = PRIORITY_OPTIONS.find((p) => p.value === project.priority)
          return (
            <div key={project.id} className="bg-white rounded-xl p-5 border hover:shadow-md transition-shadow cursor-pointer" onClick={() => openDetail(project)}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-bold text-gray-800">{project.project_name}</h3>
                  <p className="text-xs text-gray-400">{project.project_code}</p>
                </div>
                <div className="flex gap-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${status?.color || 'bg-gray-100'}`}>{status?.label || project.status}</span>
                </div>
              </div>
              <p className="text-sm text-gray-500 mb-3 line-clamp-2">{project.description || 'لا يوجد وصف'}</p>
              <div className="flex items-center justify-between text-xs text-gray-400 mb-3">
                <span className="flex items-center gap-1"><Calendar size={12} /> {project.expected_start || '-'} إلى {project.expected_end || '-'}</span>
                <span className="flex items-center gap-1"><DollarSign size={12} /> {project.budget?.toLocaleString() || 0} ر.س</span>
              </div>
              <div className="flex items-center justify-between">
                <span className={`text-xs px-2 py-0.5 rounded-full ${priority?.color || 'bg-gray-100'}`}>{priority?.label || project.priority}</span>
                <div className="flex gap-1">
                  <button onClick={(e) => { e.stopPropagation(); handleEdit(project) }} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"><Edit2 size={14} /></button>
                  <button onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(project.id) }} className="p-1.5 text-red-600 hover:bg-red-50 rounded"><Trash2 size={14} /></button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
      {data?.results?.length === 0 && (
        <div className="text-center py-20">
          <FolderKanban size={48} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-400">لا توجد مشاريع</p>
        </div>
      )}
    </div>
  )
}
