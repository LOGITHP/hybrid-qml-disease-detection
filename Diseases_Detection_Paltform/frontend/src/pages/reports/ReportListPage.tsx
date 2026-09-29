import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, FileText } from 'lucide-react';
import { modelsApi } from '../../api';
import { Model } from '../../types';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

const hasPerformance = (model: Model) => {
  const metrics = model.configuration?.metrics || model.versions?.[0]?.metrics;
  return typeof metrics?.accuracy === 'number';
};

export const ReportListPage: React.FC = () => {
  const { data: defaults, isLoading: defaultsLoading } = useQuery({
    queryKey: ['defaultModels'], queryFn: modelsApi.listDefaults,
  });
  const { data: userModels, isLoading: userModelsLoading } = useQuery({
    queryKey: ['userModels'], queryFn: modelsApi.list,
  });

  const combined = [...(defaults || []), ...(userModels || [])];
  const models = combined.filter((model, index) => combined.findIndex((candidate) => candidate.id === model.id) === index);
  const measured = models.filter(hasPerformance);
  const checkpoints = measured.filter((model) => model.configuration?.pretrained).length;
  const trainedRuns = measured.filter((model) => !!model.configuration?.dataset_version_id).length;

  if (defaultsLoading || userModelsLoading) return <LoadingSkeleton rows={3} />;

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <div className="mb-1 flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-brand-700">
          <FileText className="h-4 w-4 text-quantum-600" /><span>Saved evaluation results</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Model performance report</h1>
        <p className="text-xs text-slate-500">Source checkpoint results and held-out performance for models trained on your uploaded datasets.</p>
      </div>

      <article className="card-scientific flex flex-col justify-between space-y-5 rounded-xl border border-slate-200 bg-white p-6 shadow-sm md:flex-row md:items-center">
        <div className="space-y-2">
          <span className="badge bg-slate-100 text-[10px] text-slate-700">Generated from saved model metrics</span>
          <h2 className="text-base font-bold text-slate-900">Experimental_ML checkpoints and your training runs</h2>
          <p className="text-xs text-slate-500">{measured.length} model results · {checkpoints} experiment checkpoints · {trainedRuns} uploaded-data training runs</p>
        </div>
        <Link to="/reports/model-performance" className="btn-primary flex shrink-0 items-center space-x-1.5 text-xs">
          <span>View performance report</span><ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </article>

      {!measured.length && <p className="text-xs text-slate-500">No saved metrics yet. Experiment checkpoints appear when their source artifacts are loaded; upload a dataset and train a model to add a measured run.</p>}
    </div>
  );
};
