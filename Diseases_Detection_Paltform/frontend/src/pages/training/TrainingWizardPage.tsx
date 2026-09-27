import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Cpu,
  Layers,
  Database,
  Filter,
  Atom,
  ArrowRight,
  Play,
  CheckCircle2,
  Sparkles,
  Zap,
} from 'lucide-react';
import { datasetsApi, modelsApi, trainingApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

export const TrainingWizardPage: React.FC = () => {
  const navigate = useNavigate();

  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [executionDevice, setExecutionDevice] = useState<'simulator' | 'noisy' | 'hardware'>('simulator');

  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: datasetsApi.list });
  const { data: models } = useQuery({ queryKey: ['defaultModels'], queryFn: modelsApi.listDefaults });

  const activeDataset = datasets?.find((d) => d.id === selectedDatasetId) || datasets?.[0];
  const activeVersion = activeDataset?.versions?.[0];
  const activeModel = models?.find((m) => m.id === selectedModelId) || models?.[0];

  const trainMutation = useMutation({
    mutationFn: async () => {
      if (!activeModel || !activeVersion) throw new Error('Missing configuration');
      return await trainingApi.startRun({
        model_id: activeModel.id,
        dataset_version_id: activeVersion.id,
        feature_selection_run_id: 'canonical-fs-4',
      });
    },
    onSuccess: (run) => {
      navigate(`/training/${run.id}`);
    },
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <Cpu className="w-4 h-4 text-quantum-600" />
            <span>Training Orchestration</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Launch Classical or Quantum Model Training
          </h1>
          <p className="text-xs text-slate-500">
            Coordinate end-to-end model training using the canonical 4-feature subset
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Setup Options */}
        <div className="lg:col-span-2 space-y-5">
          {/* Step 1: Select Model Archetype */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              1. Choose Model Archetype
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { id: 'pretrained-cml-svm-linear-4', name: 'Linear SVM', type: 'Classical ML', desc: 'Fast, convex linear decision boundary' },
                { id: 'pretrained-cml-svm-rbf-4', name: 'RBF Kernel SVM', type: 'Classical ML', desc: 'Non-linear high-dimensional margin' },
                { id: 'pretrained-qml-vqc-4-noiseless', name: 'PennyLane VQC', type: 'Quantum ML', desc: 'AngleEmbedding variational circuit' },
              ].map((m) => {
                const isSelected = (selectedModelId || 'pretrained-qml-vqc-4-noiseless') === m.id;
                return (
                  <div
                    key={m.id}
                    onClick={() => setSelectedModelId(m.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'border-brand-800 bg-brand-50/60 shadow-sm'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-slate-900">{m.name}</span>
                      <StatusBadge status={m.type === 'Quantum ML' ? 'VQC' : 'SVM_LINEAR'} size="sm" />
                    </div>
                    <p className="text-[11px] text-slate-500">{m.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Step 2: Target Dataset & Feature Single Source of Truth */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              2. Selected Features & Patient Cohort
            </h3>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Biomedical Cohort:</span>
                <span className="font-bold text-slate-900">
                  {activeDataset?.name || 'Lung Cancer Benchmark Cohort'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Locked Feature Count:</span>
                <span className="font-bold text-brand-900 font-mono">4 Canonical Features</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Feature Names:</span>
                <span className="font-mono text-slate-800 text-[11px]">
                  WHEEZING, YELLOW_FINGERS, AGE, SHORTNESS_OF_BREATH
                </span>
              </div>
            </div>
          </div>

          {/* Step 3: Execution Backend Device */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              3. Execution Backend
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div
                onClick={() => setExecutionDevice('simulator')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  executionDevice === 'simulator'
                    ? 'border-quantum-600 bg-quantum-50/50 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <Atom className="w-4 h-4 text-quantum-600" />
                  <span className="font-bold text-slate-900">Statevector Simulator (default.qubit)</span>
                </div>
                <p className="text-[11px] text-slate-500">Exact analytic gradient descent.</p>
              </div>

              <div
                onClick={() => setExecutionDevice('noisy')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  executionDevice === 'noisy'
                    ? 'border-quantum-600 bg-quantum-50/50 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <Zap className="w-4 h-4 text-amber-600" />
                  <span className="font-bold text-slate-900">Noisy NISQ Device (default.mixed)</span>
                </div>
                <p className="text-[11px] text-slate-500">Includes depolarizing noise & readout error.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Run Summary Card */}
        <div className="space-y-4">
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Training Run Specification
            </h3>

            <div className="space-y-3 text-xs divide-y divide-slate-100">
              <div className="pt-2 flex justify-between">
                <span className="text-slate-500">Model:</span>
                <span className="font-bold text-slate-900">{activeModel?.name || 'PennyLane VQC'}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-slate-500">Selected Features:</span>
                <span className="font-bold text-brand-900">4 Biomarkers</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-slate-500">Execution Backend:</span>
                <span className="font-bold text-quantum-700 capitalize">{executionDevice}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-slate-500">Partitions:</span>
                <span className="text-slate-700">70% Train &bull; 15% Val &bull; 15% Test</span>
              </div>
            </div>

            <button
              onClick={() => trainMutation.mutate()}
              disabled={trainMutation.isPending}
              className="w-full btn-primary text-xs py-3 flex items-center justify-center space-x-2 shadow-md"
            >
              <Play className="w-4 h-4" />
              <span>{trainMutation.isPending ? 'Dispatching Training Job...' : 'Start Model Training'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
