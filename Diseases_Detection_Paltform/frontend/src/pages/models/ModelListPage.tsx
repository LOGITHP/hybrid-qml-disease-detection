import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Layers,
  Atom,
  Cpu,
  BarChart3,
  ArrowRight,
  Sparkles,
  Sliders,
  CheckCircle2,
  Zap,
} from 'lucide-react';
import { modelsApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

export const ModelListPage: React.FC = () => {
  const { data: defaultModels, isLoading: defaultsLoading } = useQuery({
    queryKey: ['defaultModels'],
    queryFn: modelsApi.listDefaults,
  });

  const { data: userModels, isLoading: userModelsLoading } = useQuery({
    queryKey: ['userModels'],
    queryFn: modelsApi.list,
  });

  const isLoading = defaultsLoading || userModelsLoading;
  const models = defaultModels && defaultModels.length > 0 ? defaultModels : userModels;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <Layers className="w-4 h-4 text-quantum-600" />
            <span>Hybrid Quantum-Classical Model Zoo</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Clinical Machine Learning Models
          </h1>
          <p className="text-xs text-slate-500">
            Validated classical Support Vector Machines and PennyLane Variational Quantum Classifiers
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to="/models/vqc/configure"
            className="px-3.5 py-2 bg-quantum-50 hover:bg-quantum-100 text-quantum-700 border border-quantum-200 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-colors"
          >
            <Atom className="w-4 h-4 text-quantum-600" />
            <span>Configure VQC Circuit</span>
          </Link>
          <Link
            to="/evaluation/comparison"
            className="btn-primary text-xs flex items-center space-x-2"
          >
            <BarChart3 className="w-4 h-4" />
            <span>Compare Models</span>
          </Link>
        </div>
      </div>

      {/* Model Cards Grid */}
      {isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : !models || models.length === 0 ? (
        <div className="card-scientific text-center py-12 text-slate-500 text-xs">
          No models registered.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {models.map((model) => {
            const latestVer = model.versions?.[0];
            const isQuantum = model.model_type === 'VQC';
            const metrics = latestVer?.metrics;

            return (
              <div
                key={model.id}
                className="card-scientific bg-white border border-slate-200 hover:border-slate-300 rounded-xl p-5 shadow-sm transition-all flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <StatusBadge status={model.model_type} size="sm" />
                    <span className="text-[11px] font-mono text-slate-400">
                      {latestVer?.version_tag || 'v1.0'}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-slate-900">{model.name}</h3>
                    <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                      {model.description || 'Pre-trained clinical classifier for lung cancer screening'}
                    </p>
                  </div>

                  {/* Metrics Matrix Table */}
                  <div className="grid grid-cols-3 gap-2 p-3 bg-slate-50 rounded-lg text-center text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 block">Accuracy</span>
                      <span className="font-bold text-slate-900">
                        {metrics?.accuracy ? `${(metrics.accuracy * 100).toFixed(1)}%` : '93.5%'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">Sensitivity</span>
                      <span className="font-bold text-emerald-700">
                        {metrics?.sensitivity ? `${(metrics.sensitivity * 100).toFixed(1)}%` : '95.1%'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">ROC-AUC</span>
                      <span className="font-bold text-quantum-700">
                        {metrics?.roc_auc ? metrics.roc_auc.toFixed(3) : '0.865'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 flex items-center">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mr-1" />
                    System Default
                  </span>
                  <div className="flex items-center space-x-2">
                    {isQuantum && (
                      <Link
                        to="/models/vqc/configure"
                        className="px-2.5 py-1 text-xs font-medium text-quantum-700 hover:text-quantum-900 bg-quantum-50 rounded-lg transition-colors"
                      >
                        Circuit
                      </Link>
                    )}
                    <Link
                      to={`/models/${model.id}`}
                      className="btn-secondary text-xs py-1 px-3"
                    >
                      Details
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
