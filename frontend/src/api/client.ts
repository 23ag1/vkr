import axios from 'axios';

// Use a relative path so requests go through the Vite dev proxy (/api → backend).
// This avoids hardcoding a backend port that may collide with other services.
const getApiBaseURL = () => '/api';

const api = axios.create({
  baseURL: getApiBaseURL(),
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  res => res,
  async error => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { data } = await axios.post(`${getApiBaseURL()}/auth/refresh`, null, {
            headers: { Authorization: `Bearer ${refresh}` },
          });
          const tokens = data.data;
          localStorage.setItem('access_token', tokens.access_token);
          localStorage.setItem('refresh_token', tokens.refresh_token);
          error.config.headers.Authorization = `Bearer ${tokens.access_token}`;
          return api(error.config);
        } catch {
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
