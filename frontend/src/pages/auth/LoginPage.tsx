import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, mfaComplete, getMe } from '../../api/auth';
import { useAuthStore } from '../../store/auth';

export default function LoginPage() {
  const navigate = useNavigate();
  const setUser = useAuthStore(s => s.setUser);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [mfaStep, setMfaStep] = useState(false);
  const [tempToken, setTempToken] = useState('');
  const [mfaCode, setMfaCode] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data: tokenRes } = await login(email, password);
      const tokens = tokenRes.data;
      if (tokens.mfa_required) {
        setTempToken(tokens.access_token);
        setMfaStep(true);
        return;
      }
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      const { data: meRes } = await getMe();
      setUser(meRes.data);
      navigate('/');
    } catch {
      setError('Неверный email или пароль');
    } finally {
      setLoading(false);
    }
  }

  async function handleMfa(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data: res } = await mfaComplete(tempToken, mfaCode);
      const tokens = res.data;
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      const { data: meRes } = await getMe();
      setUser(meRes.data);
      navigate('/');
    } catch {
      setError('Неверный код');
      setMfaCode('');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-full max-w-sm bg-gray-900 rounded-xl p-8 shadow-lg">
        {!mfaStep ? (
          <>
            <h1 className="text-xl font-semibold text-white mb-1">Вход в систему</h1>
            <p className="text-sm text-gray-400 mb-6">VKR — Осведомлённость об ИБ</p>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-300 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                  required
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm text-gray-300 mb-1">Пароль</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
              {error && <p className="text-red-400 text-sm">{error}</p>}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg py-2 text-sm font-medium transition-colors"
              >
                {loading ? 'Вход...' : 'Войти'}
              </button>
            </form>
          </>
        ) : (
          <>
            <h1 className="text-xl font-semibold text-white mb-1">Двухфакторная аутентификация</h1>
            <p className="text-sm text-gray-400 mb-6">Введите код из приложения-аутентификатора</p>
            <form onSubmit={handleMfa} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-300 mb-1">Код (6 цифр)</label>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={mfaCode}
                  onChange={e => setMfaCode(e.target.value.replace(/\D/g, ''))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm text-center tracking-widest focus:outline-none focus:border-blue-500"
                  autoFocus
                  required
                />
              </div>
              {error && <p className="text-red-400 text-sm">{error}</p>}
              <button
                type="submit"
                disabled={loading || mfaCode.length !== 6}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg py-2 text-sm font-medium transition-colors"
              >
                {loading ? 'Проверка...' : 'Подтвердить'}
              </button>
              <button
                type="button"
                onClick={() => { setMfaStep(false); setMfaCode(''); setError(''); }}
                className="w-full text-sm text-gray-400 hover:text-gray-200 transition-colors"
              >
                Назад
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
