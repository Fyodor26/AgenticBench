import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Benchmark from './pages/Benchmark';
import Agents from './pages/Agents';
import Settings from './pages/Settings';
import Leaderboard from './pages/Leaderboard';
import Results from './pages/Results';
import LoginPage from './pages/Login';
import { AuthProvider, useAuth } from './context/AuthContext';
import './styles/globals.css';

function AppContent() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/benchmark" element={<Benchmark />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/results" element={<Results />} />
        <Route path="/results/:id" element={<Results />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
