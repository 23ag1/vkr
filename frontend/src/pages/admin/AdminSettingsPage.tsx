import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings } from '../../api/settings';
import { inputCls } from '../../components/ui/FormInput';

type Tab = 'prompts' | 'model';

const KNOWN_MODELS = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'];

export default function AdminSettingsPage() {
  const [tab, setTab] = useState<Tab>('prompts');

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Настройки</h1>
      <div className="flex gap-1 mb-6 border-b border-gray-800">
        {(['prompts', 'model'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm transition-colors border-b-2 -mb-px ${
              tab === t ? 'border-blue-500 text-white' : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            {t === 'prompts' ? 'Промпты GPT' : 'Модель GPT'}
          </button>
        ))}
      </div>
      {tab === 'prompts' ? <PromptsTab /> : <ModelTab />}
    </div>
  );
}

function PromptsTab() {
  const qc = useQueryClient();
  const { data: res, isLoading } = useQuery({ queryKey: ['app-settings'], queryFn: getSettings });
  const [qPrompt, setQPrompt] = useState('');
  const [ePrompt, setEPrompt] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (res?.data.data) {
      setQPrompt(res.data.data.question_prompt);
      setEPrompt(res.data.data.explanation_prompt);
    }
  }, [res]);

  const mut = useMutation({
    mutationFn: () => updateSettings({ question_prompt: qPrompt, explanation_prompt: ePrompt }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['app-settings'] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  if (isLoading) return <p className="text-gray-500 text-sm">Загрузка...</p>;

  return (
    <div className="grid gap-5 max-w-3xl">
      <div>
        <label className="text-xs text-gray-400 block mb-1">
          Системный промпт генерации вопросов
          <span className="text-gray-600 ml-2">(используется при каждом запросе к GPT)</span>
        </label>
        <textarea
          value={qPrompt}
          onChange={e => setQPrompt(e.target.value)}
          rows={14}
          className={inputCls}
        />
      </div>
      <div>
        <label className="text-xs text-gray-400 block mb-1">
          Системный промпт объяснений
          <span className="text-gray-600 ml-2">(при неправильном ответе)</span>
        </label>
        <textarea
          value={ePrompt}
          onChange={e => setEPrompt(e.target.value)}
          rows={5}
          className={inputCls}
        />
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={() => mut.mutate()}
          disabled={mut.isPending}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
        >
          {mut.isPending ? 'Сохранение...' : 'Сохранить'}
        </button>
        {saved && <span className="text-xs text-green-400">Сохранено</span>}
      </div>
    </div>
  );
}

function ModelTab() {
  const qc = useQueryClient();
  const { data: res, isLoading } = useQuery({ queryKey: ['app-settings'], queryFn: getSettings });
  const [model, setModel] = useState('');
  const [custom, setCustom] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (res?.data.data) {
      const m = res.data.data.model;
      if (KNOWN_MODELS.includes(m) || m === '') {
        setModel(m);
      } else {
        setModel('custom');
        setCustom(m);
      }
    }
  }, [res]);

  const mut = useMutation({
    mutationFn: () => {
      const effective = model === 'custom' ? custom : model;
      return updateSettings({ model: effective });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['app-settings'] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  if (isLoading) return <p className="text-gray-500 text-sm">Загрузка...</p>;

  const effectiveModel = model === 'custom' ? custom : model;

  return (
    <div className="max-w-md">
      <p className="text-sm text-gray-400 mb-4">
        Пустое значение означает использование модели из переменной окружения <code className="text-gray-300 bg-gray-800 px-1 rounded">OPENAI_MODEL</code>.
      </p>
      <div className="grid gap-3 mb-4">
        {[...KNOWN_MODELS, 'custom'].map(m => (
          <label key={m} className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="model"
              value={m}
              checked={model === m}
              onChange={() => setModel(m)}
              className="accent-blue-500"
            />
            <span className="text-sm text-gray-300">{m === 'custom' ? 'Другая модель' : m}</span>
          </label>
        ))}
      </div>
      {model === 'custom' && (
        <input
          value={custom}
          onChange={e => setCustom(e.target.value)}
          placeholder="например: gpt-4o-2024-11-20"
          className={`${inputCls} mb-4`}
        />
      )}
      {effectiveModel && (
        <p className="text-xs text-gray-500 mb-4">
          Активная модель: <span className="text-gray-300">{effectiveModel}</span>
        </p>
      )}
      <div className="flex items-center gap-3">
        <button
          onClick={() => mut.mutate()}
          disabled={mut.isPending}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
        >
          {mut.isPending ? 'Сохранение...' : 'Сохранить'}
        </button>
        {saved && <span className="text-xs text-green-400">Сохранено</span>}
      </div>
    </div>
  );
}
