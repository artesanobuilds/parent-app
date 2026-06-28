import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Calendar, Search, MessageSquare, User, LogOut } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';

const NAV = [
  { to: '/chat', label: 'Chief of Staff', icon: MessageSquare },
  { to: '/discovery', label: 'Discover', icon: Search },
  { to: '/plan', label: 'Plan', icon: Calendar },
  { to: '/profile', label: 'Profile', icon: User },
];

export default function Layout() {
  const { userId, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex bg-canvas text-ink-primary">
      <aside className="w-60 shrink-0 border-r border-hairline bg-sober flex flex-col p-500">
        <div className="font-display text-2xl px-300 pt-300 pb-700">Plan</div>
        <nav className="flex flex-col gap-100">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-300 px-400 py-300 rounded-lg text-sm ${
                  isActive
                    ? 'bg-accent-tint text-ink-primary'
                    : 'text-ink-secondary hover:bg-elevated'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto pt-500 border-t border-hairline">
          <div className="text-ink-muted text-xs px-400 pb-300 truncate">{userId}</div>
          <button
            onClick={() => {
              logout();
              navigate('/login');
            }}
            className="flex items-center gap-300 px-400 py-300 w-full rounded-lg text-sm text-ink-secondary hover:bg-elevated"
          >
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
