import React, { useState, useMemo, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart3,
  ShieldCheck,
  Layers,
  ArrowRight,
  Activity,
  Info,
  Box,
  Lightbulb,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { MetricCard } from '../../components/common/MetricCard';
import { evaluationApi, trainingApi, modelsApi } from '../../api';
import { Model } from '../../types';

export const EvaluationPage: React.FC = () => {
  const { runId } = useParams<{ runId?: string }>();
  const [selectedRunId, setSelectedRunId] = useState<string>(runId || '');
  const [threshold, setThreshold] = useState<number>(0.5);

  // Fetch all training runs (user-trained)
  const { data: runs } = useQuery({
    queryKey: ['trainingRuns-eval'],
    queryFn: trainingApi.listRuns,
  });

  // Fetch all models — includes both pretrained (is_default=true) and user-trained
  const { data: allModels } = useQuery({
    queryKey: ['all-models-eval'],
    queryFn: modelsApi.list,
  });

  // Build a unified, ordered list of { label, runId } entries for the dropdown.
  // Strategy:
  //   - Pretrained models: use model.name. Their training_run_id points to the eval run.
  //   - User-trained models: find the matching training run via model.training_run_id.
  //   - Fallback: training runs with no matching model are shown with a generated label.
  const dropdownOptions = useMemo(() => {
    const options: { label: string; runId: string; badge: string }[] = [];
    const usedRunIds = new Set<string>();

    // Pretrained models first (is_default = true)
    const pretrained = (allModels || []).filter((m: Model) => m.is_default);
    for (const model of pretrained) {
      const runId = model.training_run_id;
      if (runId) {
        options.push({
          label: model.name,
          runId,
          badge: 'Pretrained',
        });
        usedRunIds.add(runId);
      }
    }

    // User-trained models (is_default = false, has a training_run_id)
    const userModels = (allModels || []).filter((m: Model) => !m.is_default && m.training_run_id);
    for (const model of userModels) {
      const runId = model.training_run_id!;
      if (!usedRunIds.has(runId)) {
        options.push({
          label: model.name,
          runId,
          badge: model.model_type?.toUpperCase() || 'Custom',
        });
        usedRunIds.add(runId);
      }
    }

    // Any training runs that don't yet have a matching model record
    for (const run of runs || []) {
      if (!usedRunIds.has(run.id)) {
        options.push({
          label: `Run ${run.id.slice(0, 8)} · ${run.model_type || run.model_id?.slice(0, 8) || 'unknown'}`,
          runId: run.id,
          badge: run.model_type?.toUpperCase() || 'Run',
        });
        usedRunIds.add(run.id);
      }
    }

    return options;
  }, [allModels, runs]);

  // Auto-select first option when nothing is selected
  useEffect(() => {
    if (!selectedRunId && dropdownOptions.length > 0) {
      setSelectedRunId(dropdownOptions[0].runId);
    }
  }, [dropdownOptions, selectedRunId]);

  const { data: evalContext, isLoading, isError } = useQuery({
    queryKey: ['evaluation-context', selectedRunId],
    queryFn: () => evaluationApi.getContext(selectedRunId),
    enabled: !!selectedRunId,
  });

  const dynamicMetrics = useMemo(() => {
    if (!evalContext || !evalContext.y_true || !evalContext.y_prob) {
      return null;
    }

    const y_true = evalContext.y_true as number[];
    const y_prob = evalContext.y_prob as number[];

    let tp = 0, tn = 0, fp = 0, fn = 0;

    for (let i = 0; i < y_true.length; i++) {
      const actual = y_true[i];
      const prob = y_prob[i];
      const predicted = prob >= threshold ? 1 : 0;

      if (actual === 1 && predicted === 1) tp++;
      else if (actual === 0 && predicted === 0) tn++;
      else if (actual === 0 && predicted === 1) fp++;
      else if (actual === 1 && predicted === 0) fn++;
    }

    const total = tp + tn + fp + fn;
    const accuracy = total > 0 ? (tp + tn) / total : 0;
    const sensitivity = (tp + fn) > 0 ? tp / (tp + fn) : 0;
    const specificity = (tn + fp) > 0 ? tn / (tn + fp) : 0;
    const precision = (tp + fp) > 0 ? tp / (tp + fp) : 0;
    const f1 = (precision + sensitivity) > 0 ? (2 * precision * sensitivity) / (precision + sensitivity) : 0;
    const balanced_accuracy = (sensitivity + specificity) / 2;

    const rocData = [];
    const prData = [];

    const thresholdData = [];
    for (let t = 0; t <= 100; t += 2) {
      const thresh = t / 100;
      let c_tp = 0, c_tn = 0, c_fp = 0, c_fn = 0;
      for (let i = 0; i < y_true.length; i++) {
        const actual = y_true[i];
        const predicted = y_prob[i] >= thresh ? 1 : 0;
        if (actual === 1 && predicted === 1) c_tp++;
        else if (actual === 0 && predicted === 0) c_tn++;
        else if (actual === 0 && predicted === 1) c_fp++;
        else if (actual === 1 && predicted === 0) c_fn++;
      }
      const c_sens = (c_tp + c_fn) > 0 ? c_tp / (c_tp + c_fn) : 0;
      const c_spec = (c_tn + c_fp) > 0 ? c_tn / (c_tn + c_fp) : 0;
      const c_prec = (c_tp + c_fp) > 0 ? c_tp / (c_tp + c_fp) : 1;

      thresholdData.push({
        threshold: thresh,
        sensitivity: c_sens,
        specificity: c_spec,
        precision: c_prec
      });

      rocData.push({
        fpr: 1 - c_spec,
        tpr: c_sens
      });

      prData.push({
        recall: c_sens,
        precision: c_prec
      });
    }

    rocData.sort((a, b) => a.fpr - b.fpr);
    prData.sort((a, b) => a.recall - b.recall);

    return {
      tp, tn, fp, fn,
      total,
      accuracy,
      sensitivity,
      specificity,
      precision,
      f1,
      balanced_accuracy,
      roc_auc: evalContext.metrics.roc_auc || 0,
      thresholdData,
      rocData,
      prData
    };
  }, [evalContext, threshold]);

  if (!selectedRunId) {
    return (
      <div className="p-8 text-center text-slate-500">
        <Activity className="w-12 h-12 mx-auto mb-4 text-slate-300" />
        <h2 className="text-lg font-bold text-slate-700">{dropdownOptions.length === 0 ? 'Loading models…' : 'No Evaluation Runs Yet'}</h2>
        {dropdownOptions.length > 0 && (<><p className="mb-4 mt-2 text-sm">Train a model to see its held-out evaluation here.</p><Link to="/training" className="btn-primary inline-flex items-center space-x-2"><span>Open training setup</span><ArrowRight className="w-4 h-4" /></Link></>)}
      </div>
    );
  }

  if (isLoading) return <div className="p-8 text-center text-sm font-semibold text-slate-500">Loading comprehensive evaluation context...</div>;
  if (isError || !evalContext) return <div className="p-8 text-center text-red-600 font-bold">Failed to load evaluation data for this training run.</div>;

  const m = dynamicMetrics || evalContext.metrics;
  const gen = evalContext.metrics.generalization || {};

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <BarChart3 className="w-4 h-4 text-brand-600" />
            <span>MODEL EVALUATION & DIAGNOSTICS</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Performance Metrics</h1>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Link to="/evaluation/comparison" className="btn-secondary text-xs flex items-center gap-2">
            <Layers className="w-4 h-4" /> Compare Models
          </Link>
          {/* Model selector — shows model names for pretrained + user-trained */}
          <select
            value={selectedRunId}
            onChange={(e) => setSelectedRunId(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs max-w-[300px] focus:ring-brand-500 focus:border-brand-500"
          >
            {dropdownOptions.length === 0 && (
              <option disabled value="">Loading models…</option>
            )}
            {dropdownOptions.map((opt) => (
              <option key={opt.runId} value={opt.runId}>
                {opt.label} [{opt.badge}]
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Pipeline Context Bar */}
      <section className="bg-slate-50 p-5 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2"><Box className="w-4 h-4"/> Required Pipeline Context for this Evaluation</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 text-[11px] font-mono">
          <div><span className="block text-slate-400 uppercase font-bold mb-1">Source Dataset</span><span className="text-slate-800 line-clamp-1" title={evalContext.dataset_name}>{evalContext.dataset_name}</span></div>
          <div><span className="block text-slate-400 uppercase font-bold mb-1">Target Column</span><span className="text-slate-800 break-all">{evalContext.target_column || '—'}</span></div>
          <div><span className="block text-slate-400 uppercase font-bold mb-1">Required Features</span><span className="text-slate-800">{evalContext.selected_feature_count} features</span></div>
          <div><span className="block text-slate-400 uppercase font-bold mb-1">Preprocessing Node</span><span className="text-slate-800">{evalContext.preprocessing_run_id?.substring(0,8) || 'N/A'}</span></div>
          <div><span className="block text-slate-400 uppercase font-bold mb-1">Model Architecture</span><span className="text-slate-800 uppercase">{evalContext.model_type} ({evalContext.learning_type})</span></div>
        </div>
      </section>

      {/* Core Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
        <MetricCard title="ACCURACY" value={`${(m.accuracy * 100).toFixed(1)}%`} />
        <MetricCard title="BALANCED ACC" value={`${((m.balanced_accuracy || 0) * 100).toFixed(1)}%`} />
        <MetricCard title="SENSITIVITY" value={`${(m.sensitivity * 100).toFixed(1)}%`} badgeColor="success" />
        <MetricCard title="SPECIFICITY" value={`${(m.specificity * 100).toFixed(1)}%`} />
        <MetricCard title="PRECISION" value={`${(m.precision * 100).toFixed(1)}%`} />
        <MetricCard title="F1-SCORE" value={`${(m.f1 * 100).toFixed(1)}%`} />
        <MetricCard title="ROC-AUC" value={(m.roc_auc || 0).toFixed(3)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confusion Matrix */}
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">CONFUSION MATRIX</h3>
          <div className="grid grid-cols-2 gap-3 text-center text-xs">
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
              <span className="text-[10px] text-emerald-800 font-semibold uppercase block mb-1">True Positives (TP)</span>
              <span className="text-3xl font-extrabold text-emerald-900 font-mono">{dynamicMetrics?.tp ?? 0}</span>
            </div>
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
              <span className="text-[10px] text-red-800 font-semibold uppercase block mb-1">False Positives (FP)</span>
              <span className="text-3xl font-extrabold text-red-900 font-mono">{dynamicMetrics?.fp ?? 0}</span>
            </div>
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
              <span className="text-[10px] text-amber-800 font-semibold uppercase block mb-1">False Negatives (FN)</span>
              <span className="text-3xl font-extrabold text-amber-900 font-mono">{dynamicMetrics?.fn ?? 0}</span>
            </div>
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
              <span className="text-[10px] text-emerald-800 font-semibold uppercase block mb-1">True Negatives (TN)</span>
              <span className="text-3xl font-extrabold text-emerald-900 font-mono">{dynamicMetrics?.tn ?? 0}</span>
            </div>
          </div>
        </div>

        {/* Threshold Tuning */}
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">THRESHOLD TUNING</h3>
          <div className="space-y-6 pt-4">
            <div>
               <div className="flex justify-between mb-2">
                 <span className="text-xs font-bold text-slate-600">Decision Threshold</span>
                 <span className="text-xs font-mono font-bold text-brand-700">{threshold.toFixed(2)}</span>
               </div>
               <input
                 type="range"
                 min="0.00"
                 max="1.00"
                 step="0.01"
                 value={threshold}
                 onChange={(e) => setThreshold(parseFloat(e.target.value))}
                 className="w-full accent-brand-600 cursor-pointer h-2 bg-slate-200 rounded-lg appearance-none"
               />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex flex-col justify-center items-center">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Sensitivity</span>
                <span className="text-2xl font-bold font-mono text-slate-800">{(m.sensitivity * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex flex-col justify-center items-center">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Specificity</span>
                <span className="text-2xl font-bold font-mono text-slate-800">{(m.specificity * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ROC & PR Curves */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
         <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">ROC CURVE</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dynamicMetrics?.rocData} margin={{ top: 5, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="fpr" type="number" domain={[0, 1]} tick={{fontSize: 10}} label={{ value: 'False Positive Rate', position: 'insideBottom', offset: -15, fontSize: 10 }} />
                  <YAxis type="number" domain={[0, 1]} tick={{fontSize: 10}} label={{ value: 'True Positive Rate', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10 }} />
                  <Tooltip labelFormatter={(v) => `FPR: ${Number(v).toFixed(2)}`} formatter={(v: number) => Number(v).toFixed(2)} />
                  <Area type="stepAfter" dataKey="tpr" name="Sensitivity" stroke="#3b82f6" fill="#eff6ff" />
                  <Line type="monotone" dataKey="fpr" stroke="#94a3b8" strokeDasharray="5 5" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
         </div>

         <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">PR CURVE</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dynamicMetrics?.prData} margin={{ top: 5, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="recall" type="number" domain={[0, 1]} tick={{fontSize: 10}} label={{ value: 'Recall (Sensitivity)', position: 'insideBottom', offset: -15, fontSize: 10 }} />
                  <YAxis type="number" domain={[0, 1]} tick={{fontSize: 10}} label={{ value: 'Precision', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10 }} />
                  <Tooltip labelFormatter={(v) => `Recall: ${Number(v).toFixed(2)}`} formatter={(v: number) => Number(v).toFixed(2)} />
                  <Area type="stepAfter" dataKey="precision" name="Precision" stroke="#10b981" fill="#ecfdf5" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
         </div>
      </div>

      {/* CML vs QML Comparison */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row justify-between items-center gap-4">
        <div>
          <h3 className="text-sm font-bold tracking-wider text-slate-800">CML vs QML COMPARISON</h3>
          <p className="text-xs text-slate-500 mt-1">Compare this {evalContext.model_type} model against other SVM or VQC runs on the same dataset.</p>
        </div>
        <Link to={`/evaluation/comparison?run=${selectedRunId}`} className="btn-primary text-xs flex items-center space-x-2 whitespace-nowrap">
          <Layers className="w-4 h-4" />
          <span>Launch Multi-Model Comparison</span>
        </Link>
      </div>

      {/* Generalization */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">GENERALIZATION</h3>
        <div className="grid grid-cols-3 gap-6">
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
            <span className="block text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">Train</span>
            <div className="space-y-1">
              <div className="flex justify-between text-xs"><span className="text-slate-600">Accuracy</span><span className="font-mono font-bold">{gen.train?.accuracy ? (gen.train.accuracy * 100).toFixed(1) + '%' : 'N/A'}</span></div>
              <div className="flex justify-between text-xs"><span className="text-slate-600">Sensitivity</span><span className="font-mono font-bold">{gen.train?.sensitivity ? (gen.train.sensitivity * 100).toFixed(1) + '%' : 'N/A'}</span></div>
              <div className="flex justify-between text-xs"><span className="text-slate-600">Specificity</span><span className="font-mono font-bold">{gen.train?.specificity ? (gen.train.specificity * 100).toFixed(1) + '%' : 'N/A'}</span></div>
            </div>
          </div>
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
            <span className="block text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">Validation</span>
             <div className="flex h-full pb-4 items-center justify-center text-xs text-slate-400 italic">Not tracked</div>
          </div>
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
            <span className="block text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">Test</span>
             <div className="space-y-1">
              <div className="flex justify-between text-xs"><span className="text-slate-600">Accuracy</span><span className="font-mono font-bold">{gen.test?.accuracy ? (gen.test.accuracy * 100).toFixed(1) + '%' : 'N/A'}</span></div>
              <div className="flex justify-between text-xs"><span className="text-slate-600">Sensitivity</span><span className="font-mono font-bold">{gen.test?.sensitivity ? (gen.test.sensitivity * 100).toFixed(1) + '%' : 'N/A'}</span></div>
              <div className="flex justify-between text-xs"><span className="text-slate-600">Specificity</span><span className="font-mono font-bold">{gen.test?.specificity ? (gen.test.specificity * 100).toFixed(1) + '%' : 'N/A'}</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* Computational Metrics */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">COMPUTATIONAL METRICS</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-100 flex flex-col">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">Training Time</span>
            <span className="text-xl font-mono font-bold text-slate-800">
              {evalContext.computational?.training_time != null ? `${evalContext.computational.training_time.toFixed(2)} s` : 'N/A'}
            </span>
          </div>
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-100 flex flex-col">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">Inference Time</span>
            <span className="text-xl font-mono font-bold text-slate-800">
              {evalContext.computational?.inference_time != null ? `${evalContext.computational.inference_time.toFixed(2)} ms` : 'N/A'}
            </span>
          </div>
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-100 flex flex-col">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">Trainable Parameters</span>
            <span className="text-xl font-mono font-bold text-slate-800">
              {evalContext.computational?.trainable_parameters != null ? evalContext.computational.trainable_parameters.toLocaleString() : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Quantum Model Details */}
      <div className="card-scientific bg-quantum-50 border border-quantum-200 rounded-xl p-6 shadow-sm space-y-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
          <Box className="w-32 h-32 text-quantum-900" />
        </div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-quantum-900 flex items-center gap-2">
           <Box className="w-4 h-4" /> QUANTUM MODEL DETAILS
        </h3>

        {evalContext.learning_type === 'QML' && evalContext.quantum ? (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4 relative z-10">
            <div><span className="block text-[10px] text-quantum-700 uppercase font-bold mb-1">Qubits</span><span className="text-xl font-mono font-bold text-quantum-900">{evalContext.quantum.n_qubits || 'N/A'}</span></div>
            <div><span className="block text-[10px] text-quantum-700 uppercase font-bold mb-1">Encoding</span><span className="text-sm font-bold text-quantum-900 mt-2 block">{evalContext.quantum.encoding || 'Angle'}</span></div>
            <div><span className="block text-[10px] text-quantum-700 uppercase font-bold mb-1">Layers</span><span className="text-xl font-mono font-bold text-quantum-900">{evalContext.quantum.n_layers || 'N/A'}</span></div>
            <div><span className="block text-[10px] text-quantum-700 uppercase font-bold mb-1">Gates</span><span className="text-xl font-mono font-bold text-quantum-900">{evalContext.quantum.gates || 'N/A'}</span></div>
            <div><span className="block text-[10px] text-quantum-700 uppercase font-bold mb-1">Depth</span><span className="text-xl font-mono font-bold text-quantum-900">{evalContext.quantum.depth || 'N/A'}</span></div>
            <div><span className="block text-[10px] text-quantum-700 uppercase font-bold mb-1">Shots</span><span className="text-sm font-bold text-quantum-900 mt-2 block">{evalContext.quantum.shots || 'Analytic'}</span></div>
          </div>
        ) : (
          <p className="text-xs text-quantum-700 italic">Classical Model - No quantum configuration</p>
        )}
      </div>

      {/* Model Explainability */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row justify-between items-center gap-4">
        <div>
          <h3 className="text-sm font-bold tracking-wider text-slate-800">MODEL EXPLAINABILITY</h3>
          <p className="text-xs text-slate-500 mt-1">Feature importance / sensitivity</p>
        </div>
        <Link to={`/explainability/${evalContext.training_run_id}`} className="btn-secondary text-xs flex items-center space-x-2">
          <Lightbulb className="w-4 h-4" />
          <span>View Details</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Notice */}
      <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex gap-3 text-xs text-amber-800">
        <ShieldCheck className="w-5 h-5 flex-shrink-0 text-amber-600" />
        <div>
          <p className="font-bold uppercase tracking-wider text-[10px] mb-0.5">Research / Prototype Notice</p>
          <p>
            This system is a research and computational screening prototype. Model outputs are strictly
            intended for diagnostic research and decision support and are not a medical diagnosis.
          </p>
        </div>
      </div>
    </div>
  );
};
