import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../api';
import { useAuth } from '../context/AuthContext';
import { BarChart3 } from 'lucide-react';

const LoginPage: React.FC = () => {
  const [isSignup, setIsSignup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });
  const navigate = useNavigate();
  const { login } = useAuth();
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isSignup) {
        const res = await authAPI.register(formData.name, formData.email, formData.password);
        login(res.data.access_token);
      } else {
        const res = await authAPI.login(formData.email, formData.password);
        login(res.data.access_token);
      }
      navigate('/');
    } catch (err: any) {
  const detail = err.response?.data?.detail;

  setError(
    Array.isArray(detail)
      ? detail[0].msg
      : detail || "Authentication failed"
  );
  }};

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-blue-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-2xl p-8">
          <div className="flex items-center justify-center gap-2 mb-8">
            <BarChart3 className="w-10 h-10 text-purple-600" />
            <h1 className="text-3xl font-bold text-purple-600">AgentBench</h1>
          </div>

          <h2 className="text-2xl font-bold text-gray-800 text-center mb-2">
            {isSignup ? 'Create Account' : 'Welcome Back'}
          </h2>
          <p className="text-gray-600 text-center mb-8">
            AI Judge for Multi-Agent Systems
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignup && (
              <input
                type="text"
                placeholder="Full Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                required={isSignup}
              />
            )}
            <input
              type="email"
              placeholder="Email Address"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            />

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50"
            >
              {isSignup ? 'Sign Up' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
              <button
                onClick={() => setIsSignup(!isSignup)}
                className="text-purple-600 font-semibold hover:underline"
              >
                {isSignup ? 'Sign In' : 'Sign Up'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
