import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQueries, useQuery } from '@tanstack/react-query';
import { FlaskConical, Database, Sliders, Filter, Cpu, ArrowRight } from 'lucide-react';
import { datasetsApi, experimentsApi, modelsApi, trainingApi } from '../../api';
import { EmptyState } from '../../components/common/EmptyState';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { StatusBadge } from '../../components/common/StatusBadge';

export const ExperimentDetailPage: React.FC = () => {
  const { experimentId } = useParams<{ experimentId: string }>();
  const { data: experiment, isLoading, isError } = useQuery({
    queryKey: ['experiment', experimentId],
    queryFn: () => (experimentId ? experimentsApi.get(experimentId) : Promise.reject(new Error('Missing experiment ID'))),
    enabled: !!experimentId,
  });
  const { data: dataset } = useQuery({
    queryKey: ['dataset', experiment?.dataset_id],
    queryFn: () => (experiment?.dataset_id ? datasetsApi.get(experiment.dataset_id) : Promise.reject(new Error('No dataset'))),
    enabled: !!experiment?.dataset_id,
  });
  const version = dataset?.versions?.find((item) => item.id === experiment?.dataset_version_id);
  const { data: analysis } = useQuery({
    queryKey: ['datasetAnalysis', dataset?.id, version?.id],
    queryFn: () => (dataset?.id && version ? datasetsApi.analyzeVersion(dataset.id, version.id) : Promise.reject(new Error('No dataset version'))),
    enabled: !!dataset?.id && !!version,
  });
  const runQueries = useQueries({
    queries: (experiment?.training_run_ids || []).map((runId) => ({
      queryKey: ['trainingRun', runId],
      queryFn: () => trainingApi.getStatus(runId),
      enabled: !!runId,
    })),
  });
  const { data: models } = useQuery({ queryKey: ['models'], queryFn: modelsApi.list });

  if (isLoading) return <LoadingSkeleton rows={4} />;
  if (isError || !experiment) return <EmptyState icon={FlaskConical} title="Experiment not found" description="No saved dataset-driven training run matches this experiment ID." />;

  const stages = [
    {
      title: 'Uploaded dataset',
      description: `${experiment.dataset_name || dataset?.name || 'Dataset'} · ${analysis?.row_count ?? version?.row_count ?? '—'} rows · ${analysis?.column_count ?? version?.column_count ?? '—'} columns · ${version?.version_tag || 'version unavailable'}`,
      artifact: analysis?.file_metadata?.filename || 'Original uploaded file',
      Icon: Database,
    },
    {
      title: 'Preprocessing',
      description: experiment.preprocessing_run_id ? 'Saved training-only imputation, encoding, scaling, and split configuration.' : 'No saved preprocessing run was linked to this record.',
      artifact: experiment.preprocessing_run_id || 'Not recorded',
      Icon: Sliders,
    },
    {
      title: 'Feature selection',
      description: `Target: ${experiment.target_column || '—'} · ${experiment.selected_features?.length || 0} feature columns selected`,
      artifact: experiment.selected_features?.length ? experiment.selected_features.join(', ') : experiment.feature_selection_run_id || 'No feature set recorded',
      Icon: Filter,
    },
    ...runQueries.map((query, index) => {
      const run = query.data;
      const model = models?.find((entry) => entry.id === run?.model_id);
      const metrics = run?.metrics;
      return {
        title: `Training run ${index + 1}${model ? ` · ${model.name}` : ''}`,
        description: run ? `Status: ${run.status}${metrics ? ` · held-out test accuracy ${(Number(metrics.accuracy) * 100).toFixed(1)}%` : ''}` : 'Training run details are unavailable.',
        artifact: run?.id || experiment.training_run_ids?.[index] || 'Loading run',
        Icon: Cpu,
      };
    }),
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-mono text-xs text-slate-400">ID: {experiment.id}</span>
            <StatusBadge status={experiment.status} size="sm" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">{experiment.name}</h1>
          <p className="text-xs text-slate-500">{experiment.description || 'Saved data and model provenance for this training run.'}</p>
        </div>
        <Link to="/experiments" className="btn-secondary text-xs inline-flex items-center gap-2"><ArrowRight className="w-3.5 h-3.5 rotate-180" />Back to Experiments</Link>
      </div>

      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-8 shadow-sm space-y-7">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Recorded Pipeline</h2>
        <div className="relative border-l-2 border-slate-200 ml-4 pl-6 space-y-6">
          {stages.map((stage, index) => {
            const Icon = stage.Icon;
            return (
              <div key={`${stage.title}-${index}`} className="relative">
                <div className="absolute -left-[35px] top-0.5 w-6 h-6 rounded-full bg-brand-800 text-white flex items-center justify-center ring-4 ring-white"><Icon className="w-3.5 h-3.5" /></div>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-slate-900">{index + 1}. {stage.title}</span>
                    <span className="text-[10px] font-mono text-slate-400 break-all text-right">{stage.artifact}</span>
                  </div>
                  <p className="text-xs text-slate-600">{stage.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
