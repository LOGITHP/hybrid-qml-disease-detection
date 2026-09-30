import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Activity, ArrowRight, BarChart3, Cpu, Database } from 'lucide-react';
import { trainingApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { EmptyState } from '../../components/common/EmptyState';

export const TrainingMonitorPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: run, isLoading, isError } = useQuery({
    queryKey: ['trainingRun', id],
    queryFn: () => (id ? trainingApi.getStatus(id) : Promise.reject(new Error('Missing run ID'))),
    enabled: !!id,
    refetchInterval: (query) => query.state.data?.status === 'completed' || query.state.data?.status === 'failed' ? false : 3000,
  });

  if (isLoading) return <LoadingSkeleton rows={4} />;
  if (isError || !run) return <EmptyState icon={Cpu} title="Training run unavailable" description="This run could not be loaded. Return to the experiment setup and start a run for a saved upload." />;

  const metrics = run.metrics || {};
  const metricCards = [
    ['Held-out test accuracy', 'accuracy'],
    ['Balanced accuracy', 'balanced_accuracy'],
    ['Sensitivity', 'sensitivity'],
    ['Specificity', 'specificity'],
    ['Precision', 'precision'],
    ['F1 score', 'f1_score'],
    ['ROC AUC', 'roc_auc'],
  ] as const;
  const confusion = metrics.confusion_matrix || {};
  const confusionEntries = [
    ['True positive', confusion.tp ?? confusion.true_positive],
    ['True negative', confusion.tn ?? confusion.true_negative],
    ['False positive', confusion.fp ?? confusion.false_positive],
    ['False negative', confusion.fn ?? confusion.false_negative],
  ];

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2"><span className="font-mono text-xs text-slate-500">Run {run.id}</span><StatusBadge status={run.status} size="sm" /></div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Training run results</h1>
          <p className="text-xs text-slate-500">Metrics are calculated from the held-out test partition of the selected upload.</p>
        </div>
        <div className="flex gap-2">
          {run.experiment_id && <Link to={`/experiments/${run.experiment_id}`} className="btn-secondary inline-flex items-center gap-2 text-xs"><BarChart3 className="h-4 w-4" />Experiment record</Link>}
          {run.status === 'completed' && <Link to={`/models/${run.model_id}`} className="btn-secondary inline-flex items-center gap-2 text-xs"><BarChart3 className="h-4 w-4" />Saved model metrics</Link>}
          <Link to="/predictions" className="btn-primary inline-flex items-center gap-2 text-xs"><Activity className="h-4 w-4" />Run prediction</Link>
        </div>
      </header>

      {run.status === 'running' && (
        <section className="card-scientific rounded-xl border border-brand-200 bg-brand-50 p-6 shadow-sm flex flex-col items-center justify-center text-center">
          <Activity className="h-10 w-10 text-brand-600 mb-3 animate-pulse" />
          <h2 className="text-lg font-bold text-brand-900">Training in Progress</h2>
          <p className="text-sm text-brand-700 mt-1 max-w-lg">
            Your quantum machine learning model is currently optimizing. Using maximum system resources, this intensive process may take some time for large datasets.
          </p>
          <div className="w-full max-w-md mt-6">
            <div className="flex justify-between text-xs font-semibold text-brand-800 mb-1.5">
              <span>Optimization Phase</span>
              <span className="animate-pulse">~45% Complete</span>
            </div>
            <div className="h-2.5 w-full bg-brand-200 rounded-full overflow-hidden">
              <div className="h-full bg-brand-600 rounded-full w-[45%] animate-pulse"></div>
            </div>
          </div>
        </section>
      )}

      <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="grid grid-cols-1 gap-3 text-xs sm:grid-cols-3">
          <div className="rounded-lg bg-slate-50 p-3"><span className="mb-1 flex items-center gap-2 text-slate-500"><Cpu className="h-4 w-4" />Model ID</span><span className="break-all font-mono">{run.model_id || 'Pending completion...'}</span></div>
          <div className="rounded-lg bg-slate-50 p-3"><span className="mb-1 flex items-center gap-2 text-slate-500"><Database className="h-4 w-4" />Dataset version</span><span className="break-all font-mono">{run.dataset_version_id}</span></div>
          <div className="rounded-lg bg-slate-50 p-3"><span className="mb-1 block text-slate-500">Target</span><span className="font-mono">{String(metrics.target_column || 'Pending completion...')}</span></div>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {metricCards.map(([label, key]) => <div key={key} className="rounded-lg border border-slate-200 p-4">
            <span className="block text-[11px] text-slate-500">{label}</span>
            <span className="mt-1 block text-xl font-bold text-slate-900">{typeof metrics[key] === 'number' ? key === 'roc_auc' ? metrics[key].toFixed(3) : `${(metrics[key] * 100).toFixed(1)}%` : 'Unavailable'}</span>
          </div>)}
        </div>
        <p className="text-[11px] text-slate-500">Held-out test rows: {typeof metrics.test_samples === 'number' ? metrics.test_samples : 'Unavailable'} · Training duration: {typeof metrics.training_duration_seconds === 'number' ? `${metrics.training_duration_seconds.toFixed(3)} seconds` : 'Unavailable'} · Positive class: {String(metrics.positive_class || 'Not recorded')} · ROC AUC is unavailable when the held-out partition contains one class.</p>
        {confusionEntries.some(([, value]) => typeof value === 'number') && <div>
          <h2 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-700">Held-out confusion matrix counts</h2>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">{confusionEntries.map(([label, value]) => <div key={String(label)} className="rounded-lg bg-slate-50 p-3 text-xs"><span className="block text-slate-500">{label}</span><b className="text-base text-slate-900">{typeof value === 'number' ? value : '—'}</b></div>)}</div>
        </div>}
      </section>

      <section className="card-scientific space-y-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Feature columns used</h2>
        {Array.isArray(metrics.selected_features) && metrics.selected_features.length ? <div className="flex flex-wrap gap-2">{metrics.selected_features.map((feature: string) => <span key={feature} className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 font-mono text-[11px] text-slate-700">{feature}</span>)}</div> : <p className="text-xs text-slate-500">This training record has no feature list.</p>}
        <div className="border-t border-slate-100 pt-3 text-[11px] text-slate-500">Preprocessing run: {run.preprocessing_run_id || 'Not recorded'} · Feature-selection run: {run.feature_selection_run_id || 'Not recorded'}</div>
      </section>

      <div className="flex justify-end"><Link to="/experiments" className="inline-flex items-center gap-2 text-xs font-semibold text-brand-800">All experiments<ArrowRight className="h-3.5 w-3.5" /></Link></div>
    </div>
  );
};
