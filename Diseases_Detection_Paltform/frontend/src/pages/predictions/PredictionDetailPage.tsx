import React from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  Lightbulb,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { PredictionResponse } from '../../types';
import { MedicalNotice } from '../../components/common/MedicalNotice';

export const PredictionDetailPage: React.FC = () => {
  const { predictionId } = useParams<{ predictionId: string }>();

  // Retrieve stored prediction from sessionStorage or provide fallback
  let predictionData: PredictionResponse | null = null;
  const stored = sessionStorage.getItem('latest_prediction');
  if (stored) {
    try {
      predictionData = JSON.parse(stored);
    } catch (e) {
      predictionData = null;
    }
  }

  const result = predictionData?.results?.[0] || {
    predicted_class: 1,
    predicted_label: 'POSITIVE',
    probability: 0.824,
    risk_stratification: { risk_level: 'HIGH', score: 0.824 },
    input_features_used: ['WHEEZING', 'YELLOW_FINGERS', 'AGE', 'SHORTNESS_OF_BREATH'],
    sample_id: 'sample-1',
  };

  const isHighRisk = result.risk_stratification.risk_level === 'HIGH';
  const isMediumRisk = result.risk_stratification.risk_level === 'MEDIUM';
  const isLowRisk = result.risk_stratification.risk_level === 'LOW';

  const riskBadgeStyles = isHighRisk
    ? 'bg-red-50 text-red-700 border-red-200'
    : isMediumRisk
    ? 'bg-amber-50 text-amber-700 border-amber-200'
    : 'bg-emerald-50 text-emerald-700 border-emerald-200';

  const probPercent = (result.probability * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-mono text-xs text-slate-400">
              Evaluation Reference: {predictionId || 'latest-screening'}
            </span>
            <span className={`badge border font-semibold ${riskBadgeStyles}`}>
              Risk Level: {result.risk_stratification.risk_level}
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Clinical Screening Assessment
          </h1>
          <p className="text-xs text-slate-500">
            Model inference probability distribution and risk category stratification
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link to="/predictions" className="btn-secondary text-xs flex items-center space-x-1.5">
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Screen Another Patient</span>
          </Link>
          <Link
            to={`/explainability/${predictionId || 'demo'}`}
            className="btn-primary text-xs flex items-center space-x-2"
          >
            <Lightbulb className="w-3.5 h-3.5" />
            <span>Explain Model Prediction</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

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
                  result.predicted_class === 1 ? 'text-red-700' : 'text-emerald-700'
                }`}
              >
                {result.predicted_label === 'POSITIVE' ? 'Positive Indication' : 'Negative Indication'}
              </span>
              <span className="text-xs text-slate-500 font-mono">
                Class {result.predicted_class}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-6 text-right">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                Estimated Probability
              </span>
              <span className="text-3xl font-extrabold text-slate-900 font-mono">
                {probPercent}%
              </span>
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                Stratified Category
              </span>
              <span className={`badge text-sm px-3 py-1 font-bold border mt-0.5 ${riskBadgeStyles}`}>
                {result.risk_stratification.risk_level} RISK
              </span>
            </div>
          </div>
        </div>

        {/* Accessible Probability Visualizer */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-semibold text-slate-700">
            <span>Disease Likelihood Score</span>
            <span className="font-mono">{result.probability.toFixed(4)}</span>
          </div>
          <div className="w-full bg-slate-100 h-4 rounded-full overflow-hidden p-0.5 border border-slate-200">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isHighRisk ? 'bg-red-500' : isMediumRisk ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${probPercent}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 font-mono pt-1">
            <span>0% (Low)</span>
            <span>35% (Threshold Low/Med)</span>
            <span>65% (Threshold Med/High)</span>
            <span>100% (High)</span>
          </div>
        </div>

        {/* Model Provenance & Features Used */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
          <span className="font-bold text-slate-800 block">Screening Provenance & Features Used</span>
          <div className="flex flex-wrap gap-2 pt-1">
            {result.input_features_used.map((feat) => (
              <span
                key={feat}
                className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-slate-700 font-mono text-[11px]"
              >
                {feat}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Safety Notice */}
      <MedicalNotice />
    </div>
  );
};
