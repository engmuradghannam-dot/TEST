import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { teams, employees } from '../lib/api'
import { Plus, UsersRound } from 'lucide-react'

export default function Teams() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['teams'], queryFn: () => teams.list() })
  const { data: empData } = useQuery({ queryKey: ['employees'], queryFn: () => employees.list() })
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => teams.create(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['teams'] }); setName('') },
    onError: (err) => setError('تعذر إنشاء الفريق. تأكد من البيانات.'),
  })

  const employeeName = (id) => {
    const e = empData?.results?.find((emp) => emp.id === id)
    return e ? `${e.first_name} ${e.last_name}` : id
  }

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">الفرق</h2>
          <p className="text-gray-500 text-sm">أعضاء الفريق يشوفون كل المهام المسندة للفريق تلقائيًا</p>
        </div>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate({ name, company: empData?.results?.[0]?.company }) }}
        className="flex gap-2 mb-6">
        <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="اسم الفريق الجديد"
          className="border rounded-lg px-3 py-2 text-sm flex-1 max-w-xs" />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> إنشاء فريق
        </button>
      </form>
      {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-4 border border-red-200">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data?.results?.map((team) => (
          <div key={team.id} className="bg-white rounded-xl shadow-sm border p-5">
            <div className="flex items-center gap-2 mb-3">
              <UsersRound className="text-blue-600" size={20} />
              <h3 className="font-bold text-gray-800">{team.name}</h3>
            </div>
            <p className="text-sm text-gray-500 mb-2">الأعضاء:</p>
            <div className="flex flex-wrap gap-2">
              {team.members?.length
                ? team.members.map((m) => (
                    <span key={m} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full">{employeeName(m)}</span>
                  ))
                : <span className="text-xs text-gray-400">لا يوجد أعضاء بعد</span>}
            </div>
          </div>
        ))}
        {!data?.results?.length && <p className="text-gray-400 col-span-2 text-center py-8">لا يوجد فرق بعد</p>}
      </div>
    </div>
  )
}
