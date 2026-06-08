import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// requireManager: only is_staff or is_manager can enter
// no prop: any logged-in user can enter
export default function ProtectedRoute({ children, requireManager = false }) {
  const { user, isManager } = useAuth()

  if (!user) return <Navigate to="/login" replace />
  if (requireManager && !isManager) return <Navigate to="/driver/trips" replace />

  return children
}
