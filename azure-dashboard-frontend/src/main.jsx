import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import App from './App.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import { AuthProvider } from './contexts/AuthContext.jsx';
import './index.css';
import './App.css';

// Importar páginas
import LoginPage from './pages/LoginPage.jsx';
import DashboardHome from './pages/DashboardHomeFixed.jsx';
import UserProfile from './pages/UserProfile.jsx';
import HelpPage from './pages/HelpPage.jsx';
import AzureConfigPage from './pages/AzureConfigPage.jsx';
import MicrosoftConfigPage from './pages/MicrosoftConfigPage.jsx';
import AzureFunctionsConfigPage from './pages/AzureFunctionsConfigPage.jsx';
import AzureDebugPage from './pages/AzureDebugPage.jsx';
import AuthTestPage from './pages/AuthTestPage.jsx';
import AzureCredentialsDebugPage from './pages/AzureCredentialsDebugPage.jsx';
import AdvancedSchedulesPage from './pages/AdvancedSchedulesPage.jsx';
import MonitoringPage from './pages/MonitoringPageFixed.jsx';
import ReportsPage from './pages/ReportsPage.jsx';
import BudgetPageAdvanced from './pages/BudgetPageAdvanced.jsx';
import SchedulesUnifiedPage from './pages/SchedulesUnifiedPage.jsx';
import ActionsPage from './pages/ActionsPage.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route element={<ProtectedRoute><App /></ProtectedRoute>}>
            <Route path="/dashboard" element={<DashboardHome />} />
            <Route path="/profile" element={<UserProfile />} />
            <Route path="/help" element={<HelpPage />} />
            <Route path="/azure-config" element={<AzureConfigPage />} />
            <Route path="/microsoft-config" element={<MicrosoftConfigPage />} />
            <Route path="/azure-functions-config" element={<AzureFunctionsConfigPage />} />
            <Route path="/azure-debug" element={<AzureDebugPage />} />
            <Route path="/auth-test" element={<AuthTestPage />} />
            <Route path="/azure-credentials-debug" element={<AzureCredentialsDebugPage />} />
            <Route path="/advanced-schedules" element={<AdvancedSchedulesPage />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/budget" element={<BudgetPageAdvanced />} />
            <Route path="/schedules" element={<SchedulesUnifiedPage />} />
            <Route path="/schedules-unified" element={<SchedulesUnifiedPage />} />
            <Route path="/actions" element={<ActionsPage />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  </React.StrictMode>
);

