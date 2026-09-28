import React from 'react';
import { Link } from 'react-router-dom';
import {
  Atom,
  Cpu,
  Database,
  Sliders,
  Filter,
  Layers,
  BarChart3,
  Activity,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import { MedicalNotice } from '../../components/common/MedicalNotice';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-brand-500 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-200 bg-white/70 backdrop-blur-md sticky top-0 z-30 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-brand-700 to-quantum-600 rounded-lg text-white shadow-lg shadow-quantum-900/30">
              <Atom className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <span className="font-bold text-slate-900 tracking-wide text-base block">HybridQML</span>
              <span className="text-[10px] text-slate-500 font-medium tracking-tight block">
                Early Disease Detection Platform
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <Link
              to="/login"
              className="text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/login"
              className="px-4 py-2 bg-gradient-to-r from-brand-700 to-quantum-600 hover:from-brand-600 hover:to-quantum-500 text-white text-xs font-semibold rounded-lg shadow-md transition-all flex items-center space-x-2"
            >
              <span>Launch Platform</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-6 relative overflow-hidden flex-1 flex flex-col justify-center">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(99,102,241,0.15),rgba(255,255,255,0))]" />
        
        <div className="max-w-4xl mx-auto text-center relative z-10 space-y-6">
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-quantum-50 border border-quantum-200 rounded-full text-xs font-medium text-quantum-700">
            <Atom className="w-3.5 h-3.5 animate-spin" />
            <span>PennyLane Quantum Circuits &bull; Classical Support Vector Machines</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-tight">
            Hybrid Quantum Machine Learning for{' '}
            <span className="bg-gradient-to-r from-quantum-600 to-cyan-500 bg-clip-text text-transparent">
              Early Disease Detection
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            A production-ready biomedical screening system combining AI-driven clinical data preprocessing,
            canonical feature ranking, and side-by-side evaluation between Variational Quantum Classifiers (VQC)
            and classical Support Vector Machines.
          </p>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/login"
              className="w-full sm:w-auto px-6 py-3.5 bg-brand-700 hover:bg-brand-600 text-white font-semibold text-sm rounded-xl shadow-lg transition-all flex items-center justify-center space-x-2"
            >
              <span>Access Clinical Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/dashboard"
              className="w-full sm:w-auto px-6 py-3.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold text-sm rounded-xl transition-all flex items-center justify-center space-x-2 shadow-sm"
            >
              <Cpu className="w-4 h-4 text-quantum-600" />
              <span>Explore Architecture</span>
            </Link>
          </div>
        </div>

        {/* End-to-End Workflow Flowchart */}
        <div className="max-w-5xl mx-auto mt-20 p-6 bg-white/80 border border-slate-200 rounded-2xl relative z-10 shadow-xl">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-6 text-center">
            Standardized Diagnostic Screening Pipeline
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            {[
              { step: '01', title: 'Data Ingestion', desc: 'Patient CSV Cohort', icon: Database },
              { step: '02', title: 'AI Preprocessing', desc: 'Leak-free Splits', icon: Sliders },
              { step: '03', title: 'Feature Selection', desc: 'Single Truth Ranking', icon: Filter },
              { step: '04', title: 'Hybrid Learning', desc: 'CML & VQC Models', icon: Layers },
              { step: '05', title: 'Evaluation', desc: 'CML vs QML Benchmark', icon: BarChart3 },
              { step: '06', title: 'Risk Screening', desc: 'Probability & Risk', icon: Activity },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.step}
                  className="bg-slate-50/90 border border-slate-200 p-4 rounded-xl flex flex-col items-center text-center space-y-2 hover:border-quantum-400/50 transition-colors shadow-sm"
                >
                  <span className="text-[10px] font-mono text-quantum-600 font-bold">{item.step}</span>
                  <div className="p-2 bg-white rounded-lg text-slate-600 shadow-sm border border-slate-100">
                    <Icon className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-semibold text-slate-900">{item.title}</h4>
                  <p className="text-[10px] text-slate-500">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Safety Notice Footer */}
      <footer className="border-t border-slate-200 bg-white py-8 px-6 text-slate-500 text-xs">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <p>&copy; {new Date().getFullYear()} Hybrid Quantum Machine Learning Platform for Early Disease Detection.</p>
          <div className="flex items-center space-x-6 text-[11px]">
            <span className="inline-flex items-center">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 mr-1" />
              HIPAA & Privacy Conscious
            </span>
            <span>PennyLane 0.36+</span>
            <span>FastAPI 0.111+</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
