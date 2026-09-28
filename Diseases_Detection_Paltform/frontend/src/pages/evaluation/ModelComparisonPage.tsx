import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { BarChart3, Check, Layers } from 'lucide-react';
import { modelsApi } from '../../api';
import { ComprehensiveComparisonResponse } from '../../types';
import { EmptyState } from '../../components/common/EmptyState';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

export const ModelComparisonPage: React.FC = () => {
  const { data: models, isLoading } = useQuery({ queryKey: ['models'], queryFn: modelsApi.list });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComprehensiveComparisonResponse | null>(null);
  const datasetVersionId = sessionStorage.getItem('activeDatasetVersionId');
  const targetColumn = sessionStorage.getItem('activeTargetColumn');
  const selectedFeatures = (() => {
    try { return JSON.parse(sessionStorage.getItem('activeSelectedFeatures') || '[]') as string[]; }
    catch { return []; }
  })();
  const compatibleModels = (models || []).filter((model) => {
    const config = model.configuration || {};
    const modelFeatures = Array.isArray(config.selected_features) ? config.selected_features as string[] : [];
    return model.status === 'trained'
      && config.dataset_version_id === datasetVersionId
      && config.target_column === targetColumn
      && modelFeatures.length === selectedFeatures.length
      && modelFeatures.every((feature) => selectedFeatures.includes(feature));
  });
  const compareMutation = useMutation({
    mutationFn: modelsApi.compare,
    onSuccess: setComparison,
  });

  const toggleModel = (modelId: string) => {
    setSelectedIds((current) => current.includes(modelId)
      ? current.filter((id) => id !== modelId)
      : [...current, modelId]);
    setComparison(null);
  };

  if (isLoading) return <LoadingSkeleton rows={4} />;

  return (
    <div className="space-y-6">
      <header className="flex items-start gap-3 border-b border-slate-200 pb-4">
        <Layers className="mt-1 h-5 w-5 text-quantum-600" />
        <div><h1 className="text-2xl font-bold tracking-tight text-slate-900">Compare trained models</h1><p className="text-xs text-slate-500">Comparison uses saved held-out test metrics for models trained on the current upload, target, and feature set.</p></div>
      </header>

      {!datasetVersionId || !targetColumn || !selectedFeatures.length ? <EmptyState icon={BarChart3} title="No active experiment context" description="Select a dataset, target, and feature set before comparing training runs." /> : compatibleModels.length < 2 ? <EmptyState icon={BarChart3} title="Two compatible training runs are needed" description="Train at least two models on this same dataset version, target, and feature set to compare their actual held-out test results." /> : (
        <>
          <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="text-xs text-slate-600">Target: <span className="font-mono font-semibold">{targetColumn}</span> · Dataset version: <span className="font-mono">{datasetVersionId}</span></div>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {compatibleModels.map((model) => <label key={model.id} className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 text-xs ${selectedIds.includes(model.id) ? 'border-brand-800 bg-brand-50' : 'border-slate-200 hover:border-slate-300'}`}>
                <input type="checkbox" checked={selectedIds.includes(model.id)} onChange={() => toggleModel(model.id)} className="mt-0.5 accent-brand-800" />
                <span><span className="block font-bold text-slate-900">{model.name}</span><span className="block text-slate-500">{model.model_type} · {model.status}</span></span>
              </label>)}
            </div>
            {compareMutation.isError && <p className="text-xs text-red-700">{compareMutation.error instanceof Error ? compareMutation.error.message : 'Comparison failed.'}</p>}
            <button type="button" disabled={selectedIds.length < 2 || compareMutation.isPending} onClick={() => compareMutation.mutate(selectedIds)} className="btn-primary inline-flex items-center gap-2 text-xs disabled:cursor-not-allowed disabled:opacity-50"><BarChart3 className="h-4 w-4" />{compareMutation.isPending ? 'Comparing saved runs…' : `Compare ${selectedIds.length} selected model${selectedIds.length === 1 ? '' : 's'}`}</button>
          </section>

          {compareMutation.isPending && <LoadingSkeleton type="table" rows={5} />}
          {comparison && <section className="card-scientific space-y-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div><h2 className="text-sm font-bold text-slate-900">Held-out test comparison</h2><p className="mt-1 text-xs text-slate-500">{comparison.executive_summary} Differences are descriptive and do not establish statistical significance.</p></div>
            {Object.keys(comparison.category_winners).length > 0 && <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(comparison.category_winners).map(([metric, model]) => <div key={metric} className="rounded-lg bg-emerald-50 p-3 text-xs"><span className="block text-[10px] uppercase text-emerald-700">Best {metric}</span><span className="mt-1 flex items-center gap-1 font-bold text-emerald-900"><Check className="h-3 w-3" />{model}</span></div>)}</div>}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs"><thead className="border-b border-slate-200 bg-slate-50 text-slate-600"><tr><th className="px-3 py-2">Metric</th>{comparison.models_compared.map((model) => <th key={model.model_id} className="px-3 py-2 text-center">{model.model_name}</th>)}</tr></thead>
                <tbody className="divide-y divide-slate-100">{comparison.comparison_matrix.map((row) => <tr key={row.metric_key}><td className="px-3 py-2 font-semibold text-slate-700">{row.display_name}</td>{comparison.models_compared.map((model) => {
                  const value = row.values[model.model_name];
                  return <td key={model.model_id} className="px-3 py-2 text-center font-mono">{typeof value === 'number' ? (row.metric_key === 'training_duration_sec' ? `${value.toFixed(3)} s` : `${(value * 100).toFixed(1)}%`) : 'N/A'}</td>;
                })}</tr>)}</tbody>
              </table>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">{String(comparison.cml_vs_qml_insights.interpretation || '')}{typeof comparison.cml_vs_qml_insights.classical_mean_accuracy === 'number' && ` Classical mean accuracy: ${(comparison.cml_vs_qml_insights.classical_mean_accuracy * 100).toFixed(1)}%.`}{typeof comparison.cml_vs_qml_insights.quantum_mean_accuracy === 'number' && ` Quantum mean accuracy: ${(comparison.cml_vs_qml_insights.quantum_mean_accuracy * 100).toFixed(1)}%.`}</div>
          </section>}
        </>
      )}
    </div>
  );
};
