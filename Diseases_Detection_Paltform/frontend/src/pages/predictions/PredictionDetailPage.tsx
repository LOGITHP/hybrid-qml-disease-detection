import React from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  Lightbulb,
} from 'lucide-react';
import { SinglePredictionResult } from '../../types';
import { MedicalNotice } from '../../components/common/MedicalNotice';
import { EmptyState } from '../../components/common/EmptyState';

export const PredictionDetailPage: React.FC = () => {
  const { predictionId } = useParams<{ predictionId: string }>();

  // Retrieve the actual prediction generated in this session.
  let result: SinglePredictionResult | null = null;
  let inputFeatures: Record<string, any> | null = null;
  let metrics: Record<string, any> | null = null;

  try {
    const stored = sessionStorage.getItem('latest_prediction');
    if (stored) result = JSON.parse(stored);
    
    const storedInput = sessionStorage.getItem('latest_prediction_input');
    if (storedInput) inputFeatures = JSON.parse(storedInput);

    const storedMetrics = sessionStorage.getItem('latest_prediction_metrics');
    if (storedMetrics) metrics = JSON.parse(storedMetrics);
  } catch (e) {
    // Ignore parse errors
  }

  if (!result) return <EmptyState icon={Activity} title="No prediction result" description="Run an inference with a trained model to view its actual score and selected input features." />;

  const riskLevel = result.risk_category;
  const isHighRisk = riskLevel === 'HIGH';
  const isMediumRisk = riskLevel === 'MEDIUM';

  const riskBadgeStyles = isHighRisk
    ? 'bg-red-50 text-red-700 border-red-200'
    : isMediumRisk
    ? 'bg-amber-50 text-amber-700 border-amber-200'
    : 'bg-emerald-50 text-emerald-700 border-emerald-200';

  const probPercent = result.score == null ? null : (result.score * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-mono text-xs text-slate-400">
              Run Ref: {result.training_run_id?.substring(0, 8) || 'latest-screening'}
            </span>
            <span className={`badge border font-semibold ${riskBadgeStyles}`}>
              Model category: {riskLevel || 'Unavailable'}
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Clinical Screening Assessment
          </h1>
          <p className="text-xs text-slate-500">
            Actual model output and its configurable classification threshold
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link to="/predictions" className="btn-secondary text-xs flex items-center space-x-1.5">
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Screen Another Patient</span>
          </Link>
          <Link
            to={`/explainability/${result.training_run_id || 'demo'}`}
            className="btn-primary text-xs flex items-center space-x-2"
          >
            <Lightbulb className="w-3.5 h-3.5" />
            <span>Explain Model Prediction</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Main Result Card */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-8 shadow-sm space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-100">
              <div className="space-y-1">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Binary Prediction Class
                </span>
                <div className="flex items-baseline space-x-3">
                  <span
                    className={`text-3xl font-extrabold tracking-tight ${
                      result.prediction === 1 ? 'text-red-700' : 'text-emerald-700'
                    }`}
                  >
                  {result.predicted_label}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    Class {result.prediction}
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-6 text-right">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                    Model Score
                  </span>
                  <span className="text-3xl font-extrabold text-slate-900 font-mono">
                    {probPercent == null ? 'Unavailable' : `${probPercent}%`}
                  </span>
                </div>
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                    Stratified Category
                  </span>
                  <span className={`badge text-sm px-3 py-1 font-bold border mt-0.5 ${riskBadgeStyles}`}>
                    {riskLevel || 'Unavailable'}
                  </span>
                </div>
              </div>
            </div>

            {/* Accessible Probability Visualizer */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-700">
                <span>Model score</span>
                <span className="font-mono">{result.score == null ? 'Unavailable' : result.score.toFixed(4)}</span>
              </div>
              <div className="w-full bg-slate-100 h-4 rounded-full overflow-hidden p-0.5 border border-slate-200">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isHighRisk ? 'bg-red-500' : isMediumRisk ? 'bg-amber-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${probPercent || 0}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 font-mono pt-1">
                <span>0% (Low)</span>
                <span>35% (Threshold Low/Med)</span>
                <span>65% (Threshold Med/High)</span>
                <span>100% (High)</span>
              </div>
            </div>
          </div>
          
          {/* Explainability Section */}
          {result.explanation?.top_features && (
            <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Model Explanation (Top Features)</h3>
              <div className="space-y-3">
                {(result.explanation.top_features as any[]).map((f, i) => (
                  <div key={i} className="flex justify-between text-xs items-center">
                    <span className="font-mono">{f.feature}</span>
                    <span className="text-slate-500">{typeof f.contribution === 'number' ? f.contribution.toFixed(4) : f.contribution}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="card-scientific bg-slate-50 border border-slate-200 rounded-xl p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Patient Input Values</h3>
            {inputFeatures ? (
              <div className="space-y-2">
                {Object.entries(inputFeatures).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-xs pb-1 border-b border-slate-200 last:border-0">
                    <span className="text-slate-600 font-medium">{k}</span>
                    <span className="font-mono text-slate-900 font-bold">{v !== null ? String(v) : '—'}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No input features recorded.</p>
            )}
          </div>
          
          {metrics && (
             <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Model Performance Context</h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                 <div className="bg-slate-50 p-2 rounded border border-slate-100">
                    <span className="block text-slate-500 mb-1">Sensitivity</span>
                    <span className="font-bold text-slate-800">{(metrics.sensitivity * 100).toFixed(1)}%</span>
                 </div>
                 <div className="bg-slate-50 p-2 rounded border border-slate-100">
                    <span className="block text-slate-500 mb-1">Specificity</span>
                    <span className="font-bold text-slate-800">{(metrics.specificity * 100).toFixed(1)}%</span>
                 </div>
                 <div className="bg-slate-50 p-2 rounded border border-slate-100">
                    <span className="block text-slate-500 mb-1">F1 Score</span>
                    <span className="font-bold text-slate-800">{(metrics.f1_score * 100).toFixed(1)}%</span>
                 </div>
                 <div className="bg-slate-50 p-2 rounded border border-slate-100">
                    <span className="block text-slate-500 mb-1">ROC-AUC</span>
                    <span className="font-bold text-slate-800">{metrics.roc_auc?.toFixed(3) || '—'}</span>
                 </div>
              </div>
             </div>
          )}
          <MedicalNotice />
        </div>
      </div>
    </div>
  );
};
