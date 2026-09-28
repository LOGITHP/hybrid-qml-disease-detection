import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Sliders,
  Database,
  BrainCircuit,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  AlertTriangle,
  Play,
  RotateCcw,
  Check,
  Filter,
} from 'lucide-react';
import { datasetsApi, preprocessingApi } from '../../api';
import { PreprocessingPlan, PreprocessingPlanStep } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

const STEP_LABELS = [
  { id: 1, label: 'Dataset', description: 'Select cohort' },
  { id: 2, label: 'Analysis', description: 'Inspect distributions' },
  { id: 3, label: 'Plan', description: 'Review transformations' },
  { id: 4, label: 'Approval', description: 'Human review' },
  { id: 5, label: 'Execution', description: 'Apply transforms' },
  { id: 6, label: 'Validation', description: 'Leakage audit' },
  { id: 7, label: 'Completed', description: 'Ready for features' },
];

export const PreprocessingPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [mode, setMode] = useState<'ai' | 'user_defined'>('ai');
  const [targetColumn, setTargetColumn] = useState('');
  const [targetVersionId, setTargetVersionId] = useState('');
  const [numericStrategy, setNumericStrategy] = useState<'median' | 'mean' | 'most_frequent' | 'constant'>('median');
  const [categoricalStrategy, setCategoricalStrategy] = useState<'most_frequent' | 'constant'>('most_frequent');
  const [encodingMethod, setEncodingMethod] = useState<'one_hot' | 'ordinal'>('one_hot');
  const [scalingMethod, setScalingMethod] = useState<'min_max_scaler' | 'standard_scaler' | 'robust_scaler' | 'none'>('min_max_scaler');
  const [scalingColumns, setScalingColumns] = useState<string[]>([]);
  const [encodingColumns, setEncodingColumns] = useState<string[]>([]);
  const [removeOutliers, setRemoveOutliers] = useState(false);
  const [outlierColumns, setOutlierColumns] = useState<string[]>([]);
  const [generatedPlan, setGeneratedPlan] = useState<PreprocessingPlan | null>(null);
  const [executionResult, setExecutionResult] = useState<any | null>(null);

  // Fetch available datasets
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

  // Fetch analysis for the selected dataset
  const { data: analysis } = useQuery({
    queryKey: ['datasetAnalysis', selectedDataset?.id, activeVersion?.id],
    queryFn: () =>
      selectedDataset?.id && activeVersion?.id
        ? datasetsApi.analyzeVersion(selectedDataset.id, activeVersion.id)
        : Promise.reject('No version'),
    enabled: !!selectedDataset?.id && !!activeVersion?.id,
  });

  React.useEffect(() => {
    if (analysis?.columns?.length && analysis.version_id !== targetVersionId) {
      const suggestedTarget = analysis.target_column || analysis.columns[analysis.columns.length - 1];
      setTargetColumn(suggestedTarget);
      setTargetVersionId(analysis.version_id);
      setScalingColumns((analysis.numerical_columns || []).filter((column) => column !== suggestedTarget));
      setEncodingColumns((analysis.categorical_columns || []).filter((column) => column !== suggestedTarget));
      setOutlierColumns((analysis.numerical_columns || []).filter((column) => column !== suggestedTarget));
    } else if (analysis?.columns?.length && (!analysis.columns.includes(targetColumn) || !targetColumn)) {
      setTargetColumn(analysis.target_column || analysis.columns[analysis.columns.length - 1]);
    }
    setOutlierColumns((current) => current.filter((column) => analysis?.numerical_columns?.includes(column)));
  }, [analysis?.version_id, analysis?.target_column, analysis?.columns, targetColumn, targetVersionId]);

  const numericalColumns = (analysis?.numerical_columns || []).filter((column) => column !== targetColumn);
  const categoricalColumns = (analysis?.categorical_columns || []).filter((column) => column !== targetColumn);

  const makeUserDefinedPlan = () => {
    if (!activeVersion || !selectedDataset || !targetColumn) return;
    const steps: PreprocessingPlanStep[] = [
      {
        step_id: 1,
        tool_name: 'stratified_split',
        rationale: 'Split the uploaded rows before fitting any transformation.',
        parameters: { train_ratio: 0.7, val_ratio: 0.15, test_ratio: 0.15, random_state: 42 },
        fit_on_train_only: false,
      },
    ];
    if (numericalColumns.length) {
      steps.push({
        step_id: steps.length + 1,
        tool_name: 'numeric_imputer',
        rationale: `Impute selected numeric columns with the ${numericStrategy} strategy, fitted on training rows.`,
        parameters: { strategy: numericStrategy, columns: numericalColumns },
        fit_on_train_only: true,
      });
      const columnsToScale = scalingColumns.filter((column) => numericalColumns.includes(column));
      if (scalingMethod !== 'none' && columnsToScale.length) steps.push({
        step_id: steps.length + 1,
        tool_name: scalingMethod,
        rationale: 'Fit the selected numeric scaling method on chosen columns using training rows only.',
        parameters: { columns: columnsToScale },
        fit_on_train_only: true,
      });
    }
    if (categoricalColumns.length) {
      steps.push({
        step_id: steps.length + 1,
        tool_name: 'categorical_imputer',
        rationale: `Fill missing categorical values using ${categoricalStrategy === 'constant' ? 'a missing-value category' : 'the training mode'}.`,
        parameters: { strategy: categoricalStrategy, fill_value: '__missing__', columns: categoricalColumns },
        fit_on_train_only: true,
      });
      steps.push({
        step_id: steps.length + 1,
        tool_name: `${encodingMethod}_encoder`,
        rationale: `Apply ${encodingMethod.replace('_', ' ')} encoding to the chosen categorical columns.`,
        parameters: { columns: encodingColumns.filter((column) => categoricalColumns.includes(column)) },
        fit_on_train_only: true,
      });
    }
    if (removeOutliers && numericalColumns.length) steps.push({
      step_id: steps.length + 1,
      tool_name: 'iqr_outlier_removal',
      rationale: 'Estimate IQR bounds from training rows and remove outlier training rows only.',
      parameters: { columns: outlierColumns.filter((column) => numericalColumns.includes(column)), factor: 1.5 },
      fit_on_train_only: true,
    });
    setGeneratedPlan({
      dataset_id: selectedDataset.id,
      dataset_version_id: activeVersion.id,
      steps,
      summary: `Manual plan for ${analysis?.row_count ?? activeVersion.row_count} uploaded rows and ${analysis?.column_count ?? activeVersion.column_count} columns.`,
      leakage_prevention_guarantee: 'Transformers and outlier bounds are fitted on training rows only; validation and test rows are transformed without refitting.',
    });
    setCurrentStep(3);
  };

  // AI Plan formulation mutation (invokes Gemma reasoning via backend)
  const planMutation = useMutation({
    mutationFn: async () => {
      if (!activeVersion) throw new Error('No dataset version selected');
      return await preprocessingApi.generatePlan({
        dataset_version_id: activeVersion.id,
        target_column: targetColumn,
      });
    },
    onSuccess: (data) => {
      setGeneratedPlan(data);
      setCurrentStep(3); // Move to AI Plan review
    },
  });

  // Execute Preprocessing mutation (leak-free Scikit-Learn transformers)
  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!activeVersion) throw new Error('No dataset version selected');
      return await preprocessingApi.executePlan({
        dataset_version_id: activeVersion.id,
        target_column: targetColumn,
        mode,
        steps: generatedPlan?.steps,
      });
    },
    onSuccess: (data) => {
      setExecutionResult(data);
      if (sessionStorage.getItem('activeDatasetVersionId') !== data.dataset_version_id || sessionStorage.getItem('activeTargetColumn') !== targetColumn) {
        sessionStorage.removeItem('activeFeatureSelectionRunId');
        sessionStorage.removeItem('activeSelectedFeatures');
      }
      sessionStorage.setItem('activePreprocessingRunId', data.preprocessing_run_id);
      sessionStorage.setItem('activeDatasetVersionId', data.dataset_version_id);
      sessionStorage.setItem('activeTargetColumn', targetColumn);
      setCurrentStep(6); // Validation & Complete
    },
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <BrainCircuit className="w-4 h-4 text-quantum-600 animate-pulse" />
            <span>AI Clinical Preprocessing Agent</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Biomedical Data Preprocessing
          </h1>
          <p className="text-xs text-slate-500">
            Gemma LLM guided transformation with guaranteed prevention of training-to-test data leakage
          </p>
        </div>

        {executionResult && (
          <Link
            to="/features"
            className="btn-primary text-xs flex items-center space-x-1.5 self-start sm:self-auto"
          >
            <span>Proceed to Feature Selection</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        )}
      </div>

      {/* Stepper Bar */}
      <div className="card-scientific bg-white border border-slate-200 rounded-xl p-4 shadow-sm overflow-x-auto">
        <ol className="flex items-center justify-between min-w-[720px]">
          {STEP_LABELS.map((step, idx) => {
            const isCompleted = step.id < currentStep;
            const isCurrent = step.id === currentStep;
            return (
              <li key={step.id} className="flex-1 flex items-center">
                <div className="flex items-center space-x-2">
                  <span
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                      isCompleted
                        ? 'bg-emerald-600 text-white'
                        : isCurrent
                        ? 'bg-brand-800 text-white ring-4 ring-brand-100'
                        : 'bg-slate-100 text-slate-400'
                    }`}
                  >
                    {isCompleted ? <Check className="w-3.5 h-3.5" /> : step.id}
                  </span>
                  <div>
                    <span
                      className={`text-xs font-semibold block ${
                        isCurrent ? 'text-brand-900' : isCompleted ? 'text-slate-800' : 'text-slate-400'
                      }`}
                    >
                      {step.label}
                    </span>
                    <span className="text-[10px] text-slate-400 hidden xl:block">
                      {step.description}
                    </span>
                  </div>
                </div>
                {idx < STEP_LABELS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-3 ${
                      isCompleted ? 'bg-emerald-500' : 'bg-slate-200'
                    }`}
                  />
                )}
              </li>
            );
          })}
        </ol>
      </div>

      {/* Step 1 & 2: Dataset Selection and Mode */}
      {currentStep <= 2 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              1. Select Patient Cohort Dataset
            </h3>

            {datasetsLoading ? (
              <LoadingSkeleton rows={2} />
            ) : !datasets || datasets.length === 0 ? (
              <div className="text-center py-6 text-xs text-slate-500">
                No datasets ingested yet. Please upload a dataset first.
                <div className="mt-3">
                  <Link to="/datasets" className="btn-primary text-xs">
                    Go to Datasets
                  </Link>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <select
                  value={selectedDatasetId || datasets[0]?.id}
                  onChange={(e) => {
                    setSelectedDatasetId(e.target.value);
                    setGeneratedPlan(null);
                    setExecutionResult(null);
                    sessionStorage.removeItem('activeDatasetVersionId');
                    sessionStorage.removeItem('activePreprocessingRunId');
                    sessionStorage.removeItem('activeFeatureSelectionRunId');
                    sessionStorage.removeItem('activeSelectedFeatures');
                    sessionStorage.removeItem('activeTargetColumn');
                  }}
                  className="w-full px-3 py-2.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white font-medium"
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.versions?.[0]?.row_count || 0} rows,{' '}
                      {d.versions?.[0]?.column_count || 0} columns)
                    </option>
                  ))}
                </select>

                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                  <div className="flex justify-between text-slate-600 items-center">
                    <span>Target Classification Column:</span>
                    <select
                      value={targetColumn}
                      onChange={(e) => {
                        setTargetColumn(e.target.value);
                        setGeneratedPlan(null);
                        setExecutionResult(null);
                        sessionStorage.removeItem('activePreprocessingRunId');
                        sessionStorage.removeItem('activeFeatureSelectionRunId');
                        sessionStorage.removeItem('activeSelectedFeatures');
                        sessionStorage.setItem('activeTargetColumn', e.target.value);
                      }}
                      className="ml-2 px-2 py-1 border border-slate-300 rounded text-brand-900 font-bold bg-white"
                    >
                      {analysis?.columns?.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Version Tag:</span>
                    <span className="font-mono text-slate-800">{activeVersion?.version_tag || 'v1.0'}</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Validation Status:</span>
                    <StatusBadge status={activeVersion?.status || 'validated'} size="sm" />
                  </div>
                </div>
              </div>
            )}

            <div className="pt-4 border-t border-slate-100">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3">
                2. Choose Preprocessing Strategy
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div
                  onClick={() => setMode('ai')}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    mode === 'ai'
                      ? 'border-brand-800 bg-brand-50/50 shadow-sm'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1.5">
                    <Sparkles className="w-4 h-4 text-quantum-600" />
                    <span className="text-xs font-bold text-slate-900">AI-Assisted (Gemma LLM)</span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    The agent inspects the selected upload's column types, missing values, and target distribution before proposing transformations.
                  </p>
                </div>

                <div
                  onClick={() => setMode('user_defined')}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    mode === 'user_defined'
                      ? 'border-brand-800 bg-brand-50/50 shadow-sm'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1.5">
                    <Sliders className="w-4 h-4 text-slate-700" />
                    <span className="text-xs font-bold text-slate-900">User-Defined Rules</span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Choose imputation, categorical encoding, scaling, and optional training-only outlier removal by column.
                  </p>
                </div>
              </div>
            </div>

            {mode === 'user_defined' && (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Manual transformations for this upload</h4>
                {numericalColumns.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <label className="space-y-1 text-xs font-medium text-slate-700">
                      Numeric missing values
                      <select value={numericStrategy} onChange={(e) => setNumericStrategy(e.target.value as typeof numericStrategy)} className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white">
                        <option value="median">Median</option><option value="mean">Mean</option><option value="most_frequent">Most frequent</option><option value="constant">Zero constant</option>
                      </select>
                    </label>
                    <label className="space-y-1 text-xs font-medium text-slate-700">
                      Numeric scaling
                      <select value={scalingMethod} onChange={(e) => setScalingMethod(e.target.value as typeof scalingMethod)} className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white">
                        <option value="min_max_scaler">Min-max (0 to 1)</option><option value="standard_scaler">Standard</option><option value="robust_scaler">Robust</option><option value="none">No scaling</option>
                      </select>
                    </label>
                  </div>
                )}
                {categoricalColumns.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <label className="space-y-1 text-xs font-medium text-slate-700">
                      Categorical missing values
                      <select value={categoricalStrategy} onChange={(e) => setCategoricalStrategy(e.target.value as typeof categoricalStrategy)} className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white">
                        <option value="most_frequent">Most frequent value</option><option value="constant">Missing-value category</option>
                      </select>
                    </label>
                    <label className="space-y-1 text-xs font-medium text-slate-700">
                      Categorical encoding
                      <select value={encodingMethod} onChange={(e) => setEncodingMethod(e.target.value as typeof encodingMethod)} className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white">
                        <option value="one_hot">One-hot</option><option value="ordinal">Ordinal</option>
                      </select>
                    </label>
                  </div>
                )}
                {numericalColumns.length > 0 && scalingMethod !== 'none' && (
                  <div className="space-y-2">
                    <span className="text-xs font-medium text-slate-700">Numeric columns to scale</span>
                    <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs">
                      {numericalColumns.map((column) => (
                        <label key={`scale-${column}`} className="flex items-center gap-1.5 text-slate-600">
                          <input type="checkbox" checked={scalingColumns.includes(column)} onChange={(e) => setScalingColumns((current) => e.target.checked ? [...current, column] : current.filter((item) => item !== column))} className="accent-brand-800" />
                          {column}
                        </label>
                      ))}
                    </div>
                  </div>
                )}
                {categoricalColumns.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-medium text-slate-700">Categorical columns to encode</span>
                    <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs">
                      {categoricalColumns.map((column) => (
                        <label key={`encode-${column}`} className="flex items-center gap-1.5 text-slate-600">
                          <input type="checkbox" checked={encodingColumns.includes(column)} onChange={(e) => setEncodingColumns((current) => e.target.checked ? [...current, column] : current.filter((item) => item !== column))} className="accent-brand-800" />
                          {column}
                        </label>
                      ))}
                    </div>
                    {categoricalColumns.some((column) => !encodingColumns.includes(column)) && <p className="text-[11px] text-amber-700">Unchecked categorical columns will be omitted from the model feature matrix.</p>}
                  </div>
                )}
                {numericalColumns.length > 0 && (
                  <div className="space-y-2">
                    <label className="flex items-center gap-2 text-xs font-medium text-slate-700">
                      <input type="checkbox" checked={removeOutliers} onChange={(e) => setRemoveOutliers(e.target.checked)} className="accent-brand-800" />
                      Remove IQR outlier rows from the training partition
                    </label>
                    {removeOutliers && <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs">
                      {numericalColumns.map((column) => (
                        <label key={column} className="flex items-center gap-1.5 text-slate-600">
                          <input type="checkbox" checked={outlierColumns.includes(column)} onChange={(e) => setOutlierColumns((current) => e.target.checked ? [...current, column] : current.filter((item) => item !== column))} className="accent-brand-800" />
                          {column}
                        </label>
                      ))}
                    </div>}
                  </div>
                )}
                {!numericalColumns.length && !categoricalColumns.length && <p className="text-xs text-amber-800">Select a target column with at least one remaining feature.</p>}
              </div>
            )}

            {(planMutation.isError || executeMutation.isError) && (
              <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-xs text-red-800">
                {(planMutation.error || executeMutation.error) instanceof Error ? (planMutation.error || executeMutation.error as Error).message : 'Preprocessing failed for this dataset.'}
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => mode === 'user_defined' ? makeUserDefinedPlan() : planMutation.mutate()}
                disabled={planMutation.isPending || !activeVersion || !targetColumn || (mode === 'user_defined' && numericalColumns.length + categoricalColumns.length === 0)}
                className="btn-primary text-xs py-2.5 px-5 flex items-center space-x-2"
              >
                <BrainCircuit className="w-4 h-4" />
                <span>{mode === 'user_defined' ? 'Review Manual Plan' : planMutation.isPending ? 'Analyzing Uploaded Dataset...' : 'Analyze & Formulate Plan'}</span>
              </button>
            </div>
          </div>

          {/* Right Col: Leakage Prevention Callout */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center space-x-2 text-emerald-700">
              <ShieldCheck className="w-5 h-5 flex-shrink-0" />
              <h4 className="text-xs font-bold uppercase tracking-wider">Zero Data Leakage Protocol</h4>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              In medical AI, data leakage artificially inflates diagnostic accuracy. The AI Preprocessing Agent enforces:
            </p>
            <ul className="text-xs text-slate-600 space-y-2 list-disc pl-4">
              <li>
                <strong>Stratified Split First:</strong> Training (70%), Validation (15%), and Test (15%) partitions are created before any transformation.
              </li>
              <li>
                <strong>Strict Imputation Isolation:</strong> Median and mean values are computed exclusively from training records.
              </li>
              <li>
                <strong>No Re-fitting on Test Set:</strong> Validation and testing cohorts are strictly transformed using training statistics.
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* Step 3 & 4: Review AI Plan */}
      {currentStep >= 3 && currentStep <= 5 && generatedPlan && (
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center space-x-2">
                <span className="badge bg-quantum-50 text-quantum-700 border border-quantum-200 font-semibold">
                  {mode === 'ai' ? 'AI Agent Proposed' : 'User-defined Plan'}
                </span>
                <span className="text-xs text-slate-400">Step 3 &bull; Plan Review</span>
              </div>
              <h2 className="text-lg font-bold text-slate-900 mt-1">Proposed Preprocessing Pipeline</h2>
            </div>
            <div className="text-xs text-emerald-700 font-medium bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200 flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>{generatedPlan.leakage_prevention_guarantee}</span>
            </div>
          </div>

          {/* Plan Steps Accordion / List */}
          <div className="space-y-3">
            {generatedPlan.steps.map((step) => (
              <div
                key={step.step_id}
                className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-start space-x-4"
              >
                <div className="w-6 h-6 rounded-full bg-brand-800 text-white flex items-center justify-center font-bold text-xs flex-shrink-0 mt-0.5">
                  {step.step_id}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900 font-mono">
                      {step.tool_name}
                    </span>
                    <span className="text-[10px] text-slate-400 font-medium">
                      Fit on Train Only: {step.fit_on_train_only ? 'YES (Leak-free)' : 'N/A'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600">{step.rationale}</p>
                  <div className="text-[11px] font-mono text-slate-500 pt-1">
                    Params: {JSON.stringify(step.parameters)}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Plan Approval Actions */}
          <div className="p-4 bg-brand-50/50 border border-brand-200 rounded-xl flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-xs text-slate-700">
                <span className="font-bold text-brand-900 block">Review Before Execution</span>
              <span>Confirm the selected transformations for the uploaded dataset before running them.</span>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setCurrentStep(1)}
                className="btn-secondary text-xs"
              >
                Modify / Re-plan
              </button>
              <button
                onClick={() => executeMutation.mutate()}
                disabled={executeMutation.isPending}
                className="btn-primary text-xs py-2 px-5 flex items-center space-x-2"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{executeMutation.isPending ? 'Executing Pipeline...' : 'Approve & Execute Plan'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 6 & 7: Execution & Leakage Audit Validation */}
      {currentStep >= 6 && executionResult && (
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
          <div className="flex items-center space-x-3 text-emerald-700">
            <div className="p-2 bg-emerald-100 rounded-xl">
              <CheckCircle2 className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Preprocessing Executed Successfully
              </h2>
              <p className="text-xs text-slate-500">
                Run ID: <span className="font-mono text-slate-700">{executionResult.run_id}</span>
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-[11px] text-slate-400 font-medium block">Training Partition (70%)</span>
                <span className="text-xl font-bold text-slate-900">{executionResult.train_samples} Rows</span>
              <span className="text-[10px] text-emerald-600 block mt-1">Imputer & Scaler fit here</span>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-[11px] text-slate-400 font-medium block">Validation Partition (15%)</span>
                <span className="text-xl font-bold text-slate-900">{executionResult.val_samples} Rows</span>
              <span className="text-[10px] text-slate-500 block mt-1">Transformed without refit</span>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-[11px] text-slate-400 font-medium block">Held-out Test Partition (15%)</span>
                <span className="text-xl font-bold text-slate-900">{executionResult.test_samples} Rows</span>
              <span className="text-[10px] text-slate-500 block mt-1">Final evaluation benchmark</span>
            </div>
          </div>

          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs text-emerald-900">
              <ShieldCheck className="w-4 h-4 text-emerald-700 flex-shrink-0" />
              <span><strong>Audit Result:</strong> {executionResult.leakage_audit}</span>
            </div>
            <span className="badge bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold">
              PASSED
            </span>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => {
                setCurrentStep(1);
                setGeneratedPlan(null);
                setExecutionResult(null);
              }}
              className="btn-secondary text-xs flex items-center space-x-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Preprocessing</span>
            </button>
            <Link
              to="/features"
              className="btn-primary text-xs py-2 px-5 flex items-center space-x-2"
            >
              <span>Next: Rank & Select Features</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
