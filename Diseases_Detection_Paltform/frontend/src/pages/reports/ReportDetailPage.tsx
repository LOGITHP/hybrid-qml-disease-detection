import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Printer } from 'lucide-react';
import { modelsApi } from '../../api';
import { Model } from '../../types';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { ErrorState } from '../../components/common/ErrorState';
import { MedicalNotice } from '../../components/common/MedicalNotice';

const percent = (value: unknown) => typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : '—';
const decimal = (value: unknown) => typeof value === 'number' ? value.toFixed(3) : '—';

const modelMetrics = (model: Model) => {
  const metrics = model.configuration?.metrics || model.versions?.[0]?.metrics;
  return metrics && typeof metrics.accuracy === 'number' ? metrics as Record<string, unknown> : undefined;
};

export const ReportDetailPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const { data: defaults, isLoading: defaultsLoading, error: defaultsError } = useQuery({
    queryKey: ['defaultModels'], queryFn: modelsApi.listDefaults,
  });
  const { data: userModels, isLoading: userModelsLoading, error: userModelsError } = useQuery({
    queryKey: ['userModels'], queryFn: modelsApi.list,
  });

  const isLoading = defaultsLoading || userModelsLoading;
  const error = defaultsError || userModelsError;
  const combined = [...(defaults || []), ...(userModels || [])];
  const models = combined
    .filter((model, index) => combined.findIndex((candidate) => candidate.id === model.id) === index)
    .filter((model) => !!modelMetrics(model));

  const handlePrint = () => window.print();

  if (isLoading) return <LoadingSkeleton rows={5} />;
  if (error) return <ErrorState title="Report unavailable" message="Could not load the saved model and evaluation records." />;

  return (
    <div className="mx-auto max-w-7xl space-y-6 print:p-0">
      <div className="flex items-center justify-between border-b border-slate-200 pb-4 print:hidden">
        <Link to="/reports" className="btn-secondary flex items-center space-x-1.5 text-xs">
          <ArrowLeft className="h-3.5 w-3.5" /><span>Back to Reports</span>
        </Link>
        <button onClick={handlePrint} className="btn-primary flex items-center space-x-1.5 text-xs">
          <Printer className="h-3.5 w-3.5" /><span>Print / Export PDF</span>
        </button>
      </div>

      <article className="card-scientific space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm md:p-10 print:border-none print:shadow-none print:p-0">
        <header className="space-y-2 border-b-2 border-slate-900 pb-5">
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs font-bold uppercase tracking-widest text-brand-800">Saved model performance report</span>
            <span className="font-mono text-xs text-slate-400">Ref: {reportId || 'model-results'}</span>
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">Experimental_ML checkpoints and uploaded-data training runs</h1>
          <p className="text-xs leading-relaxed text-slate-600">
            Values below come from the project’s recorded experiment metrics or from saved held-out evaluations for models trained on uploaded datasets. Templates without an evaluation are omitted.
          </p>
        </header>

        {!models.length ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-600">
            No saved model performance metrics are available yet. Load the Experimental_ML artifacts or train a model on an uploaded dataset to populate this report.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-[1120px] w-full text-left text-xs">
              <thead className="bg-slate-100 font-bold text-slate-700">
                <tr>
                  <th className="px-3 py-3">Model</th>
                  <th className="px-3 py-3">Data / evaluation</th>
                  <th className="px-3 py-3 text-right">Accuracy</th>
                  <th className="px-3 py-3 text-right">Balanced acc.</th>
                  <th className="px-3 py-3 text-right">Sensitivity</th>
                  <th className="px-3 py-3 text-right">Specificity</th>
                  <th className="px-3 py-3 text-right">Precision</th>
                  <th className="px-3 py-3 text-right">F1</th>
                  <th className="px-3 py-3 text-right">ROC-AUC</th>
                  <th className="px-3 py-3 text-right">Test rows</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-slate-700">
                {models.map((model) => {
                  const metrics = modelMetrics(model)!;
                  const config = model.configuration || {};
                  const source = config.pretrained ? 'Experimental_ML holdout' : config.dataset_version_id ? 'Uploaded data · held-out test' : 'Saved evaluation';
                  const features = Array.isArray(config.selected_features) ? config.selected_features as string[] : [];
                  return (
                    <tr key={model.id} className="align-top">
                      <td className="max-w-64 px-3 py-3 font-sans">
                        <Link to={`/models/${model.id}`} className="font-semibold text-brand-800 hover:underline">{model.name}</Link>
                        <span className="mt-1 block text-[10px] text-slate-500">{model.model_type}{features.length ? ` · ${features.length} features` : ''}</span>
                        {features.length > 0 && <span title={features.join(', ')} className="mt-1 block max-w-64 truncate font-mono text-[10px] text-slate-400">{features.join(', ')}</span>}
                      </td>
                      <td className="whitespace-nowrap px-3 py-3 font-sans">
                        <span>{source}</span>
                        {config.target_column && <span className="mt-1 block text-[10px] text-slate-500">Target: {String(config.target_column)}</span>}
                      </td>
                      <td className="px-3 py-3 text-right font-semibold">{percent(metrics.accuracy)}</td>
                      <td className="px-3 py-3 text-right">{percent(metrics.balanced_accuracy)}</td>
                      <td className="px-3 py-3 text-right">{percent(metrics.sensitivity)}</td>
                      <td className="px-3 py-3 text-right">{percent(metrics.specificity)}</td>
                      <td className="px-3 py-3 text-right">{percent(metrics.precision)}</td>
                      <td className="px-3 py-3 text-right">{percent(metrics.f1_score)}</td>
                      <td className="px-3 py-3 text-right">{decimal(metrics.roc_auc)}</td>
                      <td className="px-3 py-3 text-right">{typeof metrics.test_samples === 'number' ? metrics.test_samples : '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <p className="text-[11px] leading-relaxed text-slate-500">Metrics describe the saved test partitions associated with each row. Results across different datasets, targets, or feature sets are not directly comparable.</p>
        <MedicalNotice />
      </article>
    </div>
  );
};
