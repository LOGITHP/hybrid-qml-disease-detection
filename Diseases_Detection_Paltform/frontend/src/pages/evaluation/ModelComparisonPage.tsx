import React, { useState, useMemo } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { BarChart3, CheckSquare, Layers, Square } from 'lucide-react';
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
  LineChart as RechartsLineChart,
  Line,
} from 'recharts';
import { modelsApi, datasetsApi, evaluationApi } from '../../api';
import { ComprehensiveComparisonResponse, Model } from '../../types';
import { EmptyState } from '../../components/common/EmptyState';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { StatusBadge } from '../../components/common/StatusBadge';

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6366f1', '#ec4899'];

// ─── helpers ──────────────────────────────────────────────────────────────────
function datasetLabel(name: string | undefined, tag: string | undefined) {
  return name ? `${name} (${tag || 'v1.0'})` : tag || '—';
}

function modelBadge(m: Model) {
  if (m.model_type === 'vqc') return 'VQC';
  if (m.model_type === 'svm_rbf') return 'SVM RBF';
  if (m.model_type === 'svm_linear') return 'SVM Linear';
  return m.model_type?.toUpperCase() ?? '—';
}

// ─── component ────────────────────────────────────────────────────────────────
export const ModelComparisonPage: React.FC = () => {
  // ── data fetching ──────────────────────────────────────────────────────────
  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ['models-comparison'],
    queryFn: modelsApi.list,
  });
  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets-comparison'],
    queryFn: datasetsApi.list,
  });

  // ── filter state ───────────────────────────────────────────────────────────
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  const [selectedTarget, setSelectedTarget] = useState<string>('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComprehensiveComparisonResponse | null>(null);
  const [evalContexts, setEvalContexts] = useState<any[]>([]);
  const [isLoadingContexts, setIsLoadingContexts] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);

  // ── derive dataset+version flat list ──────────────────────────────────────
  const versionOptions = useMemo(() => {
    const out: { versionId: string; label: string; datasetName: string }[] = [];
    for (const ds of datasets || []) {
      for (const v of ds.versions || []) {
        out.push({
          versionId: v.id,
          label: datasetLabel(ds.name, v.version_tag),
          datasetName: ds.name,
        });
      }
    }
    return out;
  }, [datasets]);

  // ── derive target columns available for the chosen version ─────────────────
  const targetOptions = useMemo(() => {
    if (!selectedVersionId || !models) return [];
    const targets = new Set<string>();
    for (const m of models) {
      const cfg = m.configuration || {};
      const mvid = cfg.dataset_version_id as string | undefined;
      const tc = cfg.target_column as string | undefined;
      if (mvid === selectedVersionId && tc) targets.add(tc);
    }
    return [...targets].sort();
  }, [selectedVersionId, models]);

  // ── auto-select target if only one available ───────────────────────────────
  React.useEffect(() => {
    if (targetOptions.length === 1) setSelectedTarget(targetOptions[0]);
    else setSelectedTarget('');
  }, [targetOptions]);

  // ── models compatible with current filter ─────────────────────────────────
  const compatibleModels = useMemo(() => {
    if (!models || !selectedVersionId) return [];
    return models.filter((m) => {
      if (m.status !== 'trained') return false;
      const cfg = m.configuration || {};
      return (
        cfg.dataset_version_id === selectedVersionId &&
        (!selectedTarget || cfg.target_column === selectedTarget)
      );
    });
  }, [models, selectedVersionId, selectedTarget]);

  // auto-select all compatible models when filter changes
  React.useEffect(() => {
    setSelectedIds(compatibleModels.map((m) => m.id));
    setComparison(null);
    setEvalContexts([]);
    setCompareError(null);
  }, [compatibleModels]);

  const toggleModel = (id: string) => {
    setSelectedIds((cur) =>
      cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]
    );
    setComparison(null);
    setEvalContexts([]);
    setCompareError(null);
  };

  const toggleAll = () => {
    if (selectedIds.length === compatibleModels.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(compatibleModels.map((m) => m.id));
    }
    setComparison(null);
  };

  // ── comparison mutation ────────────────────────────────────────────────────
  const compareMutation = useMutation({
    mutationFn: () => modelsApi.compare(selectedIds),
    onSuccess: async (data) => {
      setComparison(data);
      setCompareError(null);
      if (data.models_compared) {
        setIsLoadingContexts(true);
        try {
          const runIds = data.models_compared
            .map((m) => models?.find((mod) => mod.id === m.model_id)?.training_run_id)
            .filter(Boolean) as string[];
          const contexts = await Promise.all(
            runIds.map((rid) => evaluationApi.getContext(rid).catch(() => null))
          );
          setEvalContexts(contexts.filter(Boolean));
        } finally {
          setIsLoadingContexts(false);
        }
      }
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.error?.message ||
        err?.message ||
        'Comparison failed. Ensure all selected models have training and evaluation records.';
      setCompareError(msg);
    },
  });

  // ── chart data ─────────────────────────────────────────────────────────────
  const scalarChartData = useMemo(() => {
    if (!comparison) return [];
    const valid = new Set(['accuracy', 'balanced_accuracy', 'sensitivity', 'specificity', 'precision', 'f1_score', 'roc_auc']);
    return comparison.comparison_matrix
      .filter((r) => valid.has(r.metric_key))
      .map((r) => {
        const point: any = { metric: r.display_name };
        comparison.models_compared.forEach((m) => {
          const v = r.values[m.model_name];
          point[m.model_name] = typeof v === 'number' ? parseFloat((v * 100).toFixed(1)) : 0;
        });
        return point;
      });
  }, [comparison]);

  const combinedRocData = useMemo(() => {
    if (!evalContexts.length) return [];
    return Array.from({ length: 101 }, (_, i) => {
      const fpr = i / 100;
      const point: any = { fpr: parseFloat(fpr.toFixed(2)) };
      evalContexts.forEach((ctx) => {
        const roc = ctx?.metrics?.rocData || [];
        if (!roc.length) return;
        const closest = roc.reduce((p: any, c: any) =>
          Math.abs(c.fpr - fpr) < Math.abs(p.fpr - fpr) ? c : p
        );
        point[ctx.model_name] = closest.tpr;
      });
      return point;
    });
  }, [evalContexts]);

  // ── render ─────────────────────────────────────────────────────────────────
  if (modelsLoading || datasetsLoading) return <LoadingSkeleton rows={4} />;

  const selectedVersionLabel = versionOptions.find((v) => v.versionId === selectedVersionId)?.label;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <header className="flex items-start gap-3 border-b border-slate-200 pb-4">
        <Layers className="mt-1 h-5 w-5 text-quantum-600 shrink-0" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Compare trained models</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Select a dataset and target, then pick which models to compare across all evaluation metrics.
          </p>
        </div>
      </header>

      {/* ── Step 1: Dataset + Target filter ───────────────────────────────── */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Step 1 — Choose dataset &amp; target</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="block space-y-1 text-xs font-semibold text-slate-700">
            Dataset &amp; version
            <select
              value={selectedVersionId}
              onChange={(e) => {
                setSelectedVersionId(e.target.value);
                setSelectedTarget('');
                setComparison(null);
                setCompareError(null);
              }}
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-normal focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="">— Select a dataset version —</option>
              {versionOptions.map((v) => (
                <option key={v.versionId} value={v.versionId}>{v.label}</option>
              ))}
            </select>
          </label>

          <label className="block space-y-1 text-xs font-semibold text-slate-700">
            Target column
            <select
              value={selectedTarget}
              onChange={(e) => {
                setSelectedTarget(e.target.value);
                setComparison(null);
                setCompareError(null);
              }}
              disabled={!selectedVersionId || targetOptions.length === 0}
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-normal focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:opacity-50"
            >
              <option value="">— All targets —</option>
              {targetOptions.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>
        </div>

        {selectedVersionId && compatibleModels.length === 0 && (
          <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
            No trained models found for this dataset/target combination. Train models on this version first.
          </p>
        )}
      </section>

      {/* ── Step 2: Model picker ───────────────────────────────────────────── */}
      {compatibleModels.length > 0 && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Step 2 — Select models to compare</h2>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {selectedVersionLabel && <><span className="font-mono font-semibold">{selectedVersionLabel}</span> · </>}
                {selectedTarget && <><span className="font-mono font-semibold">{selectedTarget}</span> · </>}
                {compatibleModels.length} model{compatibleModels.length !== 1 ? 's' : ''} available
              </p>
            </div>
            <button
              type="button"
              onClick={toggleAll}
              className="flex items-center gap-1.5 text-xs font-semibold text-brand-700 hover:text-brand-900"
            >
              {selectedIds.length === compatibleModels.length
                ? <><CheckSquare className="h-4 w-4" /> Deselect all</>
                : <><Square className="h-4 w-4" /> Select all</>
              }
            </button>
          </div>

          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {compatibleModels.map((model) => {
              const checked = selectedIds.includes(model.id);
              const cfg = model.configuration || {};
              const featureCount = (cfg.selected_features as string[] | undefined)?.length ?? 0;
              return (
                <label
                  key={model.id}
                  className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 text-xs transition-colors ${
                    checked ? 'border-brand-800 bg-brand-50' : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleModel(model.id)}
                    className="mt-0.5 accent-brand-800"
                  />
                  <span className="flex-1 min-w-0">
                    <span className="block font-bold text-slate-900 truncate">{model.name}</span>
                    <span className="block text-slate-500 mt-0.5">
                      {modelBadge(model)} · {featureCount} feature{featureCount !== 1 ? 's' : ''}
                      {model.is_default && (
                        <span className="ml-2 rounded-full bg-quantum-100 px-1.5 py-0.5 text-[10px] font-semibold text-quantum-700">
                          Pretrained
                        </span>
                      )}
                    </span>
                    <StatusBadge status={model.status || 'trained'} size="sm" />
                  </span>
                </label>
              );
            })}
          </div>

          {compareError && (
            <p className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {compareError}
            </p>
          )}

          <button
            type="button"
            disabled={selectedIds.length < 2 || compareMutation.isPending}
            onClick={() => compareMutation.mutate()}
            className="btn-primary inline-flex items-center gap-2 text-xs disabled:cursor-not-allowed disabled:opacity-50"
          >
            <BarChart3 className="h-4 w-4" />
            {compareMutation.isPending
              ? 'Comparing…'
              : `Compare ${selectedIds.length} model${selectedIds.length !== 1 ? 's' : ''}`}
          </button>
        </section>
      )}

      {compareMutation.isPending && <LoadingSkeleton type="table" rows={5} />}

      {/* ── Comparison results ─────────────────────────────────────────────── */}
      {comparison && (
        <div className="space-y-6">
          {/* Bar chart */}
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-5">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Held-out test comparison</h2>
              <p className="mt-1 text-xs text-slate-500">{comparison.executive_summary}</p>
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsBarChart data={scalarChartData} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="metric" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#64748b' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#64748b' }} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                  <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', fontSize: '11px' }} formatter={(v: number) => `${v}%`} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  {comparison.models_compared.map((m, idx) => (
                    <Bar key={m.model_id} dataKey={m.model_name} fill={COLORS[idx % COLORS.length]} radius={[4, 4, 0, 0]} maxBarSize={32} />
                  ))}
                </RechartsBarChart>
              </ResponsiveContainer>
            </div>

            {/* Metrics table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-slate-50">
                  <tr>
                    <th className="px-3 py-2 text-slate-600">Metric</th>
                    {comparison.models_compared.map((m) => (
                      <th key={m.model_id} className="px-3 py-2 text-center text-slate-600">{m.model_name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {comparison.comparison_matrix.map((row) => {
                    const pct = new Set(['accuracy', 'balanced_accuracy', 'sensitivity', 'specificity', 'precision', 'f1_score', 'roc_auc']);
                    const unit = row.metric_key === 'training_duration_sec' ? ' s' : row.metric_key === 'inference_latency_ms' ? ' ms' : '';
                    // find best value
                    const vals = Object.values(row.values).filter((v) => typeof v === 'number') as number[];
                    const best = vals.length ? (row.higher_is_better ? Math.max(...vals) : Math.min(...vals)) : null;
                    return (
                      <tr key={row.metric_key} className="hover:bg-slate-50">
                        <td className="px-3 py-2 font-semibold text-slate-700">{row.display_name}</td>
                        {comparison.models_compared.map((m) => {
                          const val = row.values[m.model_name];
                          const isB = best !== null && val === best;
                          const display = typeof val === 'number'
                            ? pct.has(row.metric_key) ? `${(val * 100).toFixed(1)}%` : `${val.toFixed(3)}${unit}`
                            : '—';
                          return (
                            <td key={m.model_id} className={`px-3 py-2 text-center font-mono ${isB ? 'text-emerald-700 font-bold' : 'text-slate-700'}`}>
                              {display}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* CML vs QML insights */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
              {String(comparison.cml_vs_qml_insights.interpretation || '')}
              {typeof comparison.cml_vs_qml_insights.classical_mean_accuracy === 'number' &&
                ` Classical mean accuracy: ${(comparison.cml_vs_qml_insights.classical_mean_accuracy * 100).toFixed(1)}%.`}
              {typeof comparison.cml_vs_qml_insights.quantum_mean_accuracy === 'number' &&
                ` Quantum mean accuracy: ${(comparison.cml_vs_qml_insights.quantum_mean_accuracy * 100).toFixed(1)}%.`}
            </div>
          </section>

          {/* ROC curves */}
          {evalContexts.length > 0 && !isLoadingContexts && combinedRocData.length > 0 && (
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Comparative ROC Curve</h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsLineChart data={combinedRocData} margin={{ top: 5, right: 20, bottom: 20, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="fpr" type="number" domain={[0, 1]} tick={{ fontSize: 10 }} label={{ value: 'False Positive Rate', position: 'insideBottom', offset: -15, fontSize: 10 }} />
                    <YAxis type="number" domain={[0, 1]} tick={{ fontSize: 10 }} label={{ value: 'True Positive Rate', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10 }} />
                    <Tooltip labelFormatter={(v) => `FPR: ${Number(v).toFixed(2)}`} formatter={(v: number) => Number(v).toFixed(2)} contentStyle={{ fontSize: '11px' }} />
                    <Legend wrapperStyle={{ fontSize: '10px' }} />
                    {comparison.models_compared.map((m, idx) => (
                      <Line key={m.model_id} type="stepAfter" dataKey={m.model_name} stroke={COLORS[idx % COLORS.length]} dot={false} strokeWidth={2} />
                    ))}
                  </RechartsLineChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}
        </div>
      )}

      {/* no models at all */}
      {!selectedVersionId && versionOptions.length === 0 && (
        <EmptyState icon={BarChart3} title="No datasets found" description="Upload a dataset and train models before comparing." />
      )}
    </div>
  );
};
