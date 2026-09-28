import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Activity,
  Sliders,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Layers,
  Atom,
  CheckCircle2,
} from 'lucide-react';
import { modelsApi, predictionsApi } from '../../api';
import { MedicalNotice } from '../../components/common/MedicalNotice';
import { StatusBadge } from '../../components/common/StatusBadge';

export const PredictionPage: React.FC = () => {
  const navigate = useNavigate();

  const { data: defaultModels } = useQuery({
    queryKey: ['defaultModels'],
    queryFn: modelsApi.listDefaults,
  });

  const [selectedModelId, setSelectedModelId] = useState<string>('pretrained-qml-vqc-4-noiseless');
  const [decisionThreshold, setDecisionThreshold] = useState<number>(0.5);

  // Canonical 4 features derived from FeatureSelectionRun
  const [biomarkers, setBiomarkers] = useState<Record<string, number>>({
    AGE: 65,
    YELLOW_FINGERS: 2,
    WHEEZING: 2,
    SHORTNESS_OF_BREATH: 2,
  });

  const activeModel = defaultModels?.find((m) => m.id === selectedModelId) || defaultModels?.[0];
  const activeVersion = activeModel?.versions?.[0];

  const predictMutation = useMutation({
    mutationFn: async () => {
      return await predictionsApi.predict({
        model_id: selectedModelId,
        features: biomarkers,
        decision_threshold: decisionThreshold,
      });
    },
    onSuccess: (data) => {
      // Store latest result and navigate to detail
      sessionStorage.setItem('latest_prediction', JSON.stringify(data));
      navigate(`/predictions/result-latest`);
    },
  });

  const setHighRiskPreset = () => {
    setBiomarkers({
      AGE: 72,
      YELLOW_FINGERS: 2,
      WHEEZING: 2,
      SHORTNESS_OF_BREATH: 2,
    });
  };

  const setLowRiskPreset = () => {
    setBiomarkers({
      AGE: 42,
      YELLOW_FINGERS: 1,
      WHEEZING: 1,
      SHORTNESS_OF_BREATH: 1,
    });
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <Activity className="w-4 h-4 text-quantum-600 animate-pulse" />
            <span>Real-time Clinical Screening</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Patient Disease Risk Inference
          </h1>
          <p className="text-xs text-slate-500">
            Screen patient profiles using trained classical SVMs or PennyLane Variational Quantum Classifiers
          </p>
        </div>

        {/* Quick Presets for Demo */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={setHighRiskPreset}
            className="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-lg text-xs font-semibold transition-colors"
          >
            Preset: High Risk Profile
          </button>
          <button
            type="button"
            onClick={setLowRiskPreset}
            className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-semibold transition-colors"
          >
            Preset: Low Risk Profile
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Form Input */}
        <div className="lg:col-span-2 space-y-5">
          {/* Model Selection */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
              Select Inference Classifier Archetype
            </label>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="w-full px-3 py-2.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white font-medium"
            >
              {defaultModels?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.model_type})
                </option>
              ))}
            </select>
          </div>

          {/* Biomarkers Input Card */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Biomarker Values (Expected Schema)
                </h3>
                <p className="text-[11px] text-slate-400">
                  Features strictly bound to the canonical FeatureSelectionRun
                </p>
              </div>
              <span className="badge bg-brand-50 text-brand-800 border border-brand-200">
                4 Canonical Features
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  AGE (Patient Chronological Age)
                </label>
                <input
                  type="number"
                  min="18"
                  max="100"
                  value={biomarkers.AGE}
                  onChange={(e) =>
                    setBiomarkers({ ...biomarkers, AGE: parseFloat(e.target.value) || 0 })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  YELLOW_FINGERS (Nicotine Staining)
                </label>
                <select
                  value={biomarkers.YELLOW_FINGERS}
                  onChange={(e) =>
                    setBiomarkers({ ...biomarkers, YELLOW_FINGERS: parseInt(e.target.value, 10) })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
                >
                  <option value={1}>1: Absent / Negative</option>
                  <option value={2}>2: Present / Evident</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  WHEEZING (Respiratory Sound)
                </label>
                <select
                  value={biomarkers.WHEEZING}
                  onChange={(e) =>
                    setBiomarkers({ ...biomarkers, WHEEZING: parseInt(e.target.value, 10) })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
                >
                  <option value={1}>1: Absent / Normal</option>
                  <option value={2}>2: Present / Clinical Wheeze</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  SHORTNESS_OF_BREATH (Dyspnea)
                </label>
                <select
                  value={biomarkers.SHORTNESS_OF_BREATH}
                  onChange={(e) =>
                    setBiomarkers({ ...biomarkers, SHORTNESS_OF_BREATH: parseInt(e.target.value, 10) })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
                >
                  <option value={1}>1: None / Mild</option>
                  <option value={2}>2: Moderate to Severe</option>
                </select>
              </div>
            </div>

            {/* Decision Threshold Tuning */}
            <div className="pt-4 border-t border-slate-100 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-700">Clinical Decision Threshold ($\tau$)</span>
                <span className="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                  {decisionThreshold.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.90"
                step="0.05"
                value={decisionThreshold}
                onChange={(e) => setDecisionThreshold(parseFloat(e.target.value))}
                className="w-full accent-brand-800 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400">
                Lower thresholds prioritize sensitivity (reducing false negatives in early screening).
              </p>
            </div>
          </div>
        </div>

        {/* Right Col: Action & Notice */}
        <div className="space-y-4">
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Inference Dispatch
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Biomarkers are min-max scaled using stored training bounds and fed into the selected model.
            </p>

            <button
              onClick={() => predictMutation.mutate()}
              disabled={predictMutation.isPending}
              className="w-full btn-primary text-xs py-3 flex items-center justify-center space-x-2 shadow-md"
            >
              <Activity className="w-4 h-4" />
              <span>{predictMutation.isPending ? 'Computing Prediction...' : 'Evaluate Patient Risk'}</span>
            </button>
          </div>

          <MedicalNotice />
        </div>
      </div>
    </div>
  );
};
