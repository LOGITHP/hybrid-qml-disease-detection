import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Layers, Atom, BarChart3, CheckCircle2 } from 'lucide-react';
import { modelsApi } from '../../api';
import { Model } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

const formatPercent = (value: unknown) => typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : '—';

export const ModelListPage: React.FC = () => {
  const { data: defaultModels, isLoading: defaultsLoading } = useQuery({ queryKey: ['defaultModels'], queryFn: modelsApi.listDefaults });
  const { data: userModels, isLoading: userModelsLoading } = useQuery({ queryKey: ['userModels'], queryFn: modelsApi.list });
  const isLoading = defaultsLoading || userModelsLoading;
  const mergedModels = [...(defaultModels || []), ...(userModels || [])];
  const models = mergedModels.filter((model, index) => mergedModels.findIndex((candidate) => candidate.id === model.id) === index);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-4 sm:flex-row sm:items-center">
        <div>
          <div className="mb-1 flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-brand-700"><Layers className="h-4 w-4 text-quantum-600" /><span>Experimental_ML model catalog</span></div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Trained models and results</h1>
          <p className="text-xs text-slate-500">Recorded experiment metrics are shown with their actual checkpoint. New training runs appear with their own held-out results.</p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/models/vqc/configure" className="flex items-center gap-2 rounded-lg border border-quantum-200 bg-quantum-50 px-3.5 py-2 text-xs font-semibold text-quantum-700"><Atom className="h-4 w-4" /><span>Configure VQC</span></Link>
          <Link to="/evaluation/comparison" className="btn-primary flex items-center gap-2 text-xs"><BarChart3 className="h-4 w-4" /><span>Compare trained models</span></Link>
        </div>
      </div>

      {isLoading ? <LoadingSkeleton rows={4} /> : !models.length ? <div className="card-scientific py-12 text-center text-xs text-slate-500">No models are registered yet.</div> : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {models.map((model: Model) => {
            const config = model.configuration || {};
            const metrics = (config.metrics || model.versions?.[0]?.metrics) as Record<string, unknown> | undefined;
            const hasMetrics = typeof metrics?.accuracy === 'number';
            const isQuantum = model.model_type.toLowerCase() === 'vqc';
            const source = typeof config.source_experiment === 'string' ? config.source_experiment : '';
            const isUserTrained = !!config.dataset_version_id;
            const recordedExperiment = !!config.pretrained;
            return <article key={model.id} className="card-scientific flex flex-col justify-between space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:border-slate-300">
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2"><StatusBadge status={model.model_type} size="sm" /><span className="text-[10px] font-semibold text-slate-500">{recordedExperiment ? 'Experimental_ML checkpoint' : isUserTrained ? 'Trained on upload' : 'Trainable template'}</span></div>
                <div><h2 className="text-base font-bold text-slate-900">{model.name}</h2><p className="mt-1 line-clamp-3 text-xs leading-relaxed text-slate-500">{model.description || 'No model description recorded.'}</p></div>
                {Array.isArray(config.selected_features) && <div className="rounded-lg bg-slate-50 p-3"><span className="mb-1 block text-[10px] font-semibold uppercase text-slate-400">Features · {config.selected_features.length}</span><span className="font-mono text-[10px] text-slate-700">{(config.selected_features as string[]).join(', ')}</span></div>}
                {hasMetrics ? <>
                  <div className="grid grid-cols-3 gap-2 rounded-lg bg-slate-50 p-3 text-center text-xs">
                    <div><span className="block text-[10px] text-slate-400">Accuracy</span><b className="text-slate-900">{formatPercent(metrics?.accuracy)}</b></div>
                    <div><span className="block text-[10px] text-slate-400">Sensitivity</span><b className="text-emerald-700">{formatPercent(metrics?.sensitivity)}</b></div>
                    <div><span className="block text-[10px] text-slate-400">ROC-AUC</span><b className="text-quantum-700">{typeof metrics?.roc_auc === 'number' ? metrics.roc_auc.toFixed(3) : '—'}</b></div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center text-[10px] text-slate-500">
                    <span>Balanced acc. <b className="block text-slate-800">{formatPercent(metrics?.balanced_accuracy)}</b></span>
                    <span>Specificity <b className="block text-slate-800">{formatPercent(metrics?.specificity)}</b></span>
                    <span>F1 score <b className="block text-slate-800">{formatPercent(metrics?.f1_score)}</b></span>
                  </div>
                  <p className="text-[10px] text-slate-400">{recordedExperiment ? `Recorded experiment · ${metrics?.test_samples ?? '—'} test rows` : `Held-out test · ${metrics?.test_samples ?? '—'} rows`}</p>
                </> : <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-xs text-slate-500">No measured performance is recorded yet. Train this template on an uploaded dataset to create its own metrics.</div>}
                {source && <p className="break-all text-[10px] text-slate-400">Checkpoint: <span className="font-mono">{source}</span></p>}
              </div>
              <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                <span className="flex items-center text-[11px] text-slate-400">
                  {recordedExperiment ? (
                    <><CheckCircle2 className="mr-1 h-3.5 w-3.5 text-emerald-600" />Saved experiment model</>
                  ) : isUserTrained ? (
                    <><Layers className="mr-1 h-3.5 w-3.5 text-blue-600" />Your trained model</>
                  ) : (
                    <><CheckCircle2 className="mr-1 h-3.5 w-3.5 text-emerald-600" />System Default</>
                  )}
                </span>
                <div className="flex items-center gap-2">{isQuantum && <Link to="/models/vqc/configure" className="rounded-lg bg-quantum-50 px-2.5 py-1 text-xs font-medium text-quantum-700">Circuit</Link>}<Link to={`/models/${model.id}`} className="btn-secondary px-3 py-1 text-xs">Details</Link></div>
              </div>
            </article>;
          })}
        </div>
      )}
    </div>
  );
};
