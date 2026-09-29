import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Atom, Lock, Mail, ArrowRight, Sparkles, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, quickLoginDemo } = useAuth();

  const requestedPath = (location.state as {
    from?: { pathname?: string; search?: string; hash?: string };
  } | null)?.from;
  const destination = requestedPath?.pathname
    ? `${requestedPath.pathname}${requestedPath.search || ''}${requestedPath.hash || ''}`
    : '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please provide both email and password.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate(destination, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoAutofill = async () => {
    setError(null);
    setLoading(true);
    try {
      await quickLoginDemo();
      navigate(destination, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Demo session initialisation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4 sm:p-6 font-sans">
      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden grid grid-cols-1 md:grid-cols-2">
        {/* Left Side: Brand Narrative & Abstract Quantum Concept */}
        <div className="bg-gradient-to-br from-brand-900 via-brand-800 to-quantum-900 p-8 text-white flex flex-col justify-between relative overflow-hidden">
          <div className="relative z-10 space-y-4">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 bg-white/10 rounded-xl backdrop-blur-md">
                <Atom className="w-6 h-6 text-quantum-300 animate-pulse" />
              </div>
              <div>
                <h2 className="font-bold text-lg text-white">HybridQML</h2>
                <p className="text-xs text-quantum-200">Clinical Screening Gateway</p>
              </div>
            </div>

            <div className="pt-6 space-y-3">
              <h3 className="text-xl font-bold leading-snug">
                Hybrid Quantum-Classical Learning for Oncology
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Connect directly to containerized Pennylane quantum simulators and scikit-learn models.
                Analyze patient biomarker distributions, review AI preprocessing plans, and compare classifier sensitivities.
              </p>
            </div>
          </div>

          <div className="relative z-10 pt-8 border-t border-white/10 text-[11px] text-slate-400">
            Authorized clinical and research personnel only. All access logged and audited.
          </div>
        </div>

        {/* Right Side: Login Form */}
        <div className="p-8 sm:p-10 flex flex-col justify-center">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900">Sign In</h2>
            <p className="text-xs text-slate-500 mt-1">Enter your credentials to access the screening workspace</p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Demo Autofill Banner */}
          <div className="mb-6 p-3.5 bg-quantum-50 border border-quantum-200 rounded-xl flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-quantum-600 flex-shrink-0" />
              <div className="text-[11px] text-quantum-900">
                <span className="font-semibold block">Demonstration Mode</span>
                <span className="text-quantum-700">One-click login with pre-seeded clinician credentials</span>
              </div>
            </div>
            <button
              type="button"
              onClick={handleDemoAutofill}
              disabled={loading}
              className="px-3 py-1.5 bg-quantum-600 hover:bg-quantum-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-all whitespace-nowrap"
            >
              Autofill Demo
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="doctor@hospital.org"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-2.5 flex items-center justify-center space-x-2 text-xs"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In to Workspace'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          <div className="mt-6 text-center text-xs text-slate-500">
            New researcher or biostatistician?{' '}
            <Link to="/register" className="font-semibold text-brand-700 hover:text-brand-900">
              Create account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
