import { useState } from 'react';
import { mfaSetup, mfaVerify } from '../../api/auth';

type Step = 'idle' | 'setup' | 'done';

export default function MfaSetupPage() {
  const [step, setStep] = useState<Step>('idle');
  const [secret, setSecret] = useState('');
  const [uri, setUri] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSetup() {
    setLoading(true);
    setError('');
    try {
      const { data } = await mfaSetup();
      setSecret(data.data.secret);
      setUri(data.data.otpauth_uri);
      setStep('setup');
    } catch {
      setError('Ошибка при генерации секрета');
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await mfaVerify(code);
      setStep('done');
    } catch {
      setError('Неверный код, попробуйте ещё раз');
      setCode('');
    } finally {
      setLoading(false);
    }
  }

  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(uri)}`;

  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-semibold mb-2">Двухфакторная аутентификация</h1>
      <p className="text-sm text-gray-400 mb-6">TOTP (Google Authenticator, Authy, и др.)</p>

      {step === 'idle' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <p className="text-sm text-gray-300 mb-4">
            Включите 2FA для вашего аккаунта. После настройки каждый вход будет
            требовать одноразовый код из приложения-аутентификатора.
          </p>
          {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
          <button
            onClick={handleSetup}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
          >
            {loading ? 'Загрузка...' : 'Настроить 2FA'}
          </button>
        </div>
      )}

      {step === 'setup' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5">
          <div>
            <p className="text-sm text-gray-300 mb-3">
              1. Отсканируйте QR-код в приложении-аутентификаторе
            </p>
            <img src={qrUrl} alt="TOTP QR code" className="rounded-lg w-48 h-48 bg-white p-1" />
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Или введите ключ вручную:</p>
            <code className="text-xs text-green-400 bg-gray-800 px-3 py-1.5 rounded-lg block break-all">
              {secret}
            </code>
          </div>
          <form onSubmit={handleVerify} className="space-y-3">
            <div>
              <p className="text-sm text-gray-300 mb-2">
                2. Введите код из приложения для подтверждения
              </p>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm text-center tracking-widest focus:outline-none focus:border-blue-500"
                placeholder="000000"
                autoFocus
              />
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading || code.length !== 6}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
            >
              {loading ? 'Проверка...' : 'Активировать'}
            </button>
          </form>
        </div>
      )}

      {step === 'done' && (
        <div className="bg-gray-900 border border-green-800 rounded-xl p-6">
          <p className="text-green-400 font-medium mb-2">2FA успешно активирована</p>
          <p className="text-sm text-gray-400">
            При следующем входе вам потребуется ввести код из приложения-аутентификатора.
          </p>
        </div>
      )}
    </div>
  );
}
