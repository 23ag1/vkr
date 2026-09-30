import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { useAuthStore } from '../../store/auth';
import DiagnosticOnboarding from '../DiagnosticOnboarding';
import IncidentModal from '../IncidentModal';
import Sidebar from './Sidebar';

export default function Layout() {
  const user = useAuthStore(s => s.user);
  const [dismissed, setDismissed] = useState(false);
  const [incidentOpen, setIncidentOpen] = useState(false);

  const needsDiagnostic =
    !dismissed &&
    user?.role === 'employee' &&
    user?.diagnostic_completed_at === null;

  return (
    <div className="flex min-h-screen bg-gray-950 text-white">
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
      <button
        onClick={() => setIncidentOpen(true)}
        className="fixed bottom-6 right-6 flex items-center gap-2 px-4 py-2 bg-red-800 hover:bg-red-700 border border-red-600 rounded-full text-xs font-medium text-white shadow-lg transition-colors z-40"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
        Инцидент
      </button>
      {needsDiagnostic && <DiagnosticOnboarding onComplete={() => setDismissed(true)} />}
      {incidentOpen && <IncidentModal onClose={() => setIncidentOpen(false)} />}
    </div>
  );
}
