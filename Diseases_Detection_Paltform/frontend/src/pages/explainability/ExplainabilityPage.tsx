import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { Activity, ArrowRight, Lightbulb } from 'lucide-react';
import { MedicalNotice } from '../../components/common/MedicalNotice';
import { EmptyState } from '../../components/common/EmptyState';
import { PredictionResponse } from '../../types';

export const ExplainabilityPage: React.FC = () => {
  const { predictionId } = useParams<{ predictionId: string }>();
  const prediction = (() => {
    try { return JSON.parse(sessionStorage.getItem('latest_prediction') || 'null') as PredictionResponse | null; }
    catch { return null; }
  })();
  const inputs = (() => {
    try { return JSON.parse(sessionStorage.getItem('latest_prediction_input') || '{}') as Record<string, unknown>; }
    catch { return {}; }
  })();
  const result = prediction?.results?.[0];
  const modelName = sessionStorage.getItem('latest_prediction_model_name') || 'Trained model';
  const modelType = sessionStorage.getItem('latest_prediction_model_type') || '';

  if (!prediction || !result) {
    return <EmptyState icon={Lightbulb} title="No prediction to explain" description="Run an inference on the current selected feature set to review its actual input values and model output." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1"><Lightbulb className="w-4 h-4 text-quantum-600" /><span>Prediction Provenance</span></div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Inputs and Model Output</h1>
          <p className="text-xs text-slate-500">Prediction {predictionId || result.sample_id || 'latest'} · {modelName}</p>
        </div>
        <Link to="/predictions" className="btn-secondary text-xs flex items-center space-x-1.5"><Activity className="w-3.5 h-3.5" /><span>New prediction</span></Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5">
          <span className="text-[11px] text-slate-500">Model output score</span>
          <div className="text-2xl font-bold text-slate-900">{result.probability == null ? 'Unavailable' : `${(result.probability * 100).toFixed(1)}%`}</div>
          <p className="text-[11px] text-slate-500 mt-1">{modelType === 'vqc' ? 'Uncalibrated VQC score; not a clinical probability.' : 'Model probability; not a clinically validated risk estimate.'}</p>
        </div>
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5">
          <span className="text-[11px] text-slate-500">Thresholded classification</span>
          <div className="text-2xl font-bold text-slate-900">{result.predicted_label}</div>
          <p className="text-[11px] text-slate-500 mt-1">Threshold used: {(prediction.decision_threshold_applied * 100).toFixed(0)}%</p>
        </div>
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5">
          <span className="text-[11px] text-slate-500">Prototype model category</span>
          <div className="text-2xl font-bold text-slate-900">{result.risk_stratification?.risk_level || 'Not available'}</div>
          <p className="text-[11px] text-slate-500 mt-1">The category is not medically validated.</p>
        </div>
      </div>

      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Feature values sent to the model</h2>
          <p className="text-[11px] text-slate-500 mt-1">The saved preprocessing transformer applies the same encoding and scaling used during training.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase text-[10px]"><tr><th className="py-2 px-3">Feature</th><th className="py-2 px-3">Submitted value</th><th className="py-2 px-3">Used by selected model</th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {result.input_features_used.map((feature) => (
                <tr key={feature}><td className="py-2 px-3 font-mono font-semibold">{feature}</td><td className="py-2 px-3">{inputs[feature] == null ? 'Missing' : String(inputs[feature])}</td><td className="py-2 px-3">Yes</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start gap-2">
          <Lightbulb className="w-4 h-4 text-brand-700 flex-shrink-0 mt-0.5" />
          <p>Feature-level attribution values are not produced by the current training run. The panel reports the real inputs, score, threshold, and saved pipeline provenance without assigning unsupported per-feature contributions.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg"><span className="font-bold text-slate-800 block">Preprocessing run</span><span className="font-mono text-slate-600 break-all">{prediction.preprocessing_run_id || 'Not recorded'}</span></div>
          <div className="p-3 bg-slate-50 rounded-lg"><span className="font-bold text-slate-800 block">Feature-selection run</span><span className="font-mono text-slate-600 break-all">{prediction.feature_selection_run_id || 'Not recorded'}</span></div>
        </div>
      </div>

      <div className="flex justify-end"><Link to="/predictions" className="btn-primary text-xs flex items-center gap-2">Return to predictions<ArrowRight className="w-3.5 h-3.5" /></Link></div>
      <MedicalNotice />
    </div>
  );
};
