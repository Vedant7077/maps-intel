import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard, FolderKanban, Swords, Building2,
  Activity, Archive, BarChart3, Sparkles, Radar
} from 'lucide-react';
import ProjectSwitcher from './ProjectSwitcher';

const links = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/projects', icon: FolderKanban, label: 'Projects' },
  { to: '/rivals', icon: Swords, label: 'Rivals' },
  { to: '/my-business', icon: Building2, label: 'My Business' },
  { to: '/repository', icon: Archive, label: 'Repository' },
  { to: '/analysis', icon: BarChart3, label: 'Analysis' },
  { to: '/generator', icon: Sparkles, label: 'Generator' },
];

function SidebarLink({ to, icon: Icon, label }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
          isActive
            ? 'bg-[#6366F1]/10 text-[#6366F1] font-medium'
            : 'text-[#A1A1AA] hover:text-[#FAFAFA] hover:bg-[#1C1C1F]'
        }`
      }
    >
      <Icon size={18} />
      <span className="hidden md:inline">{label}</span>
    </NavLink>
  );
}

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* ─── Desktop Sidebar ──────────────────────────────────────── */}
      <aside className="hidden md:flex flex-col w-56 border-r border-[#27272A] bg-[#0A0A0B] p-4 gap-4 shrink-0">
        {/* Logo */}
        <div className="flex items-center gap-2 px-1 mb-1">
          <Radar size={22} className="text-[#6366F1]" />
          <span className="text-lg font-semibold text-[#FAFAFA]">MapSpy</span>
        </div>

        <ProjectSwitcher />

        <nav className="flex flex-col gap-0.5 flex-1">
          {links.map((l) => <SidebarLink key={l.to} {...l} />)}
        </nav>

        <div className="text-xs text-[#A1A1AA] px-1">v1.0 — Competitor Intel</div>
      </aside>

      {/* ─── Main Content ─────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto bg-[#0A0A0B]">
        <div className="max-w-6xl mx-auto p-4 md:p-8">
          <Outlet />
        </div>
      </main>

      {/* ─── Mobile Bottom Tab Bar ────────────────────────────────── */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-[#141416] border-t border-[#27272A] flex justify-around py-2 z-40">
        {links.slice(0, 5).map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 text-xs transition-colors ${
                isActive ? 'text-[#6366F1]' : 'text-[#A1A1AA]'
              }`
            }
          >
            <Icon size={20} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
