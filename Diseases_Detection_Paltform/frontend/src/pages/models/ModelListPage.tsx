import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Activity, ArrowRight, Atom, BarChart3, Download, Layers, Search, Trash2 } from 'lucide-react';
import { modelsApi } from '../../api';
import { Model } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

const formatPercent = (value: unknown) => typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : '—';

const saveBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
};

export const ModelListPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [modelType, setModelType] = useState('all');
  const [modelStatus, setModelStatus] = useState('all');
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [frameworkFilter, setFrameworkFilter] = useState('all');
  const [datasetFilter, setDatasetFilter] = useState('all');
  const [dateSort, setDateSort] = useState('newest');

  const { data: defaults, isLoading: defaultsLoading } = useQuery({ queryKey: ['defaultModels'], queryFn: modelsApi.listDefaults });
  const { data: userModels, isLoading: userModelsLoading } = useQuery({ queryKey: ['userModels'], queryFn: modelsApi.list });
  const isLoading = defaultsLoading || userModelsLoading;
  const unique = <T extends Model>(list: T[]) => list.filter((model, index, all) => all.findIndex((candidate) => candidate.id === model.id) === index);
  const pretrainedModels = unique((defaults || []).filter((model) => !!model.configuration?.pretrained));

  // Also list pretrained models inside the filterable view if we want, but the prompt says "Allow models to be organized/filterable... Do not create duplicate model records". The user likely meant the main list of models.
  const trainedModels = unique((userModels || []).filter((model) => ['trained', 'candidate'].includes(model.status || '')));

  // Extract unique values for filters
  const types = [...new Set(trainedModels.map((model) => model.model_type))];
  const datasets = [...new Set(trainedModels.map((m) => m.configuration?.dataset_id || m.configuration?.dataset_version_id).filter(Boolean))];
  const frameworks = [...new Set(trainedModels.map((m) => m.configuration?.framework || (m.model_type.includes('vqc') ? 'PennyLane' : 'scikit-learn')))];

  const filteredModels = useMemo(() => {
    let result = trainedModels.filter((model) => {
      const config = model.configuration || {};

      const matchesType = modelType === 'all' || model.model_type === modelType;
      const matchesStatus = modelStatus === 'all' || model.status === modelStatus;

      const isQuantum = model.model_type.toLowerCase().includes('vqc') || model.model_type.toLowerCase().includes('qml');
      const matchesCategory = categoryFilter === 'all' ||
        (categoryFilter === 'quantum' && isQuantum) ||
        (categoryFilter === 'classical' && !isQuantum);

      const fw = config.framework || (isQuantum ? 'PennyLane' : 'scikit-learn');
      const matchesFramework = frameworkFilter === 'all' || fw === frameworkFilter;

      const ds = config.dataset_id || config.dataset_version_id;
      const matchesDataset = datasetFilter === 'all' || ds === datasetFilter;

      const searchable = [
        model.name,
        config.dataset_id,
        config.dataset_version_id,
        config.model_version,
        ...(config.selected_features || [])
      ].join(' ').toLowerCase();

      const matchesSearch = search === '' || searchable.includes(search.toLowerCase());

      return matchesType && matchesStatus && matchesCategory && matchesFramework && matchesDataset && matchesSearch;
    });

    // Date sorting
    result.sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return dateSort === 'newest' ? dateB - dateA : dateA - dateB;
    });

    return result;
  }, [trainedModels, modelType, modelStatus, categoryFilter, frameworkFilter, datasetFilter, search, dateSort]);

  const downloadMutation = useMutation({
    mutationFn: async (model: Model) => ({ model, blob: await modelsApi.downloadArtifact(model.id) }),
    onSuccess: ({ model, blob }) => saveBlob(blob, `${model.name.replace(/[^a-z0-9-_]+/gi, '_')}.joblib`),
  });
  const deleteMutation = useMutation({
    mutationFn: modelsApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['userModels'] }),
  });

  if (isLoading) return <LoadingSkeleton rows={5} />;

  const ModelMetrics = ({ model }: { model: Model }) => {
    const metrics = (model.configuration?.metrics || {}) as Record<string, unknown>;
    const entries: Array<[string, unknown]> = [['Accuracy', metrics.accuracy], ['Balanced accuracy', metrics.balanced_accuracy], ['Sensitivity', metrics.sensitivity], ['Specificity', metrics.specificity], ['Precision', metrics.precision], ['F1 score', metrics.f1_score]];
    return <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">{entries.map(([label, value]) => <div key={String(label)} className="rounded-lg bg-slate-50 p-2.5 text-xs"><span className="block text-[10px] text-slate-500">{label}</span><b>{formatPercent(value)}</b></div>)}<div className="rounded-lg bg-quantum-50 p-2.5 text-xs"><span className="block text-[10px] text-quantum-700">ROC-AUC</span><b>{typeof metrics.roc_auc === 'number' ? metrics.roc_auc.toFixed(3) : '—'}</b></div></div>;
  };

  return <div className="space-y-8">
    <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-4 sm:flex-row sm:items-center">
      <div><div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-brand-700"><Layers className="h-4 w-4 text-quantum-600" /><span>Model Configuration</span></div><h1 className="text-2xl font-bold tracking-tight text-slate-900">Models and measured results</h1><p className="text-xs text-slate-500">Source checkpoint metrics stay separate from evaluation results produced on your uploaded data.</p></div>
      <Link to="/evaluation/comparison" className="btn-primary flex items-center gap-2 text-xs"><BarChart3 className="h-4 w-4" /><span>Compare trained models</span></Link>
    </header>

    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-slate-800">Pretrained Checkpoints</h2>
        <p className="text-xs text-slate-500">These existing checkpoints keep their original benchmark metrics. Evaluate a compatible checkpoint against an uploaded dataset to create a separate, traceable result.</p>
      </div>
      {!pretrainedModels.length ? <div className="card-scientific rounded-xl border border-slate-200 bg-white py-10 text-center text-xs text-slate-500">No pretrained checkpoints are registered.</div> : <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">{pretrainedModels.map((model) => {
        const config = model.configuration || {};
        const metrics = config.metrics || {};
        return <article key={model.id} className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-md hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <h3 className="font-bold text-lg text-slate-900 flex items-center gap-2"><Atom className="w-4 h-4 text-brand-600"/>{model.name}</h3>
            <StatusBadge status={model.model_type} size="sm" />
          </div>
          <div><p className="text-xs text-slate-600 leading-relaxed">{model.description}</p></div>

          <div className="rounded-lg bg-slate-50 p-3 border border-slate-100 space-y-2">
            <div className="flex items-start gap-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider w-20">Source</span>
              <span className="text-xs font-medium text-slate-800">{String(config.source_experiment || config.source || 'Experimental_ML')}</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider w-20">Framework</span>
              <span className="text-xs font-medium text-slate-800">{String(config.framework || (model.model_type === 'vqc' ? 'PennyLane' : 'scikit-learn'))}</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider w-20">Input schema</span>
              <span className="text-[10px] font-mono text-brand-700 bg-brand-50 px-1.5 py-0.5 rounded break-all border border-brand-100">
                LUNG_CANCER · {Array.isArray(config.selected_features) ? config.selected_features.join(' → ') : 'checkpoint feature order'} · MinMax scaling
              </span>
            </div>
          </div>

          <div className="pt-2">
            <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">Original Benchmark Metrics</h4>
            <ModelMetrics model={{ ...model, configuration: { ...config, metrics } }} />
            <p className="text-[10px] text-slate-400 mt-2">Tested on {String(metrics.test_samples ?? '—')} validation samples.</p>
          </div>

          <div className="flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-4">
            <Link to={`/models/${model.id}`} className="btn-secondary px-3 py-1.5 text-xs font-semibold">Details</Link>
          </div>
        </article>;
      })}</div>}
    </section>

    <section className="space-y-4">
      <div><h2 className="text-lg font-bold text-slate-800">Your trained models</h2><p className="text-xs text-slate-500">Each entry traces to its dataset version, approved preprocessing, feature set, configuration, and held-out metrics.</p></div>
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-4 shadow-sm">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="relative lg:col-span-2">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search features, version, dataset, or model name"
              className="w-full rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-xs focus:ring-brand-500 focus:border-brand-500"
            />
          </label>
          <select value={dateSort} onChange={(e) => setDateSort(e.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs focus:ring-brand-500 focus:border-brand-500">
            <option value="newest">Sort by Date: Newest</option>
            <option value="oldest">Sort by Date: Oldest</option>
          </select>
          <select value={modelStatus} onChange={(event) => setModelStatus(event.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs focus:ring-brand-500 focus:border-brand-500">
            <option value="all">Status: All</option>
            <option value="trained">Validated</option>
            <option value="candidate">Candidate</option>
          </select>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 pt-4 border-t border-slate-200">
          <select value={datasetFilter} onChange={(e) => setDatasetFilter(e.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs focus:ring-brand-500 focus:border-brand-500">
            <option value="all">Dataset: All</option>
            {datasets.map(ds => <option key={ds as string} value={ds as string}>{ds as string}</option>)}
          </select>
          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs focus:ring-brand-500 focus:border-brand-500">
            <option value="all">Paradigm: All</option>
            <option value="classical">Classical</option>
            <option value="quantum">Quantum / Hybrid</option>
          </select>
          <select value={modelType} onChange={(event) => setModelType(event.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs focus:ring-brand-500 focus:border-brand-500">
            <option value="all">Algorithm: All</option>
            {types.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
          <select value={frameworkFilter} onChange={(e) => setFrameworkFilter(e.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs focus:ring-brand-500 focus:border-brand-500">
            <option value="all">Framework: All</option>
            {frameworks.map(fw => <option key={fw as string} value={fw as string}>{fw as string}</option>)}
          </select>
        </div>
      </div>
      {(downloadMutation.isError || deleteMutation.isError) && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800">{downloadMutation.error?.message || deleteMutation.error?.message}</p>}
      {!filteredModels.length ? <div className="card-scientific rounded-xl border border-slate-200 bg-white py-10 text-center text-xs text-slate-500">{trainedModels.length ? 'No trained models match those filters.' : 'No model has been trained on an uploaded dataset yet.'}</div> : <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">{filteredModels.map((model) => {
        const config = model.configuration || {};
        const metrics = (config.metrics || {}) as Record<string, unknown>;
        const features = Array.isArray(config.selected_features) ? config.selected_features as string[] : [];
        const isCandidate = model.status === 'candidate';
        const isCheckpointEvaluation = Boolean(config.pretrained_used);
        return <article key={model.id} className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-3"><div><div className="mb-1 flex items-center gap-2"><StatusBadge status={model.model_type} size="sm" /><span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${isCandidate ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>{isCandidate ? 'Candidate · review required' : isCheckpointEvaluation ? 'Checkpoint evaluated on upload' : 'Trained on upload'}</span></div><h3 className="text-base font-bold text-slate-900">{model.name}</h3><p className="mt-1 text-[11px] text-slate-500">{model.description}</p></div><Link to={`/models/${model.id}`} className="btn-secondary shrink-0 text-xs">Details</Link></div>
          <div className="grid grid-cols-2 gap-2 text-[11px] sm:grid-cols-4"><div className="rounded bg-slate-50 p-2"><span className="block text-slate-500">Dataset version</span><b className="break-all font-mono">{String(config.dataset_version_id || '—')}</b></div><div className="rounded bg-slate-50 p-2"><span className="block text-slate-500">Features</span><b>{features.length}</b></div><div className="rounded bg-slate-50 p-2"><span className="block text-slate-500">Preprocessing</span><b className="break-all font-mono">{String(config.preprocessing_run_id || '—')}</b></div><div className="rounded bg-slate-50 p-2"><span className="block text-slate-500">Version / date</span><b>v{String(config.model_version || 1)} · {new Date(model.created_at).toLocaleDateString()}</b></div></div>
          <div className="rounded-lg bg-slate-50 p-3"><span className="mb-2 block text-[10px] font-semibold uppercase text-slate-500">Selected features</span><span className="font-mono text-[11px] text-slate-700">{features.join(', ') || 'Not recorded'}</span></div>
          <ModelMetrics model={model} />
          {model.model_type === 'vqc' && (() => {
            const qc = config.quantum_config || {};
            const qubits = qc.n_qubits || 4;
            const layers = qc.n_layers || 2;
            const isNoisy = qc.is_noisy;
            return (
              <div className="rounded-xl border border-quantum-200 bg-slate-900 p-4 shadow-inner overflow-x-auto select-none">
                <div className="flex items-center justify-between mb-3 min-w-max">
                  <div className="flex items-center space-x-2">
                    <Atom className="w-4 h-4 text-quantum-400" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-quantum-200">Quantum Circuit ({qubits} Qubits, {layers} Layers)</span>
                  </div>
                  {isNoisy && <span className="text-[9px] bg-red-900/50 text-red-300 px-1.5 py-0.5 rounded border border-red-700/50 font-bold uppercase tracking-wider">Noisy Simulator</span>}
                </div>
                <div className="inline-flex flex-col gap-2 min-w-max">
                  {Array.from({ length: qubits }).map((_, qIdx) => (
                    <div key={qIdx} className="flex items-center h-6 group">
                      <div className="w-8 flex items-center pr-2 font-mono text-[10px] text-slate-400">
                        |q{qIdx}⟩
                      </div>
                      <div className="flex items-center space-x-1">
                        <div className="flex items-center">
                          <div className="w-3 h-px bg-slate-600"></div>
                          <div className="w-8 h-6 bg-blue-900/50 border border-blue-500/50 rounded flex items-center justify-center shadow-[0_0_8px_rgba(59,130,246,0.15)]">
                            <span className="text-[9px] font-mono text-blue-200">RY</span>
                          </div>
                          <div className="w-3 h-px bg-slate-600"></div>
                        </div>
                        {Array.from({ length: layers }).map((_, lIdx) => (
                          <React.Fragment key={`l_${lIdx}_q_${qIdx}`}>
                            <div className="flex items-center">
                              <div className="w-8 h-6 bg-purple-900/50 border border-purple-500/50 rounded flex items-center justify-center shadow-[0_0_8px_rgba(168,85,247,0.15)]">
                                <span className="text-[9px] font-mono text-purple-200">RY</span>
                              </div>
                              <div className="w-2 h-px bg-slate-600"></div>
                            </div>
                            {qIdx < qubits - 1 ? (
                              <div className="flex items-center relative w-6 h-6">
                                <div className="w-full h-px bg-slate-600 absolute top-1/2"></div>
                                <div className="w-1.5 h-1.5 rounded-full bg-quantum-400 absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 z-10"></div>
                                <div className="w-px h-6 bg-quantum-400/50 absolute left-1/2 translate-y-1/2"></div>
                              </div>
                            ) : (
                              <div className="flex items-center relative w-6 h-6">
                                <div className="w-full h-px bg-slate-600 absolute top-1/2"></div>
                                <div className="w-3 h-3 border border-quantum-400 rounded-full absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 z-10 flex items-center justify-center bg-slate-900">
                                  <div className="w-px h-full bg-quantum-400"></div>
                                  <div className="h-px w-full bg-quantum-400 absolute"></div>
                                </div>
                                <div className="w-px h-1/2 bg-quantum-400/50 absolute left-1/2 top-0"></div>
                              </div>
                            )}
                            <div className="w-2 h-px bg-slate-600"></div>
                          </React.Fragment>
                        ))}
                        <div className="flex items-center">
                          <div className="w-6 h-6 bg-slate-800 border border-pink-500/50 rounded flex items-center justify-center">
                            <span className="text-[9px] font-mono text-pink-300">M</span>
                          </div>
                          <div className="w-6 h-px bg-slate-600 border-b border-double border-slate-600 mt-0.5"></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
          <div className="flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-3">
            {!isCandidate && <Link to={`/predictions?model_id=${encodeURIComponent(model.id)}`} className="btn-primary inline-flex items-center gap-1.5 px-3 py-1.5 text-xs"><Activity className="h-3.5 w-3.5" /><span>Predict</span></Link>}
            <Link to={`/evaluation/${encodeURIComponent(model.training_run_id || '')}`} className="btn-secondary inline-flex items-center gap-1.5 px-3 py-1.5 text-xs"><BarChart3 className="h-3.5 w-3.5" /><span>Evaluation</span></Link>
            <button type="button" onClick={() => downloadMutation.mutate(model)} disabled={downloadMutation.isPending} className="btn-secondary inline-flex items-center gap-1.5 px-3 py-1.5 text-xs disabled:opacity-50"><Download className="h-3.5 w-3.5" /><span>{downloadMutation.isPending ? 'Downloading…' : 'Download'}</span></button>
            <button type="button" onClick={() => { if (window.confirm(`Remove ${model.name} from the model zoo? Its training and evaluation history will remain.`)) deleteMutation.mutate(model.id); }} disabled={deleteMutation.isPending} className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 disabled:opacity-50"><Trash2 className="h-3.5 w-3.5" /><span>Delete</span></button>
          </div>
        </article>;
      })}</div>}
    </section>
  </div>;
};
