import { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDocuments, uploadDocument, deleteDocument, Document } from '../../api/documents';
import { FormInput } from '../../components/ui/FormInput';
import { ErrorState } from '../../components/ui/ErrorState';

export default function AdminDocumentsPage() {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [title, setTitle] = useState('');

  const { data: res, isError, refetch } = useQuery({ queryKey: ['documents'], queryFn: getDocuments });
  const docs = res?.data.data ?? [];

  const uploadMut = useMutation({
    mutationFn: ({ t, f }: { t: string; f: File }) => uploadDocument(t, f),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] });
      setTitle('');
      if (fileRef.current) fileRef.current.value = '';
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteDocument(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });

  function handleUpload() {
    const file = fileRef.current?.files?.[0];
    if (!file || !title) return;
    uploadMut.mutate({ t: title, f: file });
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">База знаний</h1>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
        <h2 className="font-medium mb-4 text-sm">Загрузить документ</h2>
        <div className="grid gap-3">
          <FormInput label="Название" value={title} onChange={e => setTitle(e.target.value)} />
          <div>
            <label className="text-xs text-gray-400 block mb-1">Файл (PDF / TXT)</label>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.txt,.md"
              className="text-sm text-gray-400 file:mr-3 file:px-3 file:py-1 file:rounded file:border-0 file:bg-gray-700 file:text-white file:text-xs file:cursor-pointer"
            />
          </div>
        </div>
        <button
          onClick={handleUpload}
          disabled={!title || uploadMut.isPending}
          className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
        >
          {uploadMut.isPending ? 'Загрузка...' : 'Загрузить'}
        </button>
      </div>

      <div className="grid gap-2">
        {isError && <ErrorState onRetry={() => refetch()} message="Не удалось загрузить документы" />}
        {!isError && docs.map(d => (
          <DocRow key={d.id} doc={d} onDelete={() => deleteMut.mutate(d.id)} />
        ))}
        {!isError && docs.length === 0 && <p className="text-gray-500 text-sm">Нет документов</p>}
      </div>
    </div>
  );
}

function DocRow({ doc, onDelete }: { doc: Document; onDelete: () => void }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between">
      <div>
        <p className="text-sm font-medium">{doc.title}</p>
        <p className="text-xs text-gray-400 mt-0.5 truncate max-w-xs">{doc.source}</p>
      </div>
      <button onClick={onDelete} className="text-xs text-red-400 hover:text-red-300 transition-colors">
        Удалить
      </button>
    </div>
  );
}
