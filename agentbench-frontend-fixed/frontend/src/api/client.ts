import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach the bearer token to every outgoing request, if we have one.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Previously a 401 (expired/invalid token) just surfaced as a raw failed
// request on whatever page triggered it - there was no global handling, so
// the app would appear "stuck"/broken until the user manually cleared
// localStorage. Clear the stale token and force back to the login screen.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      if (window.location.pathname !== '/') {
        window.location.href = '/';
      } else {
        window.dispatchEvent(new Event('auth:logout'));
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
