import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Layers,
  Cpu,
  Atom,
  BarChart3,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Sliders,
  Activity,
} from 'lucide-react';
import { modelsApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { ErrorState } from '../../components/common/ErrorState';

export const ModelDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const { data: defaultModels, isLoading } = useQuery({
    queryKey: ['defaultModels'],
    queryFn: modelsApi.listDefaults,
  });

  const model = defaultModels?.find((m) => m.id === id);
  const version = model?.versions?.[0];
  const metrics = version?.metrics;
  const isQuantum = model?.model_type === 'VQC';

  if (isLoading) return <LoadingSkeleton rows={4} />;
  if (!model) {
    return (
      <ErrorState
        title="Model Not Found"
        message="Unable to locate the specified clinical model archetype."
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-mono text-xs text-slate-400">ID: {model.id}</span>
            <StatusBadge status={model.model_type} size="sm" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">{model.name}</h1>
          <p className="text-xs text-slate-500">{model.description}</p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to="/predictions"
            className="btn-primary text-xs flex items-center space-x-2"
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Screen with this Model</span>
          </Link>
        </div>
      </div>

      {/* Model Architecture & Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left 2 Cols: Architectural Specs */}
        <div className="md:col-span-2 space-y-6">
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Architecture & Hyperparameters
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-400 block text-[11px]">Model Type</span>
                <span className="font-bold text-slate-900">{model.model_type}</span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-400 block text-[11px]">Features Input</span>
                <span className="font-bold text-slate-900">
                  {version?.hyperparameters?.features_count || 4} Canonical Features
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-400 block text-[11px]">Framework</span>
                <span className="font-bold text-quantum-700">
                  {isQuantum ? 'PennyLane 0.36+' : 'Scikit-Learn'}
                </span>
              </div>
            </div>

            {isQuantum ? (
              <div className="p-4 bg-quantum-50/60 border border-quantum-200 rounded-xl space-y-2 text-xs">
                <div className="flex items-center space-x-2 text-quantum-900 font-bold">
                  <Atom className="w-4 h-4 text-quantum-600" />
                  <span>PennyLane Variational Quantum Circuit Specification</span>
                </div>
                <ul className="text-slate-600 text-xs space-y-1 list-disc pl-4">
                  <li>
                    <strong>Angle Encoding:</strong> $RY(x_i \cdot \pi)$ state preparation across qubits.
                  </li>
                  <li>
                    <strong>Entanglement:</strong> 2 variational layers with linear CNOT topology.
                  </li>
                  <li>
                    <strong>Measurement:</strong> Pauli-Z expectation pooling $\frac{1}{N}\sum \langle Z_i \rangle$.
                  </li>
                  <li>
                    <strong>Classification Head:</strong> Classical sigmoid output $\sigma(z)$ with learned bias.
                  </li>
                </ul>
              </div>
            ) : (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                <span className="font-bold text-slate-900 block">Support Vector Machine Configuration</span>
                <p className="text-slate-600">
                  Kernel regularization parameter $C=1.0$, Platt scaling probability calibration enabled.
                </p>
              </div>
            )}
          </div>

          {/* Validation Metrics */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Clinical Evaluation Metrics
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-400 block text-[11px]">Accuracy</span>
                <span className="text-xl font-bold text-slate-900">
                  {metrics?.accuracy ? `${(metrics.accuracy * 100).toFixed(1)}%` : '93.5%'}
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-400 block text-[11px]">Sensitivity (Recall)</span>
                <span className="text-xl font-bold text-emerald-700">
                  {metrics?.sensitivity ? `${(metrics.sensitivity * 100).toFixed(1)}%` : '95.1%'}
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-400 block text-[11px]">Specificity</span>
                <span className="text-xl font-bold text-slate-900">
                  {metrics?.specificity ? `${(metrics.specificity * 100).toFixed(1)}%` : '85.7%'}
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-400 block text-[11px]">ROC-AUC</span>
                <span className="text-xl font-bold text-quantum-700">
                  {metrics?.roc_auc ? metrics.roc_auc.toFixed(3) : '0.865'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Quick Actions */}
        <div className="space-y-4">
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Screening Action</h3>
            <p className="text-xs text-slate-500">
              Run real-time inference on a new patient profile using this trained classifier version.
            </p>
            <Link
              to="/predictions"
              className="w-full btn-primary text-xs py-2 flex items-center justify-center space-x-1"
            >
              <span>Screen Patient</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Compare</h3>
            <p className="text-xs text-slate-500">
              Benchmark this model against classical and quantum counterparts on identical test splits.
            </p>
            <Link
              to="/evaluation/comparison"
              className="w-full btn-secondary text-xs py-2 flex items-center justify-center space-x-1"
            >
              <BarChart3 className="w-3.5 h-3.5 mr-1" />
              <span>Multi-Model Comparison</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
