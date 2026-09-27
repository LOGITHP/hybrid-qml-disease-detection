import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Filter,
  BarChart3,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  Sliders,
  Layers,
  Info,
} from 'lucide-react';
import { datasetsApi, featuresApi } from '../../api';
import { FeatureSelectionRun } from '../../types';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

const RANKING_METHODS = [
  { id: 'mutual_info', label: 'Mutual Information', desc: 'Captures non-linear dependence with target' },
  { id: 'random_forest', label: 'Random Forest Gini', desc: 'Ensemble decision tree feature importances' },
  { id: 'f_classif', label: 'ANOVA F-Test', desc: 'Linear statistical variance ratio analysis' },
];

export const FeatureSelectionPage: React.FC = () => {
  const [selectedMethod, setSelectedMethod] = useState('mutual_info');
  const [kFeatures, setKFeatures] = useState<number>(4);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [savedRun, setSavedRun] = useState<FeatureSelectionRun | null>(null);

  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
  });

  const selectedDataset = datasets?.find((d) => d.id === selectedDatasetId) || datasets?.[0];
  const activeVersion = selectedDataset?.versions?.[0];

  const selectFeaturesMutation = useMutation({
    mutationFn: async () => {
      if (!activeVersion) throw new Error('No dataset version available');
      return await featuresApi.selectFeatures({
        dataset_version_id: activeVersion.id,
        ranking_method: selectedMethod,
        k_features: kFeatures,
      });
    },
    onSuccess: (data) => {
      setSavedRun(data);
    },
  });

  // Default initial scores based on actual experimental cancer study
  const initialFeatureScores: Record<string, number> = {
    WHEEZING: 0.142,
    YELLOW_FINGERS: 0.138,
    AGE: 0.119,
    SHORTNESS_OF_BREATH: 0.105,
    PEER_PRESSURE: 0.088,
    FATIGUE: 0.082,
    CHEST_PAIN: 0.076,
    COUGHING: 0.071,
    SMOKING: 0.065,
    ALCOHOL_CONSUMING: 0.058,
    ANXIETY: 0.052,
    ALLERGY: 0.048,
    CHRONIC_DISEASE: 0.041,
    SWALLOWING_DIFFICULTY: 0.035,
  };

  const currentScores = savedRun?.ranking_scores || initialFeatureScores;
  const sortedFeatures = Object.entries(currentScores).sort((a, b) => b[1] - a[1]);
  const maxScore = Math.max(...Object.values(currentScores));
  const selectedFeatureNames = savedRun
    ? savedRun.selected_features
    : sortedFeatures.slice(0, kFeatures).map((item) => item[0]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <Filter className="w-4 h-4 text-quantum-600" />
            <span>Single Source of Truth Feature Engine</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Feature Ranking & Canonical Selection
          </h1>
          <p className="text-xs text-slate-500">
            Statistically evaluate biomarker importances to produce the unified feature subset shared by all models
          </p>
        </div>

        {savedRun && (
          <Link
            to="/models"
            className="btn-primary text-xs flex items-center space-x-1.5 self-start sm:self-auto"
          >
            <span>Proceed to Models Zoo</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        )}
      </div>

      {/* Critical Architecture Callout */}
      <div className="p-4 bg-brand-900 text-white rounded-xl shadow-sm flex items-start space-x-3 text-xs">
        <Info className="w-5 h-5 text-quantum-300 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold text-sm tracking-tight text-white block">
            Core Architectural Guarantee: Single Source of Truth
          </span>
          <p className="text-slate-200 leading-relaxed">
            The selected feature subset generated here is shared <strong>identically</strong> by both Classical Support Vector Machines (Linear & RBF SVM) and Variational Quantum Classifiers (PennyLane VQC). Feature count is never configured independently per model to guarantee scientific comparability and prevent selection bias.
          </p>
        </div>
      </div>

      {/* Controls: Ranking Method & K-Feature Slider */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Method Selection */}
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
              Biomarker Ranking Algorithm
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {RANKING_METHODS.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setSelectedMethod(m.id)}
                  className={`p-3 text-left rounded-lg border text-xs transition-all ${
                    selectedMethod === m.id
                      ? 'border-brand-800 bg-brand-50/60 font-semibold text-brand-900 shadow-sm'
                      : 'border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  <span className="block font-bold">{m.label}</span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">{m.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* K-Features Selector */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Number of Canonical Features ($k$)
              </label>
              <span className="text-sm font-bold text-quantum-700 font-mono bg-quantum-50 px-2.5 py-0.5 rounded border border-quantum-200">
                {kFeatures} Features Selected
              </span>
            </div>
            <div className="pt-2">
              <input
                type="range"
                min="2"
                max="8"
                step="2"
                value={kFeatures}
                onChange={(e) => setKFeatures(parseInt(e.target.value, 10))}
                className="w-full accent-brand-800 cursor-pointer"
              />
              <div className="flex justify-between text-[11px] text-slate-400 font-mono mt-1">
                <span>2 (Fast VQC)</span>
                <span className="font-semibold text-brand-800">4 (Recommended &bull; 4-Qubit VQC)</span>
                <span>6 (6-Qubit VQC)</span>
                <span>8 (8-Qubit VQC)</span>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
          <div className="text-xs text-slate-500">
            Selected Dataset:{' '}
            <span className="font-semibold text-slate-800">
              {selectedDataset?.name || 'Lung Cancer Benchmark Cohort'}
            </span>
          </div>
          <button
            onClick={() => selectFeaturesMutation.mutate()}
            disabled={selectFeaturesMutation.isPending || !activeVersion}
            className="btn-primary text-xs py-2 px-5 flex items-center space-x-2"
          >
            <Filter className="w-3.5 h-3.5" />
            <span>
              {selectFeaturesMutation.isPending ? 'Computing Ranking Scores...' : 'Lock Canonical Feature Set'}
            </span>
          </button>
        </div>
      </div>

      {/* Selected Features Preview Badge Row */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Canonical Selected Features (Source of Truth)
          </h3>
          <span className="text-[11px] font-mono text-slate-400">
            Compatible with {kFeatures}-Qubit PennyLane VQC & SVM
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {selectedFeatureNames.map((feat, idx) => (
            <div
              key={feat}
              className="flex items-center space-x-2 px-3 py-1.5 bg-brand-50 border border-brand-200 rounded-lg text-xs font-semibold text-brand-900 shadow-sm"
            >
              <span className="w-4 h-4 rounded-full bg-brand-800 text-white flex items-center justify-center text-[10px]">
                {idx + 1}
              </span>
              <span className="font-mono">{feat}</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            </div>
          ))}
        </div>
      </div>

      {/* Feature Ranking Table & Importance Bars */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl overflow-hidden p-0 shadow-sm">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Ranked Biomarkers Importance Distribution
          </h3>
          <span className="text-xs text-slate-500">Method: {selectedMethod}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/60 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-6 w-16">Rank</th>
                <th className="py-3 px-6">Biomarker Feature</th>
                <th className="py-3 px-6">Relative Score Bar</th>
                <th className="py-3 px-6 w-28 text-right">Score</th>
                <th className="py-3 px-6 w-32 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {sortedFeatures.map(([feat, score], index) => {
                const isSelected = selectedFeatureNames.includes(feat);
                const percent = ((score / maxScore) * 100).toFixed(0);
                return (
                  <tr
                    key={feat}
                    className={`transition-colors ${
                      isSelected ? 'bg-brand-50/40 font-medium' : 'hover:bg-slate-50/60'
                    }`}
                  >
                    <td className="py-3 px-6 font-mono font-bold text-slate-500">#{index + 1}</td>
                    <td className="py-3 px-6 font-mono font-semibold text-slate-900">{feat}</td>
                    <td className="py-3 px-6">
                      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-2 rounded-full ${
                            isSelected ? 'bg-brand-700' : 'bg-slate-300'
                          }`}
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </td>
                    <td className="py-3 px-6 text-right font-mono text-slate-600">
                      {score.toFixed(4)}
                    </td>
                    <td className="py-3 px-6 text-center">
                      {isSelected ? (
                        <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Selected
                        </span>
                      ) : (
                        <span className="badge bg-slate-100 text-slate-400 border border-slate-200">
                          Excluded
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
