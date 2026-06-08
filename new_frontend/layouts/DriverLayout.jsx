import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { ClipboardList, PlusCircle, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useLang } from '../context/LangContext'
import LangToggle from '../components/LangToggle'
import api from '../hooks/useApi'

const TABS = [
  { to: '/driver/trips', key: 'my_trips', Icon: ClipboardList },
  { to: '/driver/log',   key: 'log_trip', Icon: PlusCircle },
]

export default function DriverLayout() {
  const { user, logout } = useAuth()
  const { t } = useLang()
  const navigate = useNavigate()

  async function handleLogout() {
    try { await api.post('/logout/') } catch {}
    logout()
    navigate('/login')
  }

  return (
    <div className="flex flex-col min-h-screen bg-slate">

      {/* Top bar — white with amber dot brand */}
      <header className="bg-white border-b border-slate-border px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber inline-block" />
          <span className="font-display text-sm font-semibold tracking-widest text-ink uppercase">
            Fleet Logger
          </span>
        </div>
        <div className="flex items-center gap-2">
          <LangToggle />
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-ink-400 hover:text-ink
                       text-xs font-body transition-colors px-2 py-1"
          >
            <LogOut size={13} strokeWidth={1.5} />
            {t.logout}
          </button>
        </div>
      </header>

      <div className="bg-slate-soft border-b border-slate-border px-4 py-1.5">
        <span className="font-body text-xs text-ink-300 truncate">{user?.email}</span>
      </div>

      <main className="flex-1 overflow-auto pb-20">
        <div className="page-enter p-4 max-w-xl mx-auto">
          <Outlet />
        </div>
      </main>

      {/* Bottom tab bar — amber active */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-border flex">
        {TABS.map(({ to, key, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center gap-1 py-3 text-xs font-body transition-colors ${
                isActive ? 'text-amber font-medium' : 'text-ink-400'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={18} strokeWidth={isActive ? 2 : 1.5} />
                {t[key]}
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
