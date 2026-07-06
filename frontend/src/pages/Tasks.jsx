import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tasks } from '../lib/api'
import { CheckSquare, Users } from 'lucide-react'

const STATUS_STYLES = {
  'Open': 'bg-gray-100 text-gray-600',
  'Working': 'bg-blue-100 text-blue-700',
  'Pending Review': 'bg-yellow-100 text-yellow-700',
  'Completed': 'bg-green-100 text-green-700',
  'Cancelled': 'bg-red-100 text-red-600',
}

export default function Tasks() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['tasks'], queryFn: () => tasks.list() })

  const updateStatus = useMutation({
    mutationFn: ({ id, status }) => tasks.update(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">مهامي</h2>
        <p className="text-gray-500 text-sm">مهامك الشخصية بالإضافة لمهام فريقك — الموظفون العاديون يشوفون هذا بس، المدراء يشوفون كل مهام الشركة</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm divide-y">
        {data?.results?.map((task) => (
          <div key={task.id} className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckSquare size={18} className="text-gray-400" />
              <div>
                <p className="font-medium text-gray-800">{task.subject}</p>
                {task.team && (
                  <span className="flex items-center gap-1 text-xs text-purple-600 mt-0.5">
                    <Users size={12} /> مهمة فريق
                  </span>
                )}
              </div>
            </div>
            <select
              value={task.status}
              onChange={(e) => updateStatus.mutate({ id: task.id, status: e.target.value })}
              className={`text-xs font-medium px-2.5 py-1 rounded-full border-0 ${STATUS_STYLES[task.status] || 'bg-gray-100'}`}
            >
              <option value="Open">لم تبدأ</option>
              <option value="Working">قيد التنفيذ</option>
              <option value="Pending Review">بانتظار المراجعة</option>
              <option value="Completed">مكتملة</option>
              <option value="Cancelled">ملغاة</option>
            </select>
          </div>
        ))}
        {!data?.results?.length && <p className="text-gray-400 text-center py-8">لا يوجد مهام معينة لك حاليًا</p>}
      </div>
    </div>
  )
}
