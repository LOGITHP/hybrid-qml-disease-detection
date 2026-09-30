import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { AlertTriangle, Atom, CheckCircle2, ChevronRight, Cpu, Database, Filter, Play, Sliders } from 'lucide-react';
import { datasetsApi, featuresApi, modelsApi, trainingApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

// ── Pipeline gate step ────────────────────────────────────────────────────────
function PipelineStep({
  step,
  label,
  done,
  active,
  link,
}: {
  step: number;
  label: string;
  done: boolean;
  active: boolean;
  link?: string;
}) {
  return (
    <div className={`flex items-center gap-2 text-xs ${active ? 'font-bold text-slate-900' : done ? 'text-slate-500' : 'text-slate-400'}`}>
      {done ? (
        <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
      ) : active ? (
        <span className="h-4 w-4 flex items-center justify-center rounded-full border-2 border-brand-700 text-brand-700 text-[10px] font-bold shrink-0">{step}</span>
      ) : (
        <span className="h-4 w-4 flex items-center justify-center rounded-full border-2 border-slate-300 text-slate-400 text-[10px] shrink-0">{step}</span>
      )}
      {link && !done ? (
        <Link to={link} className="underline text-brand-700">{label}</Link>
      ) : (
        <span>{label}</span>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
export const TrainingWizardPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedVersionId, setSelectedVersionId] = useState(() => sessionStorage.getItem('activeDatasetVersionId') || '');
  const [selectedFSRunId, setSelectedFSRunId] = useState(() => sessionStorage.getItem('activeFeatureSelectionRunId') || '');
  const [selectedModelId, setSelectedModelId] = useState(() => new URLSearchParams(window.location.search).get('model_id') || '');
  const [cValue, setCValue] = useState(1);
  const [vqcLayers, setVqcLayers] = useState(2);
  const [vqcEpochs, setVqcEpochs] = useState(5);
  const [customName, setCustomName] = useState('');

  // ── fetch data ───────────────────────────────────────────────────────────
  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
  });
  const { data: defaultModels, isLoading: modelsLoading } = useQuery({
    queryKey: ['defaultModels'],
    queryFn: modelsApi.listDefaults,
  });
  // All feature selection runs for the chosen dataset version
  const { data: fsRuns, isLoading: fsLoading } = useQuery({
    queryKey: ['fsRuns', selectedVersionId],
    queryFn: () => featuresApi.listRuns(selectedVersionId),
    enabled: !!selectedVersionId,
  });

  // ── derive active objects ────────────────────────────────────────────────
  const allVersions = (datasets || []).flatMap((ds) =>
    (ds.versions || []).map((v) => ({ ...v, datasetName: ds.name, datasetId: ds.id }))
  );
  const activeVersion = allVersions.find((v) => v.id === selectedVersionId);
  const activeDataset = datasets?.find((ds) => ds.id === activeVersion?.datasetId);

  // The currently selected FS run
  const activeFSRun = (fsRuns || []).find((r: any) => r.id === selectedFSRunId);
  const selectedFeatures: string[] = activeFSRun?.selected_features || [];
  const targetColumn: string = activeFSRun?.target_column || sessionStorage.getItem('activeTargetColumn') || '';
  const preprocessingRunId = sessionStorage.getItem('activePreprocessingRunId') || '';

  // ── pipeline status flags ────────────────────────────────────────────────
  const processingStatus = activeVersion?.dataset_metadata?.processing_status || {};
  const isUploaded = true; // if we have a version, it's uploaded
  const isPreprocessed = !!processingStatus.preprocessed || !!preprocessingRunId;
  const isFeatureSelected = !!processingStatus.feature_selection || !!fsRuns?.length;
  const pipelineReady =
    !!activeVersion &&
    isPreprocessed &&
    isFeatureSelected &&
    !!selectedFSRunId &&
    !!preprocessingRunId &&
    selectedFeatures.length > 0;

  // ── when version changes, reset downstream FS run ─────────────────────
  useEffect(() => {
    // if fsRuns loaded and we don't have a valid selection, pick the latest
    if (fsRuns && fsRuns.length > 0 && (!selectedFSRunId || !fsRuns.find((r: any) => r.id === selectedFSRunId))) {
      const latest = fsRuns[0];
      setSelectedFSRunId(latest.id);
      sessionStorage.setItem('activeFeatureSelectionRunId', latest.id);
      sessionStorage.setItem('activeSelectedFeatures', JSON.stringify(latest.selected_features || []));
      sessionStorage.setItem('activeTargetColumn', latest.target_column || '');
    }
  }, [fsRuns, selectedFSRunId]);

  // ── selectable model templates ──────────────────────────────────────────
  const selectableModels = (defaultModels || []).filter((model) => {
    const config = model.configuration || {};
    if (!config.pretrained) return true;
    // For pretrained checkpoints: only show if target + feature set match
    const checkpointFeatures = Array.isArray(config.selected_features) ? config.selected_features as string[] : [];
    return (
      checkpointFeatures.length === selectedFeatures.length &&
      checkpointFeatures.every((f: string, i: number) => f === selectedFeatures[i])
    );
  });
  const activeModel = selectableModels.find((m) => m.id === selectedModelId) || selectableModels[0];
  useEffect(() => {
    if (!selectedModelId && selectableModels.length > 0) {
      setSelectedModelId(selectableModels[0].id);
    }
  }, [selectableModels.length]);

  // ── training mutation ───────────────────────────────────────────────────
  const trainMutation = useMutation({
    mutationFn: async () => {
      if (!activeModel || !activeVersion || !selectedFSRunId || !preprocessingRunId || !pipelineReady) {
        throw new Error('Complete preprocessing and feature selection on this dataset version first.');
      }
      let circuit: Record<string, unknown> = {};
      try { circuit = JSON.parse(sessionStorage.getItem('vqc_circuit_config') || '{}'); } catch { circuit = {}; }
      const hyperparameters = activeModel.model_type === 'vqc'
        ? { layers: vqcLayers, epochs: vqcEpochs, ...circuit }
        : { C: cValue, gamma: 'scale' };
      return trainingApi.startRun({
        model_id: activeModel.id,
        dataset_version_id: activeVersion.id,
        feature_selection_run_id: selectedFSRunId,
        preprocessing_run_id: preprocessingRunId,
        hyperparameters,
        is_noisy_quantum: activeModel.model_type === 'vqc' && circuit.backend_type === 'default.mixed',
        noise_params:
          activeModel.model_type === 'vqc' && circuit.backend_type === 'default.mixed'
            ? (circuit.noise_params as Record<string, number> | undefined)
            : undefined,
        custom_name: customName.trim() || undefined,
      });
    },
    onSuccess: (run) => navigate(`/training/${run.id}`),
  });

  if (datasetsLoading || modelsLoading) return <LoadingSkeleton rows={4} />;

  // ── render ──────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-slate-200 pb-4">
        <Cpu className="h-5 w-5 text-quantum-600 shrink-0" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Train a Model</h1>
          <p className="text-xs text-slate-500">Preprocessing and feature selection must be complete before training.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">

          {/* ── Step 1: Dataset ─────────────────────────────────────────── */}
          <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-slate-500" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Dataset &amp; Version</h2>
            </div>

            <select
              value={selectedVersionId}
              onChange={(e) => {
                const verId = e.target.value;
                setSelectedVersionId(verId);
                setSelectedFSRunId('');
                sessionStorage.setItem('activeDatasetVersionId', verId);
                sessionStorage.removeItem('activePreprocessingRunId');
                sessionStorage.removeItem('activeFeatureSelectionRunId');
                sessionStorage.removeItem('activeTargetColumn');
                sessionStorage.removeItem('activeSelectedFeatures');
              }}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="" disabled>Select a dataset version</option>
              {(datasets || []).map((ds) => (
                <optgroup key={ds.id} label={ds.name}>
                  {(ds.versions || []).map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.version_tag} · {v.row_count ?? '?'} rows
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>

            {activeVersion && (
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="rounded-lg bg-slate-50 p-3">
                  <span className="block text-slate-500">Dataset</span>
                  <span className="font-semibold truncate block">{activeDataset?.name || '—'}</span>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <span className="block text-slate-500">Dimensions</span>
                  <span className="font-semibold">{activeVersion.row_count ?? '—'} rows · {activeVersion.column_count ?? '—'} cols</span>
                </div>
              </div>
            )}

            {/* ── Pipeline gate ────────────────────────────────────────── */}
            {selectedVersionId && (
              <div className="space-y-2 border-t border-slate-100 pt-3">
                <p className="text-[11px] font-bold uppercase text-slate-500 tracking-wider">Pipeline status</p>
                <div className="space-y-1.5">
                  <PipelineStep step={1} label="Upload" done={isUploaded} active={false} />
                  <div className="flex items-center gap-1 text-slate-300 text-xs pl-2"><ChevronRight className="h-3 w-3" /></div>
                  <PipelineStep step={2} label="Preprocessing" done={isPreprocessed} active={!isPreprocessed} link="/preprocessing" />
                  <div className="flex items-center gap-1 text-slate-300 text-xs pl-2"><ChevronRight className="h-3 w-3" /></div>
                  <PipelineStep step={3} label="Feature Selection" done={isFeatureSelected} active={isPreprocessed && !isFeatureSelected} link="/features" />
                  <div className="flex items-center gap-1 text-slate-300 text-xs pl-2"><ChevronRight className="h-3 w-3" /></div>
                  <PipelineStep step={4} label="Training" done={false} active={pipelineReady} />
                </div>
                {!isPreprocessed && (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 flex gap-2">
                    <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                    <span>Preprocess this dataset version first before running feature selection or training.</span>
                  </div>
                )}
                {isPreprocessed && !isFeatureSelected && (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 flex gap-2">
                    <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                    <span>Run feature selection on this version before training.</span>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* ── Step 2: Feature Selection Run picker ─────────────────────── */}
          {isFeatureSelected && fsRuns && fsRuns.length > 0 && (
            <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-slate-500" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Feature Selection Run</h2>
                <span className="ml-auto text-[11px] text-slate-400">{fsRuns.length} saved run{fsRuns.length !== 1 ? 's' : ''}</span>
              </div>

              <div className="space-y-2">
                {fsRuns.map((run: any) => {
                  const selected = selectedFSRunId === run.id;
                  const feats: string[] = run.selected_features || [];
                  const method = run.ranking_method || 'manual';
                  const dateStr = run.created_at ? new Date(run.created_at).toLocaleString() : '—';
                  return (
                    <label
                      key={run.id}
                      className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 text-xs transition-colors ${
                        selected ? 'border-brand-800 bg-brand-50' : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="fsRun"
                        checked={selected}
                        onChange={() => {
                          setSelectedFSRunId(run.id);
                          sessionStorage.setItem('activeFeatureSelectionRunId', run.id);
                          sessionStorage.setItem('activeSelectedFeatures', JSON.stringify(feats));
                          sessionStorage.setItem('activeTargetColumn', run.target_column || '');
                        }}
                        className="mt-0.5 accent-brand-800"
                      />
                      <span className="flex-1 min-w-0">
                        <span className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-slate-900">{feats.length} features</span>
                          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-mono text-slate-600">{method}</span>
                          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-mono text-slate-600">target: {run.target_column || '—'}</span>
                        </span>
                        <span className="block text-slate-500 mt-0.5 font-mono text-[10px]">{feats.join(', ')}</span>
                        <span className="block text-slate-400 mt-0.5">{dateStr}</span>
                      </span>
                    </label>
                  );
                })}
              </div>

              {activeFSRun && (
                <div className="rounded-lg bg-slate-50 border border-slate-100 p-3 text-xs">
                  <span className="text-slate-500">Target: </span>
                  <span className="font-mono font-semibold">{targetColumn}</span>
                  <span className="mx-2 text-slate-300">·</span>
                  <span className="text-slate-500">Features: </span>
                  <span className="font-semibold">{selectedFeatures.length}</span>
                </div>
              )}
            </section>
          )}

          {/* ── Step 3: Model template ───────────────────────────────────── */}
          {pipelineReady && (
            <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2">
                <Sliders className="h-4 w-4 text-slate-500" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Model Template</h2>
              </div>
              <p className="text-[11px] text-slate-500">
                Pretrained checkpoints only appear when target and feature set match exactly.
              </p>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {selectableModels.map((model) => {
                  const selected = activeModel?.id === model.id;
                  const quantum = model.model_type === 'vqc';
                  return (
                    <button
                      key={model.id}
                      type="button"
                      onClick={() => setSelectedModelId(model.id)}
                      className={`rounded-xl border p-4 text-left transition-colors ${
                        selected ? 'border-brand-800 bg-brand-50' : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-slate-900">{model.name}</span>
                        <StatusBadge status={quantum ? 'VQC' : model.model_type.replace('svm_', 'SVM ').toUpperCase()} size="sm" />
                      </div>
                      <p className="text-[11px] text-slate-500">{model.description}</p>
                    </button>
                  );
                })}
              </div>

              {activeModel?.model_type === 'vqc' ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <label className="space-y-1">
                      Variational layers
                      <input type="number" min={1} max={5} value={vqcLayers} onChange={(e) => setVqcLayers(Number(e.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                    </label>
                    <label className="space-y-1">
                      Epochs
                      <input type="number" min={1} max={100} value={vqcEpochs} onChange={(e) => setVqcEpochs(Number(e.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                    </label>
                  </div>
                  <Link to="/models/vqc/configure" className="inline-flex items-center gap-2 rounded-lg border border-quantum-200 bg-quantum-50 px-3.5 py-2 text-xs font-semibold text-quantum-700 transition-colors hover:bg-quantum-100">
                    <Atom className="h-4 w-4" /><span>Configure Advanced VQC Settings</span>
                  </Link>
                </div>
              ) : (
                <label className="block max-w-xs space-y-1 text-xs">
                  SVM Regularization (C)
                  <input type="number" min={0.001} step={0.1} value={cValue} onChange={(e) => setCValue(Number(e.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                </label>
              )}
            </section>
          )}
        </div>

        {/* ── Sidebar: Experiment summary ─────────────────────────────────── */}
        <aside className="card-scientific h-fit space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Experiment Summary</h2>
          <div className="space-y-3 text-xs">
            <div className="flex items-start gap-2">
              <Database className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <span className="block text-slate-500">Dataset</span>
                <span className="font-semibold">{activeDataset?.name || '—'}</span>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Filter className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <span className="block text-slate-500">Feature set</span>
                <span className="font-semibold">{selectedFeatures.length ? `${selectedFeatures.length} columns` : 'Not selected'}</span>
                {targetColumn && <span className="block text-slate-400">Target: <span className="font-mono">{targetColumn}</span></span>}
              </div>
            </div>
            <div className="flex items-start gap-2">
              {activeModel?.model_type === 'vqc' ? (
                <Atom className="h-4 w-4 text-quantum-600 shrink-0 mt-0.5" />
              ) : (
                <Sliders className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
              )}
              <div>
                <span className="block text-slate-500">Model template</span>
                <span className="font-semibold">{activeModel?.name || '—'}</span>
              </div>
            </div>
            <p className="border-t border-slate-100 pt-3 text-slate-500">
              Evaluation uses a held-out test partition (20%) from the saved pipeline settings.
            </p>
          </div>

          <div className="border-t border-slate-100 pt-3">
            <label className="block space-y-1 text-xs font-semibold text-slate-700">
              Custom Model Name <span className="font-normal text-slate-400">(optional)</span>
              <input
                type="text"
                placeholder="e.g. Lung-Cancer-VQC-v3"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </label>
          </div>

          {trainMutation.isError && (
            <p className="text-xs text-red-700">
              {trainMutation.error instanceof Error ? trainMutation.error.message : 'Training failed.'}
            </p>
          )}

          <button
            type="button"
            onClick={() => trainMutation.mutate()}
            disabled={trainMutation.isPending || !pipelineReady || !activeModel}
            className="btn-primary mt-2 flex w-full items-center justify-center gap-2 py-3 text-xs shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="h-4 w-4" />
            <span>{trainMutation.isPending ? 'Training…' : 'Start Training Run'}</span>
          </button>

          {!pipelineReady && selectedVersionId && (
            <p className="text-[11px] text-amber-700 text-center">
              Complete all pipeline steps above to enable training.
            </p>
          )}
        </aside>
      </div>
    </div>
  );
};
