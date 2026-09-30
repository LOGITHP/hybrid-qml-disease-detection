import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Database,
  Layers,
  Cpu,
  Activity,
  ArrowRight,
  Zap,
  BarChart3,
  Sliders,
  CheckCircle2,
  Atom,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { datasetsApi, modelsApi, quantumApi } from '../../api';
import { MetricCard } from '../../components/common/MetricCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { MedicalNotice } from '../../components/common/MedicalNotice';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

const workflowSteps = [
  { step: '01', title: 'Dataset', path: '/datasets', active: true },
  { step: '02', title: 'Preprocessing', path: '/preprocessing', active: true },
  { step: '03', title: 'Features', path: '/features', active: true },
  { step: '04', title: 'Configuration', path: '/configuration', active: true },
  { step: '05', title: 'Training', path: '/training', active: true },
  { step: '06', title: 'Evaluation', path: '/evaluation', active: true },
  { step: '07', title: 'Prediction', path: '/predictions', active: true },
];

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
  });

  const { data: defaultModels, isLoading: modelsLoading } = useQuery({
    queryKey: ['defaultModels'],
    queryFn: modelsApi.listDefaults,
  });

  const { data: registeredModels } = useQuery({
    queryKey: ['userModels'],
    queryFn: modelsApi.list,
  });

  const { data: quantumDevices, isLoading: devicesLoading } = useQuery({
    queryKey: ['quantumDevices'],
    queryFn: quantumApi.listDevices,
  });

  const isLoading = datasetsLoading || modelsLoading || devicesLoading;
  const allModels = [...(defaultModels || []), ...(registeredModels || [])]
    .filter((model, index, list) => list.findIndex((candidate) => candidate.id === model.id) === index);
  const trainedModels = allModels.filter((model) => model.status === 'trained' || model.status === 'candidate' || model.configuration?.pretrained);
  const topModel = [...trainedModels].sort((a, b) => {
    const accA = a.configuration?.metrics?.accuracy || a.versions?.[0]?.metrics?.accuracy || 0;
    const accB = b.configuration?.metrics?.accuracy || b.versions?.[0]?.metrics?.accuracy || 0;
    return accB - accA;
  })[0];

  return (
    <div className="space-y-8 font-sans">
      {/* Clinician Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <Atom className="w-4 h-4 text-quantum-600 animate-pulse" />
            <span>Hybrid Quantum-Classical Oncology Workspace</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Welcome, {user?.full_name || 'Clinician'}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Biomedical data screening, canonical feature selection, and CML vs QML benchmarking.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link to="/datasets" className="btn-secondary text-xs flex items-center space-x-2">
            <Database className="w-3.5 h-3.5 mr-1" />
            <span>Upload Dataset</span>
          </Link>
          <Link to="/predictions" className="btn-primary text-xs flex items-center space-x-2">
            <Activity className="w-3.5 h-3.5 mr-1" />
            <span>Predict</span>
          </Link>
        </div>
      </div>

      {/* Main Workflow Stepper Widget */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              End-to-End Diagnostic Pipeline
            </h3>
            <p className="text-[11px] text-slate-400">
              Single Source of Truth Feature Selection feeding both Classical SVM and PennyLane Quantum VQC
            </p>
          </div>
          <span className="badge bg-quantum-50 text-quantum-700 border border-quantum-200">
            Hybrid Quantum Platform
          </span>
        </div>

        <div className="flex flex-nowrap overflow-x-auto gap-3 pb-2 scrollbar-thin scrollbar-thumb-slate-200">
          {workflowSteps.map((step, idx) => (
            <Link
              key={step.step}
              to={step.path}
              className="min-w-[130px] flex-1 p-3 bg-slate-50 hover:bg-brand-50/60 border border-slate-200 hover:border-brand-300 rounded-xl transition-all group flex flex-col justify-between"
            >
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 group-hover:text-brand-600 mb-2">
                <span>{step.step}</span>
                <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-800 group-hover:text-brand-900 block truncate">
                  {step.title}
                </span>
                <span className="text-[10px] text-slate-400">Step {idx + 1}</span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Primary KPI Metrics */}
      {isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Biomedical Datasets"
            value={datasets?.length ?? 0}
            subtitle="System datasets"
            icon={Database}
          />
          <MetricCard
            title="Trained Models"
            value={trainedModels.length}
            subtitle="Custom and pretrained"
            icon={Layers}
            badge="Available"
            badgeColor="quantum"
          />
          <MetricCard
            title="Quantum Simulators"
            value={quantumDevices?.length ?? 0}
            subtitle="Noiseless & Noisy NISQ"
            icon={Zap}
            badge="Active"
            badgeColor="success"
          />
        </div>
      )}

      {/* Main Grid: Pre-trained Default Models Zoo & Quantum Infrastructure */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Pretrained Default Models Zoo */}
        <div className="lg:col-span-2 card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Top Performing Model</h3>
              <p className="text-xs text-slate-500">
                Highest accuracy model across all designs and datasets
              </p>
            </div>
            <Link
              to="/evaluation/comparison"
              className="text-xs font-medium text-brand-700 hover:text-brand-900 flex items-center"
            >
              <span>Compare All</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Link>
          </div>

          <div className="pt-2 pb-2">
            {topModel ? (() => {
              const metrics = topModel.configuration?.metrics || topModel.versions?.[0]?.metrics;
              const hasAccuracy = typeof metrics?.accuracy === 'number';
              const datasetId = topModel.configuration?.dataset_id || 'Unknown Dataset';
              return (
                <div className="p-4 bg-brand-50 border border-brand-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-lg text-brand-900">{topModel.name}</span>
                      <StatusBadge status={topModel.model_type} size="sm" />
                    </div>
                    <p className="text-xs text-brand-700 font-medium flex items-center">
                      <Database className="w-3.5 h-3.5 mr-1" />
                      Dataset ID: <span className="font-mono ml-1">{datasetId.length > 20 ? datasetId.slice(0, 8) + '...' : datasetId}</span>
                    </p>
                    <p className="text-xs text-slate-600 line-clamp-1">{topModel.description}</p>
                  </div>
                  <div className="flex flex-col items-start sm:items-end space-y-2">
                    <div className="text-left sm:text-right">
                      <span className="text-2xl font-bold text-emerald-600">
                        {hasAccuracy ? `${(metrics.accuracy * 100).toFixed(1)}%` : '—'}
                      </span>
                      <span className="text-[10px] text-slate-500 block uppercase tracking-wider font-bold">Accuracy</span>
                    </div>
                    <Link
                      to={`/models/${topModel.id}`}
                      className="px-3 py-1.5 text-xs font-semibold text-white bg-brand-700 hover:bg-brand-800 rounded-lg transition-colors"
                    >
                      Inspect Model
                    </Link>
                  </div>
                </div>
              );
            })() : (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center text-slate-500 text-sm">
                No trained models available to display.
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Quantum Backend Device Status */}
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Quantum Infrastructure</h3>
              <p className="text-xs text-slate-500">PennyLane execution backends</p>
            </div>
            <Link
              to="/quantum"
              className="text-xs font-medium text-quantum-600 hover:text-quantum-700"
            >
              Details
            </Link>
          </div>

          <div className="space-y-3">
            {[
              {
                name: 'PennyLane Statevector',
                device: 'default.qubit',
                qubits: 8,
                status: 'ONLINE',
                type: 'Ideal Simulator',
              },
              {
                name: 'Noisy NISQ Open System',
                device: 'default.mixed',
                qubits: 4,
                status: 'ONLINE',
                type: 'Depolarizing & Readout Noise',
              },
              {
                name: 'Hardware QPU Connector',
                device: 'qiskit.ibmq / braket',
                qubits: 127,
                status: 'READY',
                type: 'Cloud Abstraction',
              },
            ].map((d) => (
              <div key={d.device} className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-slate-800">{d.name}</span>
                  <StatusBadge status={d.status} size="sm" />
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500">
                  <span className="font-mono text-slate-600">{d.device}</span>
                  <span>{d.qubits} Qubits</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-1">{d.type}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Clinical Disclaimer Notice */}
      <MedicalNotice />
    </div>
  );
};
