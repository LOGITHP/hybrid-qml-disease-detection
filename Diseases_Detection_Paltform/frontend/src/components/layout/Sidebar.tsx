import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  Sliders,
  Filter,
  Layers,
  Cpu,
  Zap,
  Activity,
  BarChart3,
  Lightbulb,
  FlaskConical,
  FileText,
  Archive,
  Settings,
  LogOut,
  Atom,
  RotateCcw
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const navigationGroups = [
  {
    title: 'OVERVIEW',
    items: [{ name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard }],
  },
  {
    title: 'DATA',
    items: [
      { name: 'Datasets', path: '/datasets', icon: Database },
      { name: 'Preprocessing', path: '/preprocessing', icon: Sliders },
      { name: 'Features', path: '/features', icon: Filter },
    ],
  },
  {
    title: 'MODELS',
    items: [
      { name: 'Models Zoo', path: '/models', icon: Layers },
      { name: 'Training', path: '/training', icon: Cpu },
      { name: 'Quantum', path: '/quantum', icon: Zap },
      { name: 'Feedback & Retrain', path: '/feedback', icon: RotateCcw },
    ],
  },
  {
    title: 'RESULTS',
    items: [
      { name: 'Predictions', path: '/predictions', icon: Activity },
      { name: 'Evaluation', path: '/evaluation', icon: BarChart3 },
      { name: 'Explainability', path: '/explainability/demo', icon: Lightbulb },
    ],
  },
  {
    title: 'RESEARCH',
    items: [
      { name: 'Experiments', path: '/experiments', icon: FlaskConical },
      { name: 'Reports', path: '/reports', icon: FileText },
      { name: 'Artifacts', path: '/artifacts', icon: Archive },
    ],
  },
  {
    title: 'SYSTEM',
    items: [{ name: 'Settings', path: '/settings', icon: Settings }],
  },
];

export const Sidebar: React.FC<{ onCloseMobile?: () => void }> = ({ onCloseMobile }) => {
  const { user, logout } = useAuth();

  return (
    <aside className="w-64 bg-white text-slate-600 flex flex-col h-full border-r border-slate-200 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-200 bg-slate-50/40">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-tr from-brand-700 to-quantum-600 rounded-lg text-white shadow-md">
            <Atom className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <span className="font-bold text-slate-900 tracking-wide text-sm block">HybridQML</span>
            <span className="text-[10px] text-slate-500 font-medium tracking-tight block">
              Disease Screening Platform
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        {navigationGroups.map((group) => (
          <div key={group.title}>
            <h3 className="px-3 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
              {group.title}
            </h3>
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      onClick={onCloseMobile}
                      className={({ isActive }) =>
                        `flex items-center px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                          isActive
                            ? 'bg-brand-100 text-brand-900 shadow-sm font-semibold'
                            : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                        }`
                      }
                    >
                      <Icon className="w-4 h-4 mr-3 flex-shrink-0" />
                      <span>{item.name}</span>
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>

      {/* User Session Footer */}
      <div className="p-4 border-t border-slate-200 bg-slate-50/60 flex items-center justify-between">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="w-8 h-8 rounded-full bg-brand-700 text-white flex items-center justify-center font-bold text-xs flex-shrink-0">
            {user?.full_name ? user.full_name.charAt(0) : 'U'}
          </div>
          <div className="truncate">
            <p className="text-xs font-medium text-slate-900 truncate">{user?.full_name || 'Clinician'}</p>
            <p className="text-[10px] text-slate-500 truncate capitalize">{user?.role || 'Clinician'}</p>
          </div>
        </div>
        <button
          onClick={logout}
          title="Sign out"
          className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};
