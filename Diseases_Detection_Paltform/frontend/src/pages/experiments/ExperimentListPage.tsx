import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { FlaskConical, Plus, ArrowRight } from 'lucide-react';
import { experimentsApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { EmptyState } from '../../components/common/EmptyState';

export const ExperimentListPage: React.FC = () => {
  const { data: experiments, isLoading, isError } = useQuery({
    queryKey: ['experiments'],
    queryFn: experimentsApi.list,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <FlaskConical className="w-4 h-4 text-quantum-600" />
            <span>Research & Reproducibility</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Dataset-driven Experiments</h1>
          <p className="text-xs text-slate-500">Training runs are linked to their uploaded version, target, preprocessing, and feature-selection choices.</p>
        </div>
        <Link to="/training" className="btn-primary text-xs flex items-center space-x-2 self-start sm:self-auto">
          <Plus className="w-4 h-4" />
          <span>Train a Model</span>
        </Link>
      </div>

      {isLoading ? <LoadingSkeleton type="table" rows={3} /> : isError ? (
        <EmptyState icon={FlaskConical} title="Experiments unavailable" description="The experiment service could not load saved training runs." />
      ) : !experiments?.length ? (
        <EmptyState icon={FlaskConical} title="No training runs yet" description="Complete preprocessing, select features, and train a model. Its experiment record will appear here." />
      ) : (
        <div className="card-scientific bg-white border border-slate-200 rounded-xl overflow-hidden p-0 shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-6">Experiment</th>
                <th className="py-3 px-6">Tags</th>
                <th className="py-3 px-6">Training Runs</th>
                <th className="py-3 px-6">State</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {experiments.map((experiment) => (
                <tr key={experiment.id} className="hover:bg-slate-50/70">
                  <td className="py-4 px-6">
                    <div className="font-semibold text-slate-900">{experiment.name}</div>
                    <div className="text-[11px] text-slate-400 line-clamp-1">
                      {experiment.dataset_name || 'Uploaded dataset'} · {experiment.target_column || 'target not recorded'} · {experiment.selected_features?.length || 0} selected features
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex flex-wrap gap-1">
                      {(experiment.tags || []).map((tag) => <span key={tag} className="badge bg-slate-100 text-slate-600 border border-slate-200 text-[10px]">{tag}</span>)}
                    </div>
                  </td>
                  <td className="py-4 px-6 font-medium text-slate-800">{(experiment.training_run_ids || []).length}</td>
                  <td className="py-4 px-6"><StatusBadge status={experiment.status} size="sm" /></td>
                  <td className="py-4 px-6 text-right">
                    <Link to={`/experiments/${experiment.id}`} className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold inline-flex items-center space-x-1">
                      <span>Inspect Run</span><ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
