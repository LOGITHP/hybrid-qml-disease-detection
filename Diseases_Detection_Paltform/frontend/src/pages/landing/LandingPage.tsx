import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Activity,
  Archive,
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Atom,
  BarChart3,
  CheckCircle2,
  Cpu,
  Database,
  FileText,
  Filter,
  FlaskConical,
  Layers,
  Lightbulb,
  Settings,
  ShieldCheck,
  Sliders,
  Sparkles,
  Zap,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { MedicalNotice } from '../../components/common/MedicalNotice';

const tourGroups = [
  {
    index: '01',
    eyebrow: 'DATA WORKFLOW',
    title: 'Prepare the cohort',
    description: 'Start with a dataset, review its schema, and build one traceable feature set.',
    modules: [
      { title: 'Datasets', description: 'Browse cohort files, versions, and validation details.', path: '/datasets', icon: Database },
      { title: 'Preprocessing', description: 'Review rule-based, manual, or LLM-refined cleaning plans.', path: '/preprocessing', icon: Sliders },
      { title: 'Feature selection', description: 'Choose a target and inspect the ranked predictors.', path: '/features', icon: Filter },
    ],
  },
  {
    index: '02',
    eyebrow: 'MODEL WORKFLOW',
    title: 'Train classical and quantum models',
    description: 'Inspect available checkpoints, configure training, and view the quantum backends.',
    modules: [
      { title: 'Model zoo', description: 'Inspect pretrained experiment models and recorded metrics.', path: '/models', icon: Layers },
      { title: 'Training lab', description: 'Train a model on the selected dataset and features.', path: '/training', icon: Cpu },
      { title: 'Quantum devices', description: 'Review simulator and quantum execution backends.', path: '/quantum', icon: Zap },
    ],
  },
  {
    index: '03',
    eyebrow: 'RESULTS WORKFLOW',
    title: 'Compare results and screen',
    description: 'Review model performance, compare runs, and inspect prediction explanations.',
    modules: [
      { title: 'Evaluation & comparison', description: 'Review metrics and compare classical with quantum runs.', path: '/evaluation/comparison', icon: BarChart3 },
      { title: 'Predictions & explanations', description: 'Explore screening results and their explainability views.', path: '/predictions', icon: Activity },
    ],
  },
  {
    index: '04',
    eyebrow: 'RESEARCH WORKFLOW',
    title: 'Follow the research record',
    description: 'Open experiments, feedback, reports, artifacts, and workspace controls.',
    modules: [
      { title: 'Experiments', description: 'Review saved experimental runs and their details.', path: '/experiments', icon: FlaskConical },
      { title: 'Feedback & retraining', description: 'Inspect clinician feedback and retraining workflows.', path: '/feedback', icon: Lightbulb },
      { title: 'Reports', description: 'Browse generated evaluation and screening reports.', path: '/reports', icon: FileText },
      { title: 'Artifact registry', description: 'View files and artifacts associated with runs.', path: '/artifacts', icon: Archive },
      { title: 'Workspace settings', description: 'Review account and system preferences.', path: '/settings', icon: Settings },
    ],
  },
];

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { quickLoginDemo } = useAuth();
  const [enteringDemo, setEnteringDemo] = useState(false);
  const [demoError, setDemoError] = useState<string | null>(null);

  const enterDemo = async () => {
    setEnteringDemo(true);
    setDemoError(null);
    try {
      await quickLoginDemo();
      navigate('/dashboard');
    } catch (error) {
      setDemoError(error instanceof Error ? error.message : 'The demonstration workspace could not be opened.');
    } finally {
      setEnteringDemo(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f7fb] font-sans text-slate-900 selection:bg-brand-500 selection:text-white">
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex h-[68px] max-w-7xl items-center justify-between gap-5 px-5 sm:px-8">
          <Link to="/" className="flex shrink-0 items-center gap-3" aria-label="HybridQML home">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-700 to-quantum-600 text-white shadow-md shadow-indigo-900/15">
              <Atom className="h-5 w-5" />
            </span>
            <span>
              <span className="block text-sm font-bold tracking-tight">HybridQML</span>
              <span className="block text-[10px] font-medium text-slate-500">Early Disease Detection Platform</span>
            </span>
          </Link>

          <nav className="hidden items-center gap-7 md:flex" aria-label="Landing page navigation">
            <a href="#system-tour" className="text-xs font-semibold text-slate-600 transition hover:text-brand-800">System tour</a>
            <a href="#architecture" className="text-xs font-semibold text-slate-600 transition hover:text-brand-800">Architecture</a>
          </nav>

          <div className="flex shrink-0 items-center gap-3">
            <Link to="/login" className="hidden text-xs font-semibold text-slate-600 transition hover:text-slate-900 sm:inline-flex">Sign in</Link>
            <button
              type="button"
              onClick={enterDemo}
              disabled={enteringDemo}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-700 to-quantum-600 px-4 py-2.5 text-xs font-semibold text-white shadow-md shadow-indigo-900/15 transition hover:-translate-y-0.5 hover:shadow-lg disabled:cursor-wait disabled:opacity-70"
            >
              {enteringDemo ? 'Opening demo…' : 'Enter demo workspace'}
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden border-b border-slate-200/70">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_65%_at_18%_0%,rgba(99,102,241,0.12),transparent_70%),radial-gradient(ellipse_50%_70%_at_92%_38%,rgba(6,182,212,0.10),transparent_72%)]" />
          <div className="relative mx-auto grid max-w-7xl items-center gap-10 px-5 py-12 sm:px-8 sm:py-16 lg:grid-cols-[1.08fr_0.92fr] lg:gap-14 lg:py-[72px]">
            <div className="max-w-2xl">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white/75 px-3 py-1.5 text-[11px] font-semibold text-indigo-800 shadow-sm">
                <Sparkles className="h-3.5 w-3.5" />
                A guided, interactive system tour
              </div>
              <h1 className="max-w-[14ch] text-[2.7rem] font-extrabold leading-[1.04] tracking-[-0.045em] text-slate-950 sm:text-5xl lg:text-[3.65rem]">
                From clinical cohort to{' '}
                <span className="bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-500 bg-clip-text text-transparent">explainable screening</span>
              </h1>
              <p className="mt-5 max-w-xl text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
                Explore the complete HybridQML research workspace: dataset preparation, feature ranking, classical and quantum model training, evaluation, predictions, and research records.
              </p>
              <div className="mt-7 flex flex-col gap-3 sm:flex-row">
                <button
                  type="button"
                  onClick={enterDemo}
                  disabled={enteringDemo}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-800 px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-brand-900/15 transition hover:bg-brand-700 disabled:cursor-wait disabled:opacity-70"
                >
                  <span>{enteringDemo ? 'Opening the demo workspace…' : 'Open interactive demo'}</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
                <a
                  href="#system-tour"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white/85 px-5 py-3.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-indigo-300 hover:bg-white"
                >
                  Browse all system modules
                  <ArrowDown className="h-4 w-4 text-indigo-600" />
                </a>
              </div>
              <p className="mt-3 text-[11px] leading-5 text-slate-500">
                Jury walkthrough: open the demo, then use the workspace sidebar to move between every module.
              </p>
              {demoError && <p role="alert" className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{demoError}</p>}
            </div>

            <div className="relative mx-auto w-full max-w-xl">
              <div className="absolute -inset-5 rounded-[2rem] bg-gradient-to-br from-indigo-300/25 via-white/30 to-cyan-300/30 blur-2xl" />
              <div className="relative overflow-hidden rounded-[1.6rem] border border-white bg-white/90 p-5 shadow-[0_24px_70px_-28px_rgba(31,41,82,0.36)] sm:p-6">
                <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-600">Jury quick start</p>
                    <h2 className="mt-1 text-base font-bold tracking-tight text-slate-900">See the system in three steps</h2>
                  </div>
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700"><CheckCircle2 className="h-5 w-5" /></span>
                </div>
                <ol className="mt-4 space-y-3">
                  {[
                    { n: '01', title: 'Open the demo workspace', text: 'The built-in demo sign-in takes you straight to the dashboard.' },
                    { n: '02', title: 'Follow the data workflow', text: 'Visit Datasets, Preprocessing, and Feature Selection from the sidebar.' },
                    { n: '03', title: 'Review the research outputs', text: 'Compare model runs, open predictions, and inspect reports and experiments.' },
                  ].map((step) => (
                    <li key={step.n} className="flex gap-3 rounded-xl bg-slate-50/90 p-3.5">
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white text-[10px] font-bold text-indigo-700 shadow-sm ring-1 ring-slate-200">{step.n}</span>
                      <span>
                        <span className="block text-xs font-bold text-slate-800">{step.title}</span>
                        <span className="mt-1 block text-[11px] leading-relaxed text-slate-500">{step.text}</span>
                      </span>
                    </li>
                  ))}
                </ol>
                <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4">
                  {[
                    { label: 'Classical ML', icon: Cpu },
                    { label: 'Quantum ML', icon: Atom },
                    { label: 'Explainability', icon: Lightbulb },
                  ].map(({ label, icon: Icon }) => (
                    <span key={label} className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-1.5 text-[10px] font-semibold text-slate-600">
                      <Icon className="h-3 w-3 text-indigo-600" />{label}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="system-tour" className="scroll-mt-24 px-5 py-14 sm:px-8 sm:py-20">
          <div className="mx-auto max-w-7xl">
            <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
              <div className="max-w-2xl">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-600">Explore the full workspace</p>
                <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">Every module, one clear route in</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">Choose an area below to open it in the demo. If sign-in is needed, you will return to the module you selected.</p>
              </div>
              <button type="button" onClick={enterDemo} disabled={enteringDemo} className="inline-flex w-fit items-center gap-2 text-xs font-bold text-brand-800 transition hover:text-indigo-600 disabled:opacity-60">
                {enteringDemo ? 'Opening demo…' : 'Start at the dashboard'} <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              {tourGroups.map((group) => (
                <article key={group.index} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                  <div className="flex gap-3 border-b border-slate-100 pb-4">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-xs font-extrabold text-indigo-700">{group.index}</span>
                    <div>
                      <p className="text-[9px] font-bold tracking-[0.18em] text-indigo-600">{group.eyebrow}</p>
                      <h3 className="mt-0.5 text-sm font-bold text-slate-900">{group.title}</h3>
                      <p className="mt-1 text-[11px] leading-relaxed text-slate-500">{group.description}</p>
                    </div>
                  </div>
                  <div className="mt-3 divide-y divide-slate-100">
                    {group.modules.map((module) => {
                      const Icon = module.icon;
                      return (
                        <Link key={module.path} to={module.path} className="group flex items-center gap-3 rounded-lg px-2 py-3 transition hover:bg-indigo-50/70">
                          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 transition group-hover:border-indigo-200 group-hover:text-indigo-700"><Icon className="h-4 w-4" /></span>
                          <span className="min-w-0 flex-1">
                            <span className="block text-xs font-bold text-slate-800 group-hover:text-indigo-800">{module.title}</span>
                            <span className="mt-0.5 block text-[10px] leading-relaxed text-slate-500">{module.description}</span>
                          </span>
                          <ArrowUpRight className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-indigo-600" />
                        </Link>
                      );
                    })}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="architecture" className="scroll-mt-24 border-y border-slate-200 bg-white px-5 py-12 sm:px-8 sm:py-16">
          <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-600">System architecture</p>
              <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">A research workflow with traceable stages</h2>
              <p className="mt-3 max-w-lg text-sm leading-6 text-slate-600">The workspace connects cohort preparation to model evaluation, with classical and quantum experiments sharing the selected feature set.</p>
              <div className="mt-5"><MedicalNotice compact /></div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { title: 'Web workspace', detail: 'React interface for datasets, analysis, model configuration, and review.', icon: Layers },
                { title: 'Research services', detail: 'API-backed data, training, experiment, and reporting workflows.', icon: Database },
                { title: 'Model execution', detail: 'Classical estimators and PennyLane quantum simulation paths.', icon: Zap },
              ].map((item, index) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="relative rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                    <span className="text-[9px] font-bold uppercase tracking-[0.16em] text-slate-400">Layer 0{index + 1}</span>
                    <span className="mt-3 flex h-9 w-9 items-center justify-center rounded-xl bg-white text-indigo-700 shadow-sm ring-1 ring-slate-200"><Icon className="h-4 w-4" /></span>
                    <h3 className="mt-3 text-xs font-bold text-slate-900">{item.title}</h3>
                    <p className="mt-1.5 text-[10px] leading-relaxed text-slate-500">{item.detail}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className="px-5 py-12 sm:px-8 sm:py-16">
          <div className="mx-auto flex max-w-7xl flex-col gap-5 rounded-3xl bg-gradient-to-r from-slate-950 via-brand-950 to-indigo-950 px-6 py-8 text-white shadow-xl sm:flex-row sm:items-center sm:justify-between sm:px-9">
            <div className="max-w-2xl">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300">Ready to explore?</p>
              <h2 className="mt-2 text-xl font-bold tracking-tight sm:text-2xl">Open the workspace and follow the system end to end.</h2>
              <p className="mt-2 text-xs leading-5 text-slate-300">The dashboard and sidebar link to every dataset, model, result, and research module.</p>
            </div>
            <button type="button" onClick={enterDemo} disabled={enteringDemo} className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-xs font-bold text-brand-900 shadow-sm transition hover:bg-cyan-50 disabled:opacity-60">
              {enteringDemo ? 'Opening demo…' : 'Enter demo workspace'} <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white px-5 py-6 sm:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 text-[10px] text-slate-500">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>HybridQML research demonstration · Outputs are not definitive clinical diagnoses.</span>
          </div>
          <Link to="/login" className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-slate-500 transition hover:text-brand-800">Sign in <ArrowRight className="h-3 w-3" /></Link>
        </div>
      </footer>
    </div>
  );
};
