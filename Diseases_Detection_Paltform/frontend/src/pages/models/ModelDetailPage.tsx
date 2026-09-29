import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Layers, Atom, BarChart3, ArrowRight, Activity } from 'lucide-react';
import { modelsApi } from '../../api';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { ErrorState } from '../../components/common/ErrorState';

const percent = (value: unknown) => typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : '—';

export const ModelDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: model, isLoading, error } = useQuery({
    queryKey: ['model', id],
    queryFn: () => (id ? modelsApi.get(id) : Promise.reject(new Error('Missing model ID'))),
    enabled: !!id,
  });

  if (isLoading) return <LoadingSkeleton rows={4} />;
  if (error || !model) return <ErrorState title="Model not found" message="Unable to load this saved model and its recorded experiment metrics." />;

  const config = model.configuration || {};
  const metrics = (config.metrics || model.versions?.[0]?.metrics) as Record<string, any> | undefined;
  const hasMetrics = typeof metrics?.accuracy === 'number';
  const isQuantum = model.model_type.toLowerCase() === 'vqc';
  const features = Array.isArray(config.selected_features) ? config.selected_features as string[] : [];
  const confusion = metrics?.confusion_matrix || {};
  const testSamples = metrics?.test_samples;
  const recordedExperiment = !!config.pretrained;
  const isTrainedOnUpload = !!config.dataset_version_id;
  const confusionEntries = [
    ['True positive', confusion.true_positive ?? confusion.tp],
    ['True negative', confusion.true_negative ?? confusion.tn],
    ['False positive', confusion.false_positive ?? confusion.fp],
    ['False negative', confusion.false_negative ?? confusion.fn],
  ];

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500"><Layers className="h-4 w-4 text-quantum-600" /><span className="font-mono">{model.id}</span><span>{model.model_type}</span><span>{recordedExperiment ? 'Experimental_ML checkpoint' : isTrainedOnUpload ? 'Trained on uploaded dataset' : 'Trainable template'}</span></div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">{model.name}</h1>
          <p className="text-xs text-slate-500">{model.description || 'No description is recorded for this model.'}</p>
        </div>
        <div className="flex gap-3">
          {model.status === 'trained' ? <Link to={`/predictions?model_id=${encodeURIComponent(model.id)}`} className="btn-primary flex items-center gap-2 text-xs"><Activity className="h-3.5 w-3.5" /><span>Use this model</span></Link> : <Link to="/training" className="btn-primary flex items-center gap-2 text-xs"><Activity className="h-3.5 w-3.5" /><span>Train on uploaded data</span></Link>}
          <Link to="/evaluation/comparison" className="btn-secondary flex items-center gap-2 text-xs"><BarChart3 className="h-3.5 w-3.5" /><span>Compare</span></Link>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Checkpoint details</h2>
          <div className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-3">
            <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Model type</span><b>{model.model_type}</b></div>
            <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Feature count</span><b>{features.length || config.feature_count || '—'}</b></div>
            <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Framework</span><b>{config.framework || (isQuantum ? 'PennyLane' : model.model_type.startsWith('svm_') ? 'scikit-learn' : '—')}</b></div>
            {isQuantum && <><div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Qubits</span><b>{config.n_qubits || config.feature_count || '—'}</b></div><div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Layers</span><b>{config.n_layers || '—'}</b></div><div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Noise</span><b>{config.noise_channels ? 'Simulated NISQ' : 'Noiseless'}</b></div></>}
            {config.target_column && <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Target column</span><b className="font-mono">{config.target_column}</b></div>}
            {config.dataset_version_id && <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Dataset version</span><b className="break-all font-mono">{config.dataset_version_id}</b></div>}
          </div>
          {features.length > 0 && <div><h3 className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">Selected feature order</h3><ol className="grid grid-cols-1 gap-2 sm:grid-cols-2">{features.map((feature, index) => <li key={feature} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs"><span className="mr-2 text-slate-400">{index + 1}.</span><span className="font-mono font-semibold">{feature}</span></li>)}</ol></div>}
          {config.source_experiment && <p className="break-all border-t border-slate-100 pt-3 text-[11px] text-slate-500">Loaded checkpoint: <span className="font-mono">{String(config.source_experiment)}</span></p>}
        </section>

        <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div><h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Recorded performance</h2><p className="mt-1 text-[11px] text-slate-500">{recordedExperiment ? `Original Experimental_ML holdout · ${testSamples ?? '—'} samples` : isTrainedOnUpload ? `This model's held-out test partition · ${testSamples ?? '—'} samples` : 'No evaluation exists until this template is trained.'}</p></div>
          {hasMetrics ? <div className="grid grid-cols-2 gap-3 text-xs">
            {[["Accuracy", metrics?.accuracy], ["Balanced accuracy", metrics?.balanced_accuracy], ["Sensitivity", metrics?.sensitivity], ["Specificity", metrics?.specificity], ["Precision", metrics?.precision], ["F1 score", metrics?.f1_score]].map(([label, value]) => <div key={String(label)} className="rounded-lg bg-slate-50 p-3"><span className="block text-[10px] text-slate-500">{label}</span><b className="text-base text-slate-900">{percent(value)}</b></div>)}
            <div className="col-span-2 rounded-lg bg-quantum-50 p-3"><span className="block text-[10px] text-quantum-700">ROC-AUC</span><b className="text-base text-quantum-900">{typeof metrics?.roc_auc === 'number' ? metrics.roc_auc.toFixed(4) : '—'}</b></div>
            {typeof metrics?.training_duration_seconds === 'number' && <p className="col-span-2 text-[11px] text-slate-500">Training time: {metrics.training_duration_seconds.toFixed(2)} seconds</p>}
          </div> : <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-xs text-slate-500">No measured values are recorded for this model yet.</div>}
          {hasMetrics && <div><h3 className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">Confusion matrix</h3><div className="grid grid-cols-2 gap-2">{confusionEntries.map(([label, value]) => <div key={String(label)} className="rounded-lg border border-slate-200 p-3 text-xs"><span className="block text-slate-500">{label}</span><b>{typeof value === 'number' ? value : '—'}</b></div>)}</div></div>}
          {recordedExperiment && config.pretrained_source_metrics && <div className="flex items-start gap-2 rounded-lg bg-slate-50 p-3 text-[11px] text-slate-600"><Atom className="mt-0.5 h-4 w-4 flex-shrink-0 text-quantum-600" />The stored experiment metrics remain the original checkpoint benchmark. Training a copy on an upload displays that new run’s separate held-out metrics.</div>}
        </section>
      </div>
      <div className="flex justify-end"><Link to="/models" className="inline-flex items-center gap-2 text-xs font-semibold text-brand-800">Back to model results<ArrowRight className="h-3.5 w-3.5" /></Link></div>
    </div>
  );
};
