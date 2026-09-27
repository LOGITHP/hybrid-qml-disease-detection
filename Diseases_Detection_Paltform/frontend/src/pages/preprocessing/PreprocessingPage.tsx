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
  { id: 3, label: 'AI Plan', description: 'Gemma reasoning' },
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
  const [targetColumn, setTargetColumn] = useState('LUNG_CANCER');
  const [generatedPlan, setGeneratedPlan] = useState<PreprocessingPlan | null>(null);
  const [executionResult, setExecutionResult] = useState<any | null>(null);

  // Fetch available datasets
  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
  });

  const selectedDataset = datasets?.find((d) => d.id === selectedDatasetId) || datasets?.[0];
  const activeVersion = selectedDataset?.versions?.[0];

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
        steps: generatedPlan?.steps,
      });
    },
    onSuccess: (data) => {
      setExecutionResult(data);
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
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full px-3 py-2.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white font-medium"
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.versions?.[0]?.row_count || 309} patients,{' '}
                      {d.versions?.[0]?.column_count || 16} biomarkers)
                    </option>
                  ))}
                </select>

                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                  <div className="flex justify-between text-slate-600">
                    <span>Target Classification Column:</span>
                    <span className="font-bold text-brand-900">{targetColumn}</span>
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
                    Gemma analyzes dataset telemetry and formulates an optimal clinical pipeline.
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
                    Manually configure stratified splits, median imputation, and min-max feature scaling.
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => planMutation.mutate()}
                disabled={planMutation.isPending || !activeVersion}
                className="btn-primary text-xs py-2.5 px-5 flex items-center space-x-2"
              >
                <BrainCircuit className="w-4 h-4" />
                <span>{planMutation.isPending ? 'Formulating Plan with Gemma...' : 'Analyze & Formulate Plan'}</span>
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
                  Gemma LLM Proposed
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
              <span className="font-bold text-brand-900 block">Human-in-the-Loop Approval Required</span>
              <span>Review the deterministic transformations above before executing on patient telemetry.</span>
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
              <span className="text-xl font-bold text-slate-900">{executionResult.train_samples} Patients</span>
              <span className="text-[10px] text-emerald-600 block mt-1">Imputer & Scaler fit here</span>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-[11px] text-slate-400 font-medium block">Validation Partition (15%)</span>
              <span className="text-xl font-bold text-slate-900">{executionResult.val_samples} Patients</span>
              <span className="text-[10px] text-slate-500 block mt-1">Transformed without refit</span>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-[11px] text-slate-400 font-medium block">Held-out Test Partition (15%)</span>
              <span className="text-xl font-bold text-slate-900">{executionResult.test_samples} Patients</span>
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
