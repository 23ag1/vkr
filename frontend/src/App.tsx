import { Routes, Route, Navigate } from 'react-router-dom';
import type { UserRole } from './api/users';
import LoginPage from './pages/auth/LoginPage';
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/layout/ProtectedRoute';

import ModulesPage from './pages/employee/ModulesPage';
import ModuleViewPage from './pages/employee/ModuleViewPage';
import TestingPage from './pages/employee/TestingPage';
import MentorPage from './pages/employee/MentorPage';
import ProfilePage from './pages/employee/ProfilePage';
import PhishingInboxPage from './pages/employee/PhishingInboxPage';
import SocialEngPage from './pages/employee/SocialEngPage';

import AdminModulesPage from './pages/admin/AdminModulesPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminDocumentsPage from './pages/admin/AdminDocumentsPage';
import AdminPhishingPage from './pages/admin/AdminPhishingPage';
import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage';
import AdminSettingsPage from './pages/admin/AdminSettingsPage';
import AdminAuditPage from './pages/admin/AdminAuditPage';
import AdminLlmPage from './pages/admin/AdminLlmPage';
import AdminSchedulesPage from './pages/admin/AdminSchedulesPage';
import MfaSetupPage from './pages/admin/MfaSetupPage';

const ADMIN_ROLES: UserRole[] = ['admin', 'manager', 'security_specialist'];

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          {/* Employee */}
          <Route path="/modules" element={<ModulesPage />} />
          <Route path="/modules/:id" element={<ModuleViewPage />} />
          <Route path="/testing" element={<TestingPage />} />
          <Route path="/mentor" element={<MentorPage />} />
          <Route path="/phishing" element={<PhishingInboxPage />} />
          <Route path="/social-eng" element={<SocialEngPage />} />
          <Route path="/profile" element={<ProfilePage />} />

          {/* Admin / Manager / Specialist */}
          <Route element={<ProtectedRoute roles={ADMIN_ROLES} />}>
            <Route path="/admin/modules" element={<AdminModulesPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/documents" element={<AdminDocumentsPage />} />
            <Route path="/admin/phishing" element={<AdminPhishingPage />} />
            <Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
            <Route path="/admin/settings" element={<AdminSettingsPage />} />
            <Route path="/admin/audit" element={<AdminAuditPage />} />
            <Route path="/admin/advisor" element={<AdminLlmPage />} />
            <Route path="/admin/schedules" element={<AdminSchedulesPage />} />
            <Route path="/admin/mfa" element={<MfaSetupPage />} />
          </Route>

          <Route path="/" element={<Navigate to="/modules" replace />} />
          <Route path="*" element={<Navigate to="/modules" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}
