import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Layers, Atom, BarChart3, ArrowRight, Activity, Database, Sparkles, Box } from 'lucide-react';
import { modelsApi } from '../../api';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { ErrorState } from '../../components/common/ErrorState';
import { StatusBadge } from '../../components/common/StatusBadge';

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
  const sourceMetrics = config.pretrained_source_metrics as Record<string, any> | undefined;
  const hasMetrics = typeof metrics?.accuracy === 'number';
  const isQuantum = model.model_type.toLowerCase() === 'vqc';
  const features = Array.isArray(config.selected_features) ? config.selected_features as string[] : [];
  const confusion = metrics?.confusion_matrix || {};
  const testSamples = metrics?.test_samples;
  const recordedExperiment = !!config.pretrained;
  const isCheckpointEvaluation = !!config.pretrained_used;

  const confusionEntries = [
    ['True Positive', confusion.true_positive ?? confusion.tp],
    ['True Negative', confusion.true_negative ?? confusion.tn],
    ['False Positive', confusion.false_positive ?? confusion.fp],
    ['False Negative', confusion.false_negative ?? confusion.fn],
  ];

  return (
    <div className="space-y-6">
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">ID: {model.id.split('-')[0]}...</span>
            <StatusBadge status={model.model_type} size="sm" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-2 py-0.5 rounded">
              {recordedExperiment ? 'Pretrained Checkpoint' : isCheckpointEvaluation ? 'Checkpoint Evaluation' : model.status === 'candidate' ? 'Review Candidate' : 'Trained Model'}
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">{model.name}</h1>
          <p className="text-sm text-slate-500 mt-1 max-w-2xl leading-relaxed">{model.description || 'No description is recorded for this model.'}</p>
        </div>
        <div className="flex items-center gap-3">
          {recordedExperiment ? (
            <Link to={`/training?model_id=${encodeURIComponent(model.id)}`} className="btn-primary flex items-center gap-2 px-5 py-2.5 font-semibold shadow-md hover:shadow-lg transition-all">
              <Activity className="h-4 w-4" /><span>Evaluate on upload</span>
            </Link>
          ) : model.status === 'trained' ? (
            <>
              <Link to={`/predictions?model_id=${encodeURIComponent(model.id)}`} className="btn-primary flex items-center gap-2 px-5 py-2.5 font-semibold shadow-md hover:shadow-lg transition-all">
                <Activity className="h-4 w-4" /><span>Use for Prediction</span>
              </Link>
              <Link to="/evaluation/comparison" className="btn-secondary flex items-center gap-2 px-4 py-2.5">
                <BarChart3 className="h-4 w-4" /><span>Compare</span>
              </Link>
            </>
          ) : null}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Model Details */}
        <div className="lg:col-span-2 space-y-8">

          {/* Lineage Card */}
          <section className="card-scientific space-y-5 rounded-2xl border border-slate-200 bg-white p-6 md:p-8 shadow-sm">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <Box className="w-5 h-5 text-brand-600" /> Model Configuration
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="rounded-xl bg-slate-50 border border-slate-100 p-4">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">Model Type</span>
                <b className="text-sm text-slate-900">{model.model_type}</b>
              </div>
              <div className="rounded-xl bg-slate-50 border border-slate-100 p-4">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">Feature Count</span>
                <b className="text-sm text-slate-900">{features.length || config.feature_count || '—'}</b>
              </div>
              <div className="rounded-xl bg-slate-50 border border-slate-100 p-4">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">Framework</span>
                <b className="text-sm text-slate-900">{config.framework || (isQuantum ? 'PennyLane' : model.model_type.startsWith('svm_') ? 'scikit-learn' : '—')}</b>
              </div>
              {recordedExperiment && (
                <div className="rounded-xl bg-brand-50 border border-brand-100 p-4 col-span-2 sm:col-span-3">
                  <span className="block text-[10px] font-bold uppercase tracking-wider text-brand-600 mb-1 flex items-center gap-1"><Database className="w-3 h-3"/> Dataset</span>
                  <b className="text-xs text-brand-900 break-all">Lung Cancer Survey (V1)</b>
                </div>
              )}
            </div>
          </section>

          {/* Features Card */}
          {features.length > 0 && (
            <section className="card-scientific space-y-4 rounded-2xl border border-slate-200 bg-white p-6 md:p-8 shadow-sm">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-emerald-600" /> Input Features
              </h2>
              <ol className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {features.map((feature, index) => (
                  <li key={feature} className="flex items-center rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm transition-colors hover:border-emerald-300 hover:bg-emerald-50/50">
                    <span className="w-6 font-bold text-slate-400 text-xs">{index + 1}.</span>
                    <span className="font-mono font-medium text-slate-800">{feature}</span>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {/* Quantum Circuit Card */}
          {isQuantum && (
            <section className="card-scientific space-y-4 rounded-2xl border border-quantum-200 bg-gradient-to-br from-white to-quantum-50/30 p-6 md:p-8 shadow-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <Atom className="w-32 h-32 text-quantum-600" />
              </div>
              <h2 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-quantum-900 relative z-10">
                <Atom className="h-5 w-5" /> Quantum Circuit Topology
              </h2>
              {config.pretrained ? (
                <div className="text-sm text-slate-600 bg-white/80 p-4 rounded-xl border border-quantum-100 relative z-10">
                  <p><strong>{config.n_qubits || config.feature_count || '—'} Qubits</strong> · <strong>{config.n_layers || '—'} Layers</strong></p>
                  <p className="text-xs text-slate-500 mt-1">Source circuit details are locked to the registered checkpoint metadata.</p>
                </div>
              ) : config.quantum_config ? (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 relative z-10">
                    {[
                      ['Encoding', config.quantum_config.encoding_method],
                      ['Trainable Gate', config.quantum_config.variational_gate],
                      ['Entanglement', config.quantum_config.entanglement_strategy],
                      ['Backend', config.quantum_config.backend_type],
                      ['Qubits', config.quantum_config.n_qubits],
                      ['Layers', config.quantum_config.n_layers]
                    ].map(([label, value]) => (
                      <div key={String(label)} className="rounded-xl bg-white/90 border border-quantum-100 p-3 shadow-sm">
                        <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">{label}</span>
                        <b className="text-xs text-quantum-900">{String(value || '—')}</b>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-sm text-slate-500 relative z-10">No circuit configuration was saved.</p>
              )}
            </section>
          )}

        </div>

        {/* Right Column: Performance */}
        <div className="space-y-6">
          <section className="card-scientific space-y-6 rounded-2xl border border-slate-200 bg-white p-6 md:p-8 shadow-md">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800">Recorded Performance</h2>
              <p className="mt-1.5 text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                {recordedExperiment ? `Original checkpoint benchmark · ${testSamples ?? '—'} samples` : isCheckpointEvaluation ? `Uploaded dataset evaluation · held-out test · ${testSamples ?? '—'} samples` : `Held-out test partition · ${testSamples ?? '—'} samples`}
              </p>
            </div>

            {hasMetrics ? (
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  {[
                    ["Accuracy", metrics?.accuracy, "text-emerald-700", "bg-emerald-50", "border-emerald-100"],
                    ["Balanced Acc", metrics?.balanced_accuracy, "text-slate-800", "bg-slate-50", "border-slate-100"],
                    ["Sensitivity", metrics?.sensitivity, "text-slate-800", "bg-slate-50", "border-slate-100"],
                    ["Specificity", metrics?.specificity, "text-slate-800", "bg-slate-50", "border-slate-100"],
                    ["Precision", metrics?.precision, "text-slate-800", "bg-slate-50", "border-slate-100"],
                    ["F1 Score", metrics?.f1_score, "text-slate-800", "bg-slate-50", "border-slate-100"]
                  ].map(([label, value, textColor, bgColor, borderColor]) => (
                    <div key={String(label)} className={`rounded-xl border ${borderColor} ${bgColor} p-4`}>
                      <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">{label}</span>
                      <b className={`text-xl ${textColor}`}>{percent(value)}</b>
                    </div>
                  ))}

                  <div className="col-span-2 rounded-xl border border-quantum-200 bg-quantum-50 p-4 flex items-center justify-between">
                    <span className="block text-xs font-bold uppercase tracking-wider text-quantum-700">ROC-AUC Score</span>
                    <b className="text-2xl text-quantum-900">{typeof metrics?.roc_auc === 'number' ? metrics.roc_auc.toFixed(4) : '—'}</b>
                  </div>
                </div>

                {confusionEntries.some(([_, val]) => typeof val === 'number') && (
                  <div className="pt-2 border-t border-slate-100">
                    <h3 className="mb-3 text-[10px] font-bold uppercase tracking-wider text-slate-500">Confusion Matrix</h3>
                    <div className="grid grid-cols-2 gap-3">
                      {confusionEntries.map(([label, value]) => (
                        <div key={String(label)} className="rounded-lg bg-slate-50 p-3 text-center border border-slate-100">
                          <b className="text-lg text-slate-800 block">{typeof value === 'number' ? value : '—'}</b>
                          <span className="text-[10px] uppercase tracking-wider text-slate-500 mt-1">{label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
                No performance metrics recorded.
              </div>
            )}
          </section>
          {isCheckpointEvaluation && sourceMetrics && (
            <section className="card-scientific space-y-3 rounded-2xl border border-indigo-200 bg-indigo-50/50 p-5">
              <div>
                <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-900">Source checkpoint metrics</h2>
                <p className="mt-1 text-[10px] text-indigo-800">Original benchmark · {String(sourceMetrics.test_samples ?? '—')} samples. Kept separate from the upload evaluation above.</p>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {[
                  ['Accuracy', sourceMetrics.accuracy],
                  ['Balanced accuracy', sourceMetrics.balanced_accuracy],
                  ['Sensitivity', sourceMetrics.sensitivity],
                  ['Specificity', sourceMetrics.specificity],
                  ['Precision', sourceMetrics.precision],
                  ['F1 score', sourceMetrics.f1_score],
                ].map(([label, value]) => <div key={String(label)} className="rounded-lg border border-indigo-100 bg-white p-2"><span className="block text-[10px] text-slate-500">{String(label)}</span><b>{percent(value)}</b></div>)}
                <div className="col-span-2 flex justify-between rounded-lg border border-indigo-100 bg-white p-2"><span className="text-[10px] text-slate-500">ROC-AUC</span><b>{typeof sourceMetrics.roc_auc === 'number' ? sourceMetrics.roc_auc.toFixed(4) : '—'}</b></div>
              </div>
            </section>
          )}
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <Link to="/models" className="inline-flex items-center gap-2 text-sm font-semibold text-brand-700 hover:text-brand-900 transition-colors">
          Back to Configuration <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
};
