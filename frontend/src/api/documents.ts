import api from './client';

export interface Document {
  id: string;
  title: string;
  source: string;
  module_id: string | null;
}

export const getDocuments = () => api.get<{ data: Document[] }>('/documents');
export const uploadDocument = (title: string, file: File) => {
  const form = new FormData();
  form.append('title', title);
  form.append('file', file);
  return api.post<{ data: Document }>('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const deleteDocument = (id: string) => api.delete(`/documents/${id}`);
