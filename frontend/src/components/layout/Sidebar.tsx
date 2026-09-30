import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/auth';

interface NavItem {
  to: string;
  label: string;
}

const employeeNav: NavItem[] = [
  { to: '/modules', label: 'Модули' },
  { to: '/testing', label: 'Тестирование' },
  { to: '/mentor', label: 'Наставник' },
  { to: '/phishing', label: 'Фишинг' },
  { to: '/social-eng', label: 'Соц. инженерия' },
  { to: '/profile', label: 'Мой профиль' },
];

const adminNav: NavItem[] = [
  { to: '/admin/modules', label: 'Модули' },
  { to: '/admin/users', label: 'Пользователи' },
  { to: '/admin/documents', label: 'База знаний' },
  { to: '/admin/phishing', label: 'Фишинг' },
  { to: '/admin/analytics', label: 'Аналитика' },
  { to: '/admin/audit', label: 'Аудит' },
  { to: '/admin/schedules', label: 'Расписания' },
  { to: '/admin/advisor', label: 'AI-советник' },
  { to: '/admin/mfa', label: '2FA' },
  { to: '/admin/settings', label: 'Настройки' },
];

const managerNav: NavItem[] = [
  { to: '/admin/analytics', label: 'Аналитика' },
];

const specialistNav: NavItem[] = [
  { to: '/admin/phishing', label: 'Фишинг' },
  { to: '/admin/documents', label: 'База знаний' },
  { to: '/admin/analytics', label: 'Аналитика' },
  { to: '/admin/audit', label: 'Аудит' },
  { to: '/admin/advisor', label: 'AI-советник' },
  { to: '/admin/mfa', label: '2FA' },
];

function navByRole(role: string): NavItem[] {
  if (role === 'admin') return adminNav;
  if (role === 'manager') return managerNav;
  if (role === 'security_specialist') return specialistNav;
  return employeeNav;
}

export default function Sidebar() {
  const user = useAuthStore(s => s.user);
  const logout = useAuthStore(s => s.logout);
  const navigate = useNavigate();
  const nav = navByRole(user?.role ?? 'employee');

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <aside className="w-56 bg-gray-900 min-h-screen flex flex-col border-r border-gray-800">
      <div className="px-5 py-5 border-b border-gray-800">
        <span className="text-white font-semibold text-sm">VKR ИБ</span>
      </div>
      <nav className="flex-1 py-4">
        {nav.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block px-5 py-2 text-sm transition-colors ${
                isActive ? 'text-white bg-gray-800' : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-4 border-t border-gray-800">
        <p className="text-xs text-gray-500 mb-1 truncate">{user?.full_name}</p>
        <p className="text-xs text-gray-600 mb-3">{user?.role}</p>
        <button
          onClick={handleLogout}
          className="text-xs text-gray-400 hover:text-white transition-colors"
        >
          Выйти
        </button>
      </div>
    </aside>
  );
}
