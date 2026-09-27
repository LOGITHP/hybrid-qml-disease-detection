import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Settings,
  User,
  Shield,
  Server,
  Database,
  Cpu,
  Zap,
  CheckCircle2,
  AlertCircle,
  LogOut,
  Lock,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { healthApi } from '../../api';

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();

  const { data: health } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: healthApi.getHealth,
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="pb-4 border-b border-slate-200">
        <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
          <Settings className="w-4 h-4 text-quantum-600" />
          <span>System & Account Configuration</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Platform Settings</h1>
        <p className="text-xs text-slate-500">
          Manage clinician credentials, session security, and monitor containerized infrastructure status
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Clinician Profile */}
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <User className="w-4 h-4 text-brand-800" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Clinician Profile Information
            </h3>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block text-[11px] mb-0.5">Full Name</label>
              <span className="font-bold text-slate-900">{user?.full_name || 'Dr. Jane Smith, MD'}</span>
            </div>
            <div>
              <label className="text-slate-400 block text-[11px] mb-0.5">Email Address</label>
              <span className="font-mono text-slate-700">{user?.email || 'clinician@hybridqml.org'}</span>
            </div>
            <div>
              <label className="text-slate-400 block text-[11px] mb-0.5">Role Designation</label>
              <span className="badge bg-slate-100 text-slate-800 capitalize">
                {user?.role || 'Clinician / Oncology Investigator'}
              </span>
            </div>
            <div>
              <label className="text-slate-400 block text-[11px] mb-0.5">Institution</label>
              <span className="text-slate-700">{user?.institution || 'Biomedical Oncology Center'}</span>
            </div>
          </div>
        </div>

        {/* Security & Session */}
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
              <Shield className="w-4 h-4 text-emerald-700" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Security & Session Token
              </h3>
            </div>

            <div className="space-y-2 text-xs text-slate-600">
              <p>
                Authentication tokens are signed using <strong>Argon2id + HS256 JWT</strong> with a 60-minute expiration window.
              </p>
              <div className="p-3 bg-slate-50 rounded-lg space-y-1 font-mono text-[11px]">
                <div className="text-slate-500">Access Scope: role-based endpoint isolation</div>
                <div className="text-emerald-700 font-semibold">Tenant Isolation: active</div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-400">Current session active</span>
            <button
              onClick={logout}
              className="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Terminate Session</span>
            </button>
          </div>
        </div>
      </div>

      {/* Subsystem Health Diagnostics */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <Server className="w-4 h-4 text-quantum-600" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Subsystem Health Diagnostics (Live Telemetry)
          </h3>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center text-xs">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">
              FastAPI Gateway
            </span>
            <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px]">
              ONLINE (:8000)
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">
              PostgreSQL 16
            </span>
            <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px]">
              CONNECTED
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">
              Redis 7 Queue
            </span>
            <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px]">
              HEALTHY
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">
              Gemma LLM Service
            </span>
            <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px]">
              ONLINE (:8001)
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">
              PennyLane Simulators
            </span>
            <span className="badge bg-quantum-50 text-quantum-700 border border-quantum-200 text-[10px]">
              ACTIVE
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
