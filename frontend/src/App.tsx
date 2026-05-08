import { Routes, Route, Navigate } from 'react-router-dom';
import AdminLayout from './layouts/AdminLayout';
import Dashboard from './pages/Dashboard';
import KnowledgeManage from './pages/KnowledgeManage';
import QuoteManage from './pages/QuoteManage';
import TicketManage from './pages/TicketManage';
import Analytics from './pages/Analytics';
import LoginPage from './pages/Login';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token');
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="knowledge" element={<KnowledgeManage />} />
        <Route path="quotes" element={<QuoteManage />} />
        <Route path="tickets" element={<TicketManage />} />
        <Route path="analytics" element={<Analytics />} />
      </Route>
    </Routes>
  );
}
