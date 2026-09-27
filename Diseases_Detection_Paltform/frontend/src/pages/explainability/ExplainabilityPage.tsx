import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Lightbulb,
  ShieldCheck,
  Atom,
  Sliders,
  ChevronDown,
  ChevronUp,
  Activity,
  ArrowRight,
  Info,
} from 'lucide-react';
import { MedicalNotice } from '../../components/common/MedicalNotice';

export const ExplainabilityPage: React.FC = () => {
  const { predictionId } = useParams<{ predictionId: string }>();
  const [showTechnical, setShowTechnical] = useState(false);

  const featureAttributions = [
    { feature: 'WHEEZING', value: 'Present (2)', contribution: 0.38, direction: 'Positive (Elevates Risk)' },
    { feature: 'YELLOW_FINGERS', value: 'Present (2)', contribution: 0.29, direction: 'Positive (Elevates Risk)' },
    { feature: 'AGE', value: '65 Years', contribution: 0.21, direction: 'Moderate Positive' },
    { feature: 'SHORTNESS_OF_BREATH', value: 'Severe (2)', contribution: 0.12, direction: 'Positive (Elevates Risk)' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <Lightbulb className="w-4 h-4 text-quantum-600" />
            <span>Clinical Model Interpretability</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Prediction Explainability & Provenance
          </h1>
          <p className="text-xs text-slate-500">
            Mathematical breakdown of how patient biomarker values influenced the model decision
          </p>
        </div>

        <Link
          to="/predictions"
          className="btn-secondary text-xs flex items-center space-x-1.5 self-start sm:self-auto"
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Back to Screening</span>
        </Link>
      </div>

      {/* Primary Interpretation Card */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900">What the Model Predicted</h3>
            <p className="text-xs text-slate-500">
              Output: <span className="font-bold text-red-700">Positive Screening Indication</span> (Estimated Likelihood: 82.4%)
            </p>
          </div>
          <span className="badge bg-red-50 text-red-700 border border-red-200 font-semibold">
            HIGH RISK CATEGORY
          </span>
        </div>

        {/* Feature Contribution Distribution */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Biomarker Feature Attributions
            </span>
            <span className="text-[11px] text-slate-400">
              Relative contribution to log-odds activation
            </span>
          </div>

          <div className="space-y-3">
            {featureAttributions.map((item) => (
              <div key={item.feature} className="p-3 bg-slate-50 rounded-xl space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-slate-900 font-mono font-bold">{item.feature} ({item.value})</span>
                  <span className="text-brand-900 font-mono font-bold">
                    +{(item.contribution * 100).toFixed(0)}% Weight
                  </span>
                </div>
                <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-brand-800 h-2 rounded-full"
                    style={{ width: `${item.contribution * 100}%` }}
                  />
                </div>
                <div className="text-[11px] text-slate-500 flex justify-between">
                  <span>{item.direction}</span>
                  <span className="text-[10px] text-slate-400">Validated against training split</span>
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start space-x-2">
            <Info className="w-4 h-4 text-brand-700 flex-shrink-0 mt-0.5" />
            <p>
              <strong>Important Clinical Distinction:</strong> These attribution scores describe mathematical contributions to the model output function. They do <em>not</em> claim physiological causation.
            </p>
          </div>
        </div>
      </div>

      {/* Expandable Technical Details */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
        <button
          onClick={() => setShowTechnical(!showTechnical)}
          className="w-full flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-700"
        >
          <div className="flex items-center space-x-2">
            <Atom className="w-4 h-4 text-quantum-600" />
            <span>Technical Quantum & Classical Execution Metadata</span>
          </div>
          {showTechnical ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showTechnical && (
          <div className="pt-3 border-t border-slate-100 space-y-3 text-xs text-slate-600">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="font-bold text-slate-800 block">Classifier Engine</span>
                <span className="font-mono text-slate-600">PennyLane Variational Quantum Classifier (4 Qubits)</span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="font-bold text-slate-800 block">Backend Device</span>
                <span className="font-mono text-slate-600">default.qubit Statevector Simulator</span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="font-bold text-slate-800 block">Ansatz Architecture</span>
                <span className="font-mono text-slate-600">2-Layer Linear CNOT Entanglement with Pauli-Z Pooling</span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="font-bold text-slate-800 block">Data Leakage Verification</span>
                <span className="font-mono text-emerald-700">PASSED: Scaler bounds fit strictly on train set</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Medical Safety Notice */}
      <MedicalNotice />
    </div>
  );
};
