import axios from 'axios'

// withCredentials = true tells axios to send HttpOnly cookies on every request
// No token in headers needed — browser handles the cookie automatically
const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// If server returns 401, user's session is gone — reload to login
api.interceptors.response.use(
  res => res,
  err => {
    const status = err.response?.status

    if (status === 401) {
      sessionStorage.removeItem('fleet_user')
      window.location.href = '/login'
      return Promise.reject(err)
    }

    if (status === 500) {
      // Global server error — you could show a toast here later
      console.error('Server error:', err.response?.data)
    }

    if (!err.response) {
      console.error('Network error — server unreachable')
    }

    return Promise.reject(err)
  }
)

export default api
