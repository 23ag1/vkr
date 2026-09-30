import { useEffect } from 'react';
import { useNavigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../store/auth';
import { getMe } from '../../api/auth';
import type { UserRole } from '../../api/users';

interface Props {
  roles?: UserRole[];
}

export default function ProtectedRoute({ roles }: Props) {
  const navigate = useNavigate();
  const { user, setUser } = useAuthStore();
  const token = localStorage.getItem('access_token');

  useEffect(() => {
    if (!token) { navigate('/login', { replace: true }); return; }
    if (user) return;
    getMe()
      .then(({ data }) => setUser(data.data))
      .catch(() => { navigate('/login', { replace: true }); });
  }, [token]); // re-run when token changes (null after logout)

  if (!token || !user) return null;
  if (roles && !roles.includes(user.role as UserRole)) {
    return <div className="text-red-400 p-4">Доступ запрещён</div>;
  }
  return <Outlet />;
}
