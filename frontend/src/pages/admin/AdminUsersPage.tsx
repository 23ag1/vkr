import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getUsers, createUser, deactivateUser, User, UserRole } from '../../api/users';
import { FormInput, inputCls } from '../../components/ui/FormInput';
import { ErrorState } from '../../components/ui/ErrorState';

interface FormState {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
}

const EMPTY: FormState = { email: '', password: '', full_name: '', role: 'employee' };

export default function AdminUsersPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [showForm, setShowForm] = useState(false);

  const { data: res, isError, refetch } = useQuery({ queryKey: ['users'], queryFn: getUsers });
  const users = res?.data.data ?? [];

  const createMut = useMutation({
    mutationFn: () => createUser(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] });
      setForm(EMPTY);
      setShowForm(false);
    },
  });

  const deactivateMut = useMutation({
    mutationFn: (id: string) => deactivateUser(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });

  function field(key: keyof FormState) {
    return {
      value: form[key],
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
        setForm(prev => ({ ...prev, [key]: e.target.value as UserRole })),
    };
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">Пользователи</h1>
        <button
          onClick={() => setShowForm(s => !s)}
          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
        >
          {showForm ? 'Отмена' : 'Создать'}
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
          <h2 className="font-medium mb-4 text-sm">Новый пользователь</h2>
          <div className="grid gap-3">
            <FormInput label="ФИО" {...field('full_name')} />
            <FormInput label="Email" type="email" {...field('email')} />
            <FormInput label="Пароль" type="password" {...field('password')} />
            <div>
              <label className="text-xs text-gray-400 block mb-1">Роль</label>
              <select value={form.role} onChange={e => setForm(prev => ({ ...prev, role: e.target.value as UserRole }))} className={inputCls}>
                <option value="employee">Сотрудник</option>
                <option value="admin">Администратор</option>
                <option value="manager">Менеджер</option>
                <option value="security_specialist">Специалист ИБ</option>
              </select>
            </div>
          </div>
          <button
            onClick={() => createMut.mutate()}
            disabled={!form.email || !form.password || createMut.isPending}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
          >
            {createMut.isPending ? 'Создание...' : 'Создать'}
          </button>
        </div>
      )}

      <div className="grid gap-2">
        {isError && <ErrorState onRetry={() => refetch()} message="Не удалось загрузить пользователей" />}
        {!isError && users.map(u => (
          <UserRow key={u.id} user={u} onDeactivate={() => deactivateMut.mutate(u.id)} />
        ))}
        {!isError && users.length === 0 && <p className="text-gray-500 text-sm">Нет пользователей</p>}
      </div>
    </div>
  );
}

function UserRow({ user, onDeactivate }: { user: User; onDeactivate: () => void }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between">
      <div>
        <p className="text-sm font-medium">{user.full_name}</p>
        <p className="text-xs text-gray-400 mt-0.5">{user.email} · {user.role}</p>
      </div>
      <div className="flex items-center gap-3">
        <span className={`text-xs px-2 py-0.5 rounded-full ${user.is_active ? 'text-green-400 bg-green-900/30' : 'text-gray-500 bg-gray-800'}`}>
          {user.is_active ? 'Активен' : 'Неактивен'}
        </span>
        {user.is_active && (
          <button onClick={onDeactivate} className="text-xs text-red-400 hover:text-red-300 transition-colors">
            Деактивировать
          </button>
        )}
      </div>
    </div>
  );
}
