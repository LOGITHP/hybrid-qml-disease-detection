import React from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  FlaskConical,
  Database,
  Sliders,
  Filter,
  Layers,
  Cpu,
  Atom,
  BarChart3,
  Activity,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

const CHAIN_STAGES = [
  { stage: '1. Ingestion', title: 'Biomedical Dataset', desc: 'Lung Cancer Cohort (309 patients, 16 biomarkers)', icon: Database, artifact: 'datasets/v1/original.csv' },
  { stage: '2. Preprocessing', title: 'AI Preprocessing Agent', desc: 'Stratified 70/15/15 split, Median Imputation, Zero Leakage', icon: Sliders, artifact: 'runs/prep-401/pipeline.joblib' },
  { stage: '3. Features', title: 'Canonical Feature Selection', desc: 'Top 4: WHEEZING, YELLOW_FINGERS, AGE, SHORTNESS_OF_BREATH', icon: Filter, artifact: 'runs/fs-run-001/features.json' },
  { stage: '4. Models', title: 'Hybrid Architectures', desc: 'Classical Linear/RBF SVM & PennyLane 4-Qubit VQC', icon: Layers, artifact: 'models/vqc-4/weights.npy' },
  { stage: '5. Quantum', title: 'Quantum Execution', desc: 'AngleEmbedding RY + Linear CNOT Entanglement + Pauli-Z', icon: Atom, artifact: 'backends/default.qubit' },
  { stage: '6. Evaluation', title: 'Clinical Benchmark', desc: 'Accuracy: 93.5% &bull; Sensitivity: 95.1% &bull; ROC-AUC: 0.865', icon: BarChart3, artifact: 'evaluations/benchmark-matrix.json' },
];

export const ExperimentDetailPage: React.FC = () => {
  const { experimentId } = useParams<{ experimentId: string }>();

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-mono text-xs text-slate-400">ID: {experimentId || 'exp-01'}</span>
            <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
              Audited & Reproducible
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            End-to-End Reproducibility Chain
          </h1>
          <p className="text-xs text-slate-500">
            Unbroken provenance tracing data ingestion, transformations, circuit weights, and clinical evaluation
          </p>
        </div>

        <Link
          to="/reports"
          className="btn-primary text-xs flex items-center space-x-1.5 self-start sm:self-auto"
        >
          <span>Generate Audit Report</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Reproducibility Timeline */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-8 shadow-sm space-y-8">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
          Traceable Scientific Execution Pipeline
        </h3>

        <div className="relative border-l-2 border-slate-200 ml-4 pl-6 space-y-8">
          {CHAIN_STAGES.map((step) => {
            const Icon = step.icon;
            return (
              <div key={step.stage} className="relative group">
                {/* Timeline Node Dot */}
                <div className="absolute -left-[35px] top-0.5 w-6 h-6 rounded-full bg-brand-800 text-white flex items-center justify-center text-xs shadow-sm ring-4 ring-white">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>

                <div className="space-y-1 bg-slate-50 border border-slate-200 rounded-xl p-4 hover:border-slate-300 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{step.stage}: {step.title}</span>
                    <span className="text-[10px] font-mono text-slate-400">{step.artifact}</span>
                  </div>
                  <p className="text-xs text-slate-600">{step.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
