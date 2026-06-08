import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

// user shape: { email, username, is_staff, is_manager } — no token, cookie handles auth
export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = sessionStorage.getItem('fleet_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  function login(userData) {
    sessionStorage.setItem('fleet_user', JSON.stringify(userData))
    setUser(userData)
  }

  function logout() {
    sessionStorage.removeItem('fleet_user')
    setUser(null)
  }

  const isManager = user?.is_manager === true || user?.is_staff === true
  const isDriver  = !isManager && user !== null

  return (
    <AuthContext.Provider value={{ user, login, logout, isManager, isDriver }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
