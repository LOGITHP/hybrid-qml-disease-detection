import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Atom, Database, LogOut, Server, Settings, Shield, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { healthApi } from '../../api';

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const { data: health, isLoading, isError } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: healthApi.getHealth,
    refetchInterval: 10000,
  });

  return <div className="space-y-6">
    <header className="border-b border-slate-200 pb-4">
      <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-brand-700"><Settings className="h-4 w-4 text-quantum-600" /><span>Account and platform</span></div>
      <h1 className="text-2xl font-bold tracking-tight text-slate-900">Platform Settings</h1>
      <p className="text-xs text-slate-500">Account details, session controls, and the integrations this deployment uses.</p>
    </header>

    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3"><User className="h-4 w-4 text-brand-800" /><h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Account Profile</h2></div>
        <dl className="space-y-3 text-xs">
          <div><dt className="text-[11px] text-slate-400">Full name</dt><dd className="font-bold text-slate-900">{user?.full_name || '—'}</dd></div>
          <div><dt className="text-[11px] text-slate-400">Email</dt><dd className="font-mono text-slate-700">{user?.email || '—'}</dd></div>
          {user?.institution && <div><dt className="text-[11px] text-slate-400">Institution</dt><dd className="text-slate-700">{user.institution}</dd></div>}
        </dl>
      </section>

      <section className="card-scientific flex flex-col justify-between space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3"><Shield className="h-4 w-4 text-emerald-700" /><h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Security and Session</h2></div>
          <p className="text-xs text-slate-600">Your session is authenticated with a signed access token. Account authorization continues to use the existing backend role and ownership checks.</p>
        </div>
        <div className="flex items-center justify-between border-t border-slate-100 pt-4"><span className="text-[11px] text-slate-400">Session controls</span><button onClick={logout} className="flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700 transition-colors hover:bg-red-100"><LogOut className="h-3.5 w-3.5" /><span>Sign out</span></button></div>
      </section>
    </div>

    <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3"><Server className="h-4 w-4 text-quantum-600" /><h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Runtime Integrations</h2></div>
      <div className="grid grid-cols-1 gap-3 text-xs sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><b className="block text-slate-800">API gateway</b><span className="mt-1 block text-slate-600">{isLoading ? 'Checking…' : isError ? 'Unavailable' : `${health?.status || 'Unknown'} · ${health?.service || 'service not reported'}`}</span></div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><b className="flex items-center gap-1.5 text-slate-800"><Database className="h-3.5 w-3.5" />Database</b><span className="mt-1 block text-slate-600">MongoDB is configured in Docker Compose. This app does not expose a separate live database probe.</span></div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><b className="block text-slate-800">Preprocessing AI Agent</b><span className="mt-1 block text-slate-600">Ollama is configured. The preprocessing flow reports whether the provider processes each plan update.</span></div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><b className="block text-slate-800">Artifact storage</b><span className="mt-1 block text-slate-600">Dataset and model APIs currently use the backend local artifact filesystem.</span></div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><b className="flex items-center gap-1.5 text-slate-800"><Atom className="h-3.5 w-3.5" />Quantum execution</b><span className="mt-1 block text-slate-600">PennyLane noiseless and noisy simulators are supported. Real quantum hardware is unavailable.</span></div>
      </div>
    </section>
  </div>;
};
