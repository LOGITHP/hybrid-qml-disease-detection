import React, { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Activity, ArrowRight, Lightbulb, RotateCcw } from 'lucide-react';
import { PredictionResponse } from '../../types';
import { feedbackApi } from '../../api';
import { MedicalNotice } from '../../components/common/MedicalNotice';
import { EmptyState } from '../../components/common/EmptyState';

export const PredictionDetailPage: React.FC = () => {
  const { predictionId } = useParams<{ predictionId: string }>();
  const response = (() => {
    try { return JSON.parse(sessionStorage.getItem('latest_prediction') || 'null') as PredictionResponse | null; }
    catch { return null; }
  })();
  const inputs = (() => {
    try { return JSON.parse(sessionStorage.getItem('latest_prediction_input') || '{}') as Record<string, unknown>; }
    catch { return {}; }
  })();
  const modelName = sessionStorage.getItem('latest_prediction_model_name') || 'Trained model';
  const modelVersion = sessionStorage.getItem('latest_prediction_model_version') || 'Unknown';
  const datasetName = sessionStorage.getItem('latest_prediction_dataset_name') || 'Unknown';
  const datasetVersion = sessionStorage.getItem('latest_prediction_dataset_version') || 'Unknown';
  const [feedbackMessage, setFeedbackMessage] = useState('');
  const [feedbackError, setFeedbackError] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const result = response?.results?.[0];

  if (!response || !result) return <EmptyState icon={Activity} title="No prediction result" description="Generate a prediction with a trained model to see its actual output and input values." />;

  const risk = result.risk_stratification;
  const isPositive = result.predicted_class === 1;
  const score = result.probability;
  const badge = risk?.risk_level === 'HIGH'
    ? 'border-red-200 bg-red-50 text-red-700'
    : risk?.risk_level === 'MEDIUM'
      ? 'border-amber-200 bg-amber-50 text-amber-700'
      : 'border-emerald-200 bg-emerald-50 text-emerald-700';

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500"><span className="font-mono">{predictionId || result.sample_id || 'latest'}</span><span className={`rounded border px-2 py-0.5 font-semibold ${badge}`}>Prototype category: {risk?.risk_level || 'Unavailable'}</span></div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Prediction result</h1>
          <p className="text-xs text-slate-500">{modelName} · version {modelVersion} · {new Date(response.timestamp).toLocaleString()}</p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/predictions" className="btn-secondary flex items-center space-x-1.5 text-xs"><RotateCcw className="h-3.5 w-3.5" /><span>New prediction</span></Link>
          <Link to="/explainability/latest" className="btn-primary flex items-center gap-2 text-xs"><Lightbulb className="h-3.5 w-3.5" /><span>Review inputs</span><ArrowRight className="h-3.5 w-3.5" /></Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <section className="card-scientific space-y-5 rounded-xl border border-slate-200 bg-white p-7 shadow-sm">
            <div className="flex flex-col justify-between gap-5 border-b border-slate-100 pb-5 sm:flex-row sm:items-center">
              <div><span className="text-xs font-bold uppercase tracking-wider text-slate-400">Thresholded classification</span><div className={`mt-1 text-3xl font-extrabold ${isPositive ? 'text-red-700' : 'text-emerald-700'}`}>{result.predicted_label}</div><p className="text-xs text-slate-500">Class {result.predicted_class}</p></div>
              <div className="text-left sm:text-right"><span className="block text-xs font-bold uppercase tracking-wider text-slate-400">Model output score</span><span className="font-mono text-3xl font-extrabold text-slate-900">{score == null ? 'Unavailable' : `${(score * 100).toFixed(1)}%`}</span><p className="text-[11px] text-slate-500">Threshold: {(response.decision_threshold_applied * 100).toFixed(0)}%</p></div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-700"><span>Model output</span><span className="font-mono">{score == null ? 'Unavailable' : score.toFixed(4)}</span></div>
              <div className="h-4 overflow-hidden rounded-full border border-slate-200 bg-slate-100 p-0.5"><div className={`h-full rounded-full ${isPositive ? 'bg-red-500' : 'bg-emerald-500'}`} style={{ width: `${Math.max(0, Math.min(100, (score || 0) * 100))}%` }} /></div>
              <p className="text-[11px] text-slate-500">This score and its prototype category are research outputs, not a validated clinical risk estimate.</p>
            </div>
          </section>
          <section className="card-scientific rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Submitted feature values</h2>
            <div className="mt-3 overflow-x-auto"><table className="w-full text-left text-xs"><thead className="bg-slate-50 text-[10px] uppercase text-slate-500"><tr><th className="px-3 py-2">Feature</th><th className="px-3 py-2">Value</th></tr></thead><tbody className="divide-y divide-slate-100">{result.input_features_used.map((feature) => <tr key={feature}><td className="px-3 py-2 font-mono font-semibold">{feature}</td><td className="px-3 py-2">{inputs[feature] == null ? 'Missing' : String(inputs[feature])}</td></tr>)}</tbody></table></div>
          </section>

          <section className="card-scientific rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Clinician Feedback</h2>
              <span className="text-[10px] font-semibold text-brand-600 bg-brand-50 px-2 py-1 rounded">Continuous Learning</span>
            </div>
            <p className="text-xs text-slate-500 mb-4">Verified feedback is attached to this saved prediction and can be used only in a manually started retraining run.</p>
            {feedbackMessage && <p role="status" className="mb-3 rounded-lg bg-emerald-50 p-3 text-xs text-emerald-800">{feedbackMessage}</p>}
            {feedbackError && <p role="alert" className="mb-3 rounded-lg bg-red-50 p-3 text-xs text-red-800">{feedbackError}</p>}

            <form onSubmit={async (e) => {
              e.preventDefault();
              const form = e.currentTarget;
              const isCorrect = (form.elements.namedItem('is_correct') as HTMLSelectElement).value === 'true';
              const verifiedLabel = (form.elements.namedItem('verified_label') as HTMLInputElement).value;
              if (!isCorrect && verifiedLabel === '') {
                setFeedbackError('Enter the verified class label before submitting incorrect-prediction feedback.');
                setFeedbackMessage('');
                return;
              }
              if (!result.prediction_id) {
                setFeedbackError('This result has no saved prediction record. Feedback cannot be submitted.');
                setFeedbackMessage('');
                return;
              }
              const payload = {
                prediction_id: result.prediction_id,
                model_id: response.model_id,
                is_correct: isCorrect,
                verified_label: isCorrect ? result.predicted_class : (verifiedLabel ? parseInt(verifiedLabel, 10) : 0),
                original_input: inputs,
                notes: (form.elements.namedItem('notes') as HTMLTextAreaElement).value
              };

              try {
                setSubmittingFeedback(true);
                setFeedbackError('');
                await feedbackApi.submit(payload);
                setFeedbackMessage('Verified feedback saved. It remains pending until a retraining run is started manually.');
                form.reset();
              } catch (err) {
                setFeedbackError(err instanceof Error ? err.message : 'Feedback could not be submitted.');
              } finally {
                setSubmittingFeedback(false);
              }
            }} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <label className="block text-xs font-semibold text-slate-700 space-y-1">
                  <span>Is prediction correct?</span>
                  <select name="is_correct" className="w-full border-slate-300 rounded-md shadow-sm text-sm p-2 bg-white" required onChange={(e) => {
                    const labelInput = document.getElementById('verified_label_wrapper');
                    if (labelInput) labelInput.style.display = e.target.value === 'false' ? 'block' : 'none';
                  }}>
                    <option value="">Select...</option>
                    <option value="true">Yes, correct</option>
                    <option value="false">No, incorrect</option>
                  </select>
                </label>
                <label id="verified_label_wrapper" className="block text-xs font-semibold text-slate-700 space-y-1" style={{ display: 'none' }}>
                  <span>Verified Label (0 or 1)</span>
                  <input type="number" name="verified_label" min="0" max="1" className="w-full border-slate-300 rounded-md shadow-sm text-sm p-2" placeholder="e.g. 1" />
                </label>
              </div>
              <label className="block text-xs font-semibold text-slate-700 space-y-1">
                <span>Clinical Notes (Optional)</span>
                <textarea name="notes" className="w-full border-slate-300 rounded-md shadow-sm text-sm p-2" rows={2} placeholder="Any reasoning..."></textarea>
              </label>
              <button type="submit" disabled={submittingFeedback || !!feedbackMessage || !result.prediction_id} className="btn-primary w-full py-2 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-50">{submittingFeedback ? 'Saving feedback…' : feedbackMessage ? 'Feedback saved' : 'Submit Feedback'}</button>
            </form>
          </section>
        </div>

        <aside className="space-y-4">
          <section className="card-scientific space-y-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Pipeline provenance</h2>
            <div className="text-xs"><span className="block text-slate-500">Model</span><span className="break-all font-mono">{response.model_id}</span></div>
            <div className="text-xs"><span className="block text-slate-500">Dataset</span><span>{datasetName} · {datasetVersion}</span></div>
            <div className="text-xs"><span className="block text-slate-500">Dataset version ID</span><span className="break-all font-mono">{response.dataset_version_id || 'Not recorded'}</span></div>
            <div className="text-xs"><span className="block text-slate-500">Prediction record</span><span className="break-all font-mono">{result.prediction_id || 'Not saved'}</span></div>
            <div className="text-xs"><span className="block text-slate-500">Preprocessing run</span><span className="break-all font-mono">{response.preprocessing_run_id || 'Not recorded'}</span></div>
            <div className="text-xs"><span className="block text-slate-500">Feature-selection run</span><span className="break-all font-mono">{response.feature_selection_run_id || 'Not recorded'}</span></div>
          </section>
          <MedicalNotice />
        </aside>
      </div>
    </div>
  );
};
