import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Layers,
  BarChart3,
  Award,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Atom,
  Clock,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';
import { modelsApi } from '../../api';
import { ComprehensiveComparisonResponse } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

export const ModelComparisonPage: React.FC = () => {
  const [selectedIds, setSelectedIds] = useState<string[]>([
    'pretrained-cml-svm-linear-4',
    'pretrained-cml-svm-rbf-4',
    'pretrained-qml-vqc-4-noiseless',
  ]);

  const { data: defaultModels, isLoading: modelsLoading } = useQuery({
    queryKey: ['defaultModels'],
    queryFn: modelsApi.listDefaults,
  });

  const compareMutation = useMutation({
    mutationFn: async (ids: string[]) => {
      return await modelsApi.compare(ids);
    },
  });

  useEffect(() => {
    if (selectedIds.length >= 2) {
      compareMutation.mutate(selectedIds);
    }
  }, [selectedIds]);

  const handleToggleModel = (modelId: string) => {
    if (selectedIds.includes(modelId)) {
      if (selectedIds.length <= 2) return; // Keep minimum 2
      setSelectedIds(selectedIds.filter((id) => id !== modelId));
    } else {
      setSelectedIds([...selectedIds, modelId]);
    }
  };

  const comparison = compareMutation.data;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="pb-4 border-b border-slate-200">
        <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
          <Layers className="w-4 h-4 text-quantum-600" />
          <span>Multi-Model Comparative Benchmarking</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Classical ML vs Hybrid Quantum ML Comparison
        </h1>
        <p className="text-xs text-slate-500">
          Side-by-side performance evaluation on identical clinical partitions and canonical features
        </p>
      </div>

      {/* Model Selection Checkbox Bar */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Select Models to Compare (Select 2 or more)
          </span>
          <span className="text-xs font-semibold text-brand-800 bg-brand-50 px-2.5 py-0.5 rounded border border-brand-200">
            {selectedIds.length} Models Active
          </span>
        </div>

        {modelsLoading ? (
          <div className="h-10 animate-pulse bg-slate-100 rounded-lg"></div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {defaultModels?.map((m) => {
              const isChecked = selectedIds.includes(m.id);
              const isQML = m.model_type === 'VQC';
              return (
                <div
                  key={m.id}
                  onClick={() => handleToggleModel(m.id)}
                  className={`p-3 rounded-lg border cursor-pointer text-xs transition-all flex flex-col justify-between ${
                    isChecked
                      ? isQML
                        ? 'border-quantum-600 bg-quantum-50/70 text-quantum-950 font-bold shadow-sm'
                        : 'border-brand-800 bg-brand-50/70 text-brand-950 font-bold shadow-sm'
                      : 'border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="truncate">{m.name}</span>
                    <input
                      type="checkbox"
                      checked={isChecked}
                      readOnly
                      className="accent-brand-800 ml-1.5"
                    />
                  </div>
                  <span className="text-[10px] text-slate-400 capitalize">{m.model_type}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Comparison Loading or Content */}
      {compareMutation.isPending && !comparison ? (
        <LoadingSkeleton type="table" rows={6} />
      ) : !comparison ? (
        <div className="card-scientific text-center py-10 text-xs text-slate-500">
          Select at least two models above to view the comparative benchmark.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Winners Callout Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card-scientific bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center space-x-3">
              <div className="p-2.5 bg-emerald-100 rounded-xl text-emerald-700 flex-shrink-0">
                <Award className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Best Accuracy
                </span>
                <span className="text-xs font-bold text-slate-900 block truncate">
                  {comparison.best_performer.by_accuracy}
                </span>
              </div>
            </div>

            <div className="card-scientific bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center space-x-3">
              <div className="p-2.5 bg-brand-100 rounded-xl text-brand-700 flex-shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Best Sensitivity (Screening)
                </span>
                <span className="text-xs font-bold text-slate-900 block truncate">
                  {comparison.best_performer.by_sensitivity_recall}
                </span>
              </div>
            </div>

            <div className="card-scientific bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center space-x-3">
              <div className="p-2.5 bg-quantum-100 rounded-xl text-quantum-700 flex-shrink-0">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Best F1-Score
                </span>
                <span className="text-xs font-bold text-slate-900 block truncate">
                  {comparison.best_performer.by_f1_score}
                </span>
              </div>
            </div>

            <div className="card-scientific bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center space-x-3">
              <div className="p-2.5 bg-indigo-100 rounded-xl text-indigo-700 flex-shrink-0">
                <TrendingUp className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Best ROC-AUC
                </span>
                <span className="text-xs font-bold text-slate-900 block truncate">
                  {comparison.best_performer.by_roc_auc}
                </span>
              </div>
            </div>
          </div>

          {/* Full Metrics Comparison Table */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl overflow-hidden p-0 shadow-sm">
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Exhaustive Evaluation Metrics Matrix
              </h3>
              <span className="text-[11px] text-slate-500 font-mono">
                {comparison.models_compared_count} Models Benchmarked
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100/70 text-slate-700 font-semibold border-b border-slate-200 text-[11px]">
                  <tr>
                    <th className="py-3 px-6">Evaluation Metric</th>
                    {comparison.models.map((m) => (
                      <th key={m.model_id} className="py-3 px-6 text-center font-bold">
                        <div className="truncate max-w-[160px] mx-auto">{m.model_name}</div>
                        <span className="text-[10px] font-normal text-slate-400 block font-mono">
                          {m.model_type}
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800">
                  {comparison.metrics_matrix.map((row) => (
                    <tr key={row.metric_name} className="hover:bg-slate-50/70">
                      <td className="py-3 px-6 font-semibold text-slate-900 flex items-center space-x-1.5">
                        <span>{row.metric_name}</span>
                        {row.unit && (
                          <span className="text-[10px] text-slate-400 font-mono">({row.unit})</span>
                        )}
                      </td>
                      {comparison.models.map((m) => {
                        const val = row.values[m.model_id];
                        const isScore = row.unit !== 's';
                        return (
                          <td key={m.model_id} className="py-3 px-6 text-center font-mono font-medium">
                            {isScore ? `${(val * 100).toFixed(1)}%` : `${val.toFixed(2)}s`}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Confusion Matrix Side-by-Side Comparison */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Confusion Matrix Cross-Comparison
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {comparison.models.map((m) => (
                <div key={m.model_id} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                  <div className="flex items-center justify-between pb-1 border-b border-slate-200">
                    <span className="font-bold text-xs text-slate-900 truncate">{m.model_name}</span>
                    <span className="text-[10px] font-mono text-slate-400">{m.model_type}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-center text-xs pt-1">
                    <div className="p-2 bg-emerald-50 rounded border border-emerald-200">
                      <span className="text-[9px] text-emerald-800 block">TP</span>
                      <span className="font-bold text-emerald-900 font-mono">{m.confusion_matrix.tp}</span>
                    </div>
                    <div className="p-2 bg-red-50 rounded border border-red-200">
                      <span className="text-[9px] text-red-800 block">FN</span>
                      <span className="font-bold text-red-900 font-mono">{m.confusion_matrix.fn}</span>
                    </div>
                    <div className="p-2 bg-amber-50 rounded border border-amber-200">
                      <span className="text-[9px] text-amber-800 block">FP</span>
                      <span className="font-bold text-amber-900 font-mono">{m.confusion_matrix.fp}</span>
                    </div>
                    <div className="p-2 bg-emerald-50 rounded border border-emerald-200">
                      <span className="text-[9px] text-emerald-800 block">TN</span>
                      <span className="font-bold text-emerald-900 font-mono">{m.confusion_matrix.tn}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CML vs QML Benchmark Insights */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
            <div className="flex items-center space-x-2 text-brand-900 font-bold text-xs uppercase tracking-wider">
              <Atom className="w-4 h-4 text-quantum-600" />
              <span>CML vs QML Comparative Insights</span>
            </div>
            <ul className="space-y-2 text-xs text-slate-600 list-disc pl-5 leading-relaxed">
              {comparison.cml_vs_qml_insights.map((insight, idx) => (
                <li key={idx}>{insight}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
