import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Cpu, Database, Filter, Play, Sliders, Atom } from 'lucide-react';
import { datasetsApi, modelsApi, trainingApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

export const TrainingWizardPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [selectedModelId, setSelectedModelId] = useState('');
  const [cValue, setCValue] = useState(1);
  const [vqcLayers, setVqcLayers] = useState(2);
  const [vqcEpochs, setVqcEpochs] = useState(5);

  const { data: datasets, isLoading: datasetsLoading } = useQuery({ queryKey: ['datasets'], queryFn: datasetsApi.list });
  const { data: models, isLoading: modelsLoading } = useQuery({ queryKey: ['defaultModels'], queryFn: modelsApi.listDefaults });

  const storedVersionId = sessionStorage.getItem('activeDatasetVersionId');
  const pipelineVersionId = sessionStorage.getItem('activeDatasetVersionId');
  const featureSelectionRunId = sessionStorage.getItem('activeFeatureSelectionRunId');
  const preprocessingRunId = sessionStorage.getItem('activePreprocessingRunId');
  const targetColumn = sessionStorage.getItem('activeTargetColumn');
  const selectedFeatures = (() => {
    try { return JSON.parse(sessionStorage.getItem('activeSelectedFeatures') || '[]') as string[]; }
    catch { return []; }
  })();

  const activeDataset = datasets?.find((dataset) => dataset.id === selectedDatasetId)
    || datasets?.find((dataset) => dataset.versions?.some((version) => version.id === storedVersionId))
    || datasets?.[0];
  const activeVersion = activeDataset?.versions?.find((version) => version.id === storedVersionId)
    || [...(activeDataset?.versions || [])].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))[0];
  const recommendedModel = models?.find((model) => model.model_type === 'svm_linear') || models?.[0];
  const activeModel = models?.find((model) => model.id === selectedModelId) || recommendedModel;
  const pipelineReady = !!activeVersion && pipelineVersionId === activeVersion.id
    && !!featureSelectionRunId && !!preprocessingRunId && selectedFeatures.length > 0;

  const trainMutation = useMutation({
    mutationFn: async () => {
      if (!activeModel || !activeVersion || !featureSelectionRunId || !preprocessingRunId || !pipelineReady) {
        throw new Error('Run preprocessing and feature selection for this uploaded dataset first.');
      }
      const hyperparameters = activeModel.model_type === 'vqc'
        ? { layers: vqcLayers, epochs: vqcEpochs }
        : { C: cValue, gamma: 'scale' };
      return trainingApi.startRun({
        model_id: activeModel.id,
        dataset_version_id: activeVersion.id,
        feature_selection_run_id: featureSelectionRunId,
        preprocessing_run_id: preprocessingRunId,
        hyperparameters,
      });
    },
    onSuccess: (run) => navigate(`/training/${run.id}`),
  });

  if (datasetsLoading || modelsLoading) return <LoadingSkeleton rows={4} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 border-b border-slate-200 pb-4">
        <Cpu className="h-5 w-5 text-quantum-600" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Train on the selected upload</h1>
          <p className="text-xs text-slate-500">The saved preprocessing and feature-selection runs define the data sent to the estimator.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Uploaded dataset and target</h2>
            <label className="block space-y-1 text-xs font-semibold text-slate-700">
              Dataset
              <select value={activeDataset?.id || ''} onChange={(event) => setSelectedDatasetId(event.target.value)} className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal">
                {(datasets || []).map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Version</span><span className="font-mono font-semibold">{activeVersion?.version_tag || 'No uploaded version'}</span></div>
              <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Dimensions</span><span className="font-semibold">{activeVersion?.row_count ?? '—'} rows · {activeVersion?.column_count ?? '—'} columns</span></div>
              <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Target</span><span className="font-mono font-semibold">{targetColumn || 'Choose in Feature Selection'}</span></div>
              <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Selected feature columns</span><span className="font-semibold">{selectedFeatures.length}</span></div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">
              <span className="mb-1 block text-slate-500">Features</span>
              <span className="break-words font-mono">{selectedFeatures.length ? selectedFeatures.join(', ') : 'No feature-selection run saved for this version.'}</span>
            </div>
            {!pipelineReady && <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
              Complete preprocessing and feature selection on the same dataset version before training.
              <div className="mt-2 flex gap-3 font-semibold"><Link to="/preprocessing" className="underline">Preprocessing</Link><Link to="/features" className="underline">Feature selection</Link></div>
            </div>}
          </section>

          <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Built-in model templates</h2>
            <p className="text-[11px] text-slate-500">Templates are fitted to this upload at training time; they do not contain transferable pretrained weights.</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {(models || []).map((model) => {
                const selected = (selectedModelId || recommendedModel?.id) === model.id;
                const quantum = model.model_type === 'vqc';
                return <button key={model.id} type="button" onClick={() => setSelectedModelId(model.id)} className={`rounded-xl border p-4 text-left transition-colors ${selected ? 'border-brand-800 bg-brand-50' : 'border-slate-200 hover:border-slate-300'}`}>
                  <div className="mb-2 flex items-center justify-between gap-2"><span className="text-xs font-bold text-slate-900">{model.name}</span><StatusBadge status={quantum ? 'VQC' : model.model_type.replace('svm_', 'SVM ').toUpperCase()} size="sm" /></div>
                  <p className="text-[11px] text-slate-500">{model.description}</p>
                  {model.id === recommendedModel?.id && <span className="mt-2 block text-[10px] font-semibold text-emerald-700">Default tabular baseline</span>}
                </button>;
              })}
            </div>
            {activeModel?.model_type === 'vqc' ? <div className="grid grid-cols-2 gap-3 text-xs">
              <label className="space-y-1">Variational layers<input type="number" min={1} max={5} value={vqcLayers} onChange={(event) => setVqcLayers(Number(event.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
              <label className="space-y-1">Epochs<input type="number" min={1} max={100} value={vqcEpochs} onChange={(event) => setVqcEpochs(Number(event.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
            </div> : <label className="block max-w-xs space-y-1 text-xs">SVM regularization (C)<input type="number" min={0.001} step={0.1} value={cValue} onChange={(event) => setCValue(Number(event.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2" /></label>}
          </section>
        </div>

        <aside className="card-scientific h-fit space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Experiment summary</h2>
          <div className="space-y-3 text-xs">
            <div className="flex items-center gap-2"><Database className="h-4 w-4 text-slate-500" /><span>{activeDataset?.name || 'No dataset selected'}</span></div>
            <div className="flex items-center gap-2"><Filter className="h-4 w-4 text-slate-500" /><span>{selectedFeatures.length} selected feature columns</span></div>
            <div className="flex items-center gap-2">{activeModel?.model_type === 'vqc' ? <Atom className="h-4 w-4 text-quantum-600" /> : <Sliders className="h-4 w-4 text-slate-500" />}<span>{activeModel?.name || 'Loading model templates'}</span></div>
            <p className="border-t border-slate-100 pt-3 text-slate-500">Evaluation uses a held-out test partition from the saved pipeline settings.</p>
          </div>
          {trainMutation.isError && <p className="text-xs text-red-700">{trainMutation.error instanceof Error ? trainMutation.error.message : 'Training failed for this upload.'}</p>}
          <button type="button" onClick={() => trainMutation.mutate()} disabled={trainMutation.isPending || !pipelineReady || !activeModel} className="btn-primary flex w-full items-center justify-center gap-2 py-3 text-xs shadow-md">
            <Play className="h-4 w-4" /><span>{trainMutation.isPending ? 'Training on uploaded data…' : 'Start training run'}</span>
          </button>
        </aside>
      </div>
    </div>
  );
};
