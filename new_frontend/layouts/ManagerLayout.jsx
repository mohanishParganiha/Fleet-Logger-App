import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Truck, Users, ClipboardList, Calculator, Settings, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useLang } from '../context/LangContext'
import LangToggle from '../components/LangToggle'
import api from '../hooks/useApi'

const NAV = [
  { to: '/manager/vehicles', key: 'vehicles',  Icon: Truck },
  { to: '/manager/drivers',  key: 'drivers',   Icon: Users },
  { to: '/manager/trips',    key: 'trips',      Icon: ClipboardList },
  { to: '/manager/bulk',     key: 'bulk_calc',  Icon: Calculator },
  { to: '/manager/users',    key: 'users',      Icon: Settings },
]

export default function ManagerLayout() {
  const { user, logout } = useAuth()
  const { t } = useLang()
  const navigate = useNavigate()

  async function handleLogout() {
    try { await api.post('/logout/') } catch {}
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen bg-slate">

      {/* Sidebar — white with border */}
      <aside className="w-56 bg-white border-r border-slate-border flex flex-col shrink-0">

        {/* Brand — amber accent strip */}
        <div className="px-5 py-5 border-b border-slate-border">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber inline-block" />
            <span className="font-display text-sm font-semibold tracking-widest text-ink uppercase">
              Fleet Logger
            </span>
          </div>
          <span className="block font-body text-xs text-ink-300 mt-1 truncate">
            {user?.email}
          </span>
        </div>

        <nav className="flex-1 px-2 py-3 space-y-0.5">
          {NAV.map(({ to, key, Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded text-sm font-body transition-colors ${
                  isActive
                    ? 'bg-amber/10 text-amber font-medium border-l-2 border-amber'
                    : 'text-ink-400 hover:bg-slate hover:text-ink'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={15} strokeWidth={isActive ? 2 : 1.5} />
                  {t[key]}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="px-2 py-3 border-t border-slate-border space-y-1">
          <LangToggle />
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded text-sm
                       font-body text-ink-400 hover:bg-slate hover:text-ink transition-colors"
          >
            <LogOut size={15} strokeWidth={1.5} />
            {t.logout}
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="page-enter p-6 max-w-6xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
