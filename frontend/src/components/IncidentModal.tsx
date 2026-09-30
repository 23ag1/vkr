import { useState } from 'react';
import { reportIncident } from '../api/incident';

interface Props {
  onClose: () => void;
}

export default function IncidentModal({ onClose }: Props) {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [guidance, setGuidance] = useState<string | null>(null);

  async function handleSubmit() {
    if (!description.trim() || loading) return;
    setLoading(true);
    try {
      const res = await reportIncident(description.trim());
      setGuidance(res.data.data.guidance);
    } catch {
      setGuidance('Произошла ошибка. Обратитесь к специалисту по ИБ напрямую.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-gray-900 border border-red-800 rounded-xl w-full max-w-lg"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <h2 className="font-semibold text-red-400">Подозрение на инцидент</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">✕</button>
        </div>

        <div className="px-6 py-4">
          {!guidance ? (
            <>
              <p className="text-sm text-gray-400 mb-3">
                Опишите, что произошло — AI-советник даст немедленные инструкции.
              </p>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Например: я перешёл по подозрительной ссылке из письма..."
                rows={4}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-red-600 resize-none mb-3"
              />
              <button
                onClick={handleSubmit}
                disabled={!description.trim() || loading}
                className="w-full py-2 bg-red-700 hover:bg-red-600 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
              >
                {loading ? 'Получение инструкций...' : 'Получить инструкции'}
              </button>
            </>
          ) : (
            <>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-sm text-gray-200 whitespace-pre-wrap leading-relaxed mb-4">
                {guidance}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => { setGuidance(null); setDescription(''); }}
                  className="flex-1 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
                >
                  Новый запрос
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
                >
                  Закрыть
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
