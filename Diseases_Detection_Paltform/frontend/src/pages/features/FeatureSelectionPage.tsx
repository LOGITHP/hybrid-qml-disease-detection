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
  { id: 'lasso', label: 'L1 Logistic (LASSO)', desc: 'Sparse classification coefficients' },
  { id: 'manual', label: 'Manual', desc: 'Choose the dataset columns directly' },
];

export const FeatureSelectionPage: React.FC = () => {
  const [selectedMethod, setSelectedMethod] = useState('mutual_info');
  const [kFeatures, setKFeatures] = useState<number>(4);
  const [targetColumn, setTargetColumn] = useState(() => sessionStorage.getItem('activeTargetColumn') || '');
  const [targetVersionId, setTargetVersionId] = useState(() => sessionStorage.getItem('activeDatasetVersionId') || '');
  const [manualFeatures, setManualFeatures] = useState<string[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [savedRun, setSavedRun] = useState<FeatureSelectionRun | null>(null);

  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
  });

  const storedVersionId = sessionStorage.getItem('activeDatasetVersionId');
  const selectedDataset = datasets?.find((d) => d.id === selectedDatasetId)
    || datasets?.find((d) => d.versions?.some((version) => version.id === storedVersionId))
    || datasets?.[0];
  const activeVersion = selectedDataset?.versions?.find((version) => version.id === storedVersionId)
    || [...(selectedDataset?.versions || [])].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))[0];

  const selectFeaturesMutation = useMutation({
    mutationFn: async () => {
      if (!activeVersion) throw new Error('No dataset version available');
      return await featuresApi.selectFeatures({
        dataset_version_id: activeVersion.id,
        ranking_method: selectedMethod,
        k_features: kFeatures,
        target_column: targetColumn,
        selected_features: selectedMethod === 'manual' ? manualFeatures : undefined,
      });
    },
    onSuccess: (data) => {
      setSavedRun(data);
      if (activeVersion) {
        sessionStorage.setItem('activeDatasetVersionId', activeVersion.id);
        sessionStorage.setItem('activeFeatureSelectionRunId', data.id);
        sessionStorage.setItem('activeSelectedFeatures', JSON.stringify(data.selected_features));
        sessionStorage.setItem('activeTargetColumn', targetColumn);
      }
    },
  });

  // Fetch analysis for the selected dataset to know the columns
  const { data: analysis } = useQuery({
    queryKey: ['datasetAnalysis', selectedDataset?.id, activeVersion?.id],
    queryFn: () =>
      selectedDataset?.id && activeVersion?.id
        ? datasetsApi.analyzeVersion(selectedDataset.id, activeVersion.id)
        : Promise.reject('No version'),
    enabled: !!selectedDataset?.id && !!activeVersion?.id,
  });

  const availableFeatureColumns = (analysis?.columns || []).filter((column) => column !== targetColumn);
  const targetCandidates = analysis?.columns || [];

  React.useEffect(() => {
    if (analysis?.columns?.length && analysis.version_id !== targetVersionId) {
      setTargetColumn(analysis.target_column || analysis.columns[analysis.columns.length - 1]);
      setTargetVersionId(analysis.version_id);
    } else if (analysis?.columns?.length && (!targetColumn || !analysis.columns.includes(targetColumn))) {
      setTargetColumn(analysis.target_column || analysis.columns[analysis.columns.length - 1]);
    }
  }, [analysis?.version_id, analysis?.target_column, analysis?.columns, targetColumn, targetVersionId]);

  React.useEffect(() => {
    const max = Math.min(8, Math.max(1, availableFeatureColumns.length));
    setKFeatures((current) => Math.min(current, max));
    setManualFeatures((current) => current.filter((column) => availableFeatureColumns.includes(column)));
    setSavedRun(null);
  }, [activeVersion?.id, targetColumn]);

  const currentScores = savedRun?.ranking_scores || {};
  const sortedFeatures = Object.entries(currentScores).sort((a, b) => b[1] - a[1]);
  const maxScore = sortedFeatures.length > 0 ? sortedFeatures[0][1] : 1;
  const selectedFeatureNames = selectedMethod === 'manual' ? manualFeatures : savedRun
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

      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="space-y-1 text-xs font-semibold text-slate-700">
          Uploaded dataset
          <select
            value={selectedDataset?.id || ''}
            onChange={(event) => {
              setSelectedDatasetId(event.target.value);
              setSavedRun(null);
              sessionStorage.removeItem('activeDatasetVersionId');
              sessionStorage.removeItem('activePreprocessingRunId');
              sessionStorage.removeItem('activeFeatureSelectionRunId');
              sessionStorage.removeItem('activeSelectedFeatures');
              sessionStorage.removeItem('activeTargetColumn');
            }}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white font-normal"
          >
            {(datasets || []).map((dataset) => (
              <option key={dataset.id} value={dataset.id}>{dataset.name}</option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-xs font-semibold text-slate-700">
          Target column
          <select
            value={targetColumn}
            onChange={(event) => {
              setTargetColumn(event.target.value);
              setSavedRun(null);
              sessionStorage.setItem('activeTargetColumn', event.target.value);
              sessionStorage.removeItem('activePreprocessingRunId');
              sessionStorage.removeItem('activeFeatureSelectionRunId');
              sessionStorage.removeItem('activeSelectedFeatures');
            }}
            disabled={!targetCandidates.length}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white font-normal"
          >
            {targetCandidates.map((column) => <option key={column} value={column}>{column}</option>)}
          </select>
        </label>
        {analysis && (
          <p className="md:col-span-2 text-[11px] text-slate-500">
            {analysis.row_count} uploaded rows · {availableFeatureColumns.length} candidate feature columns · {activeVersion?.version_tag}
          </p>
        )}
      </div>

      {/* Controls: Ranking Method & Feature Count */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Method Selection */}
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
              Biomarker Ranking Algorithm
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2">
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
                min="1"
                max={Math.max(1, Math.min(8, availableFeatureColumns.length))}
                step="1"
                value={Math.min(kFeatures, Math.max(1, Math.min(8, availableFeatureColumns.length)))}
                onChange={(e) => setKFeatures(parseInt(e.target.value, 10))}
                className="w-full accent-brand-800 cursor-pointer"
                disabled={!availableFeatureColumns.length || selectedMethod === 'manual'}
              />
              <div className="flex justify-between text-[11px] text-slate-400 font-mono mt-1">
                <span>1</span>
                <span className="font-semibold text-brand-800">Up to {Math.min(8, availableFeatureColumns.length)} features in this dataset</span>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
          <div className="text-xs text-slate-500">
            Selected Dataset:{' '}
            <span className="font-semibold text-slate-800">
              {selectedDataset?.name || 'Select an uploaded dataset'}
            </span>
          </div>
          <button
            onClick={() => selectFeaturesMutation.mutate()}
            disabled={selectFeaturesMutation.isPending || !activeVersion || !targetColumn || (selectedMethod === 'manual' && manualFeatures.length === 0)}
            className="btn-primary text-xs py-2 px-5 flex items-center space-x-2"
          >
            <Filter className="w-3.5 h-3.5" />
            <span>{selectFeaturesMutation.isPending ? 'Computing from Uploaded Data...' : selectedMethod === 'manual' ? 'Save Selected Columns' : 'Rank & Select Features'}</span>
          </button>
        </div>
      </div>

      {selectFeaturesMutation.isError && (
        <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-xs text-red-800">
          {selectFeaturesMutation.error instanceof Error ? selectFeaturesMutation.error.message : 'Feature selection failed for this dataset.'}
        </div>
      )}

      {/* Selected Features Preview Badge Row */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Canonical Selected Features (Source of Truth)
          </h3>
          <span className="text-[11px] font-mono text-slate-400">
            {selectedFeatureNames.length} columns selected from this dataset
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {selectedMethod === 'manual' ? availableFeatureColumns.map((feat) => (
            <label key={feat} className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-200 bg-slate-50 text-xs">
              <input
                type="checkbox"
                checked={manualFeatures.includes(feat)}
                onChange={(event) => setManualFeatures((current) => event.target.checked
                  ? [...current, feat]
                  : current.filter((column) => column !== feat))}
                className="accent-brand-800"
              />
              <span className="font-mono">{feat}</span>
            </label>
          )) : selectedFeatureNames.map((feat, idx) => (
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
              {sortedFeatures.length === 0 ? (
                <tr><td colSpan={5} className="p-8 text-center text-slate-500">
                  {selectedMethod === 'manual' ? 'Manual column selection is enabled above.' : 'Choose a ranking method and run it to see scores from the uploaded dataset.'}
                </td></tr>
              ) : sortedFeatures.map(([feat, score], index) => {
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
