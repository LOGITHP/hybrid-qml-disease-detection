import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Activity, Database, Sliders } from 'lucide-react';
import { datasetsApi, modelsApi, predictionsApi } from '../../api';
import { Dataset, DatasetVersion } from '../../types';
import { MedicalNotice } from '../../components/common/MedicalNotice';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

const sameFeatureSet = (left: string[], right: string[]) =>
  left.length === right.length && left.every((feature, index) => feature === right[index]);

const latestVersion = (datasets: Dataset[]): { dataset: Dataset; version: DatasetVersion } | undefined => {
  const versions = datasets.flatMap((dataset) => (dataset.versions || []).map((version) => ({ dataset, version })));
  return versions.sort((a, b) => Date.parse(b.version.created_at) - Date.parse(a.version.created_at))[0];
};

export const PredictionPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedModelId, setSelectedModelId] = useState(() => new URLSearchParams(window.location.search).get('model_id') || '');
  const [threshold, setThreshold] = useState(0.5);
  const [inputFeatures, setInputFeatures] = useState<Record<string, string | number | null>>({});

  const { data: datasets, isLoading: datasetsLoading } = useQuery({ queryKey: ['datasets'], queryFn: datasetsApi.list });
  const { data: defaultModels, isLoading: defaultsLoading } = useQuery({ queryKey: ['defaultModels'], queryFn: modelsApi.listDefaults });
  const { data: userModels, isLoading: modelsLoading } = useQuery({ queryKey: ['userModels'], queryFn: modelsApi.list });
  const mergedModels = useMemo(() => [...(defaultModels || []), ...(userModels || [])], [defaultModels, userModels]);

  const storedVersionId = sessionStorage.getItem('activeDatasetVersionId');
  const activeUpload = useMemo(() => {
    const selected = datasets?.flatMap((dataset) => (dataset.versions || []).map((version) => ({ dataset, version })))
      .find(({ version }) => version.id === storedVersionId);
    return selected || (datasets ? latestVersion(datasets) : undefined);
  }, [datasets, storedVersionId]);

  const storedFeatures = (() => {
    try { return JSON.parse(sessionStorage.getItem('activeSelectedFeatures') || '[]') as string[]; }
    catch { return []; }
  })();
  const activeTarget = sessionStorage.getItem('activeTargetColumn') || '';
  const pipelineMatchesUpload = !!activeUpload && storedVersionId === activeUpload.version.id;
  const expectedFeatures = pipelineMatchesUpload ? storedFeatures : [];
  const expectedTarget = pipelineMatchesUpload ? activeTarget : '';

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['datasetAnalysis', activeUpload?.dataset.id, activeUpload?.version.id, expectedTarget],
    queryFn: () => activeUpload
      ? datasetsApi.analyzeVersion(activeUpload.dataset.id, activeUpload.version.id, expectedTarget || undefined)
      : Promise.reject(new Error('No uploaded dataset version is available.')),
    enabled: !!activeUpload,
  });

  const trainedModels = mergedModels.filter((model) => {
    const config = model.configuration || {};
    if (config.pretrained) return true;
    if (model.status !== 'trained' || !activeUpload || config.dataset_version_id !== activeUpload.version.id) return false;
    if (expectedTarget && config.target_column !== expectedTarget) return false;
    const featureNames = Array.isArray(config.selected_features) ? config.selected_features as string[] : [];
    return !expectedFeatures.length || sameFeatureSet(featureNames, expectedFeatures);
  }).sort((left, right) => {
    // Show user trained models first, then default models
    if (left.configuration?.pretrained && !right.configuration?.pretrained) return 1;
    if (!left.configuration?.pretrained && right.configuration?.pretrained) return -1;
    return Date.parse(right.created_at || '2000-01-01') - Date.parse(left.created_at || '2000-01-01');
  });
  const activeModel = trainedModels.find((model) => model.id === selectedModelId) || trainedModels[0];
  const features = (activeModel?.configuration?.selected_features || []) as string[];
  const targetColumn = String(activeModel?.configuration?.target_column || analysis?.target_column || expectedTarget || '');

  useEffect(() => {
    if (trainedModels.length && !trainedModels.some((model) => model.id === selectedModelId)) {
      setSelectedModelId(trainedModels[0].id);
    }
  }, [trainedModels, selectedModelId]);

  useEffect(() => {
    setInputFeatures((current) => {
      const next: Record<string, string | number | null> = {};
      features.forEach((feature) => { next[feature] = current[feature] ?? null; });
      return next;
    });
  }, [activeModel?.id, features.join('\u0000')]);

  const predictMutation = useMutation({
    mutationFn: async () => {
      if (!activeModel) throw new Error('Train a model on the active upload before generating predictions.');
      const values: Record<string, string | number | null> = {};
      features.forEach((feature) => {
        const value = inputFeatures[feature];
        values[feature] = value === '' || value === undefined ? null : value;
      });
      return predictionsApi.predict({ model_id: activeModel.id, features: values, decision_threshold: threshold });
    },
    onSuccess: (result) => {
      sessionStorage.setItem('latest_prediction', JSON.stringify(result));
      sessionStorage.setItem('latest_prediction_input', JSON.stringify(inputFeatures));
      sessionStorage.setItem('latest_prediction_model_name', activeModel?.name || 'Trained model');
      sessionStorage.setItem('latest_prediction_model_type', activeModel?.model_type || '');
      navigate('/predictions/latest');
    },
  });

  if (datasetsLoading || modelsLoading || defaultsLoading) return <LoadingSkeleton rows={4} />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-4 sm:flex-row sm:items-center">
        <div>
          <div className="mb-1 flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-brand-700"><Activity className="h-4 w-4 text-quantum-600" /><span>Dataset-aware prediction</span></div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Prediction input</h1>
          <p className="text-xs text-slate-500">Inputs follow the selected model’s saved features and preprocessing pipeline.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Active uploaded dataset</h2>
            {activeUpload ? <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Dataset</span><span className="font-semibold">{activeUpload.dataset.name}</span></div>
              <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Version</span><span className="font-mono font-semibold">{activeUpload.version.version_tag}</span></div>
              <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Rows · columns</span><span className="font-semibold">{activeUpload.version.row_count} · {activeUpload.version.column_count}</span></div>
              <div className="rounded-lg bg-slate-50 p-3"><span className="block text-slate-500">Target</span><span className="font-mono font-semibold">{targetColumn || '—'}</span></div>
            </div> : <p className="text-xs text-slate-600">Upload a CSV dataset and complete preprocessing, feature selection, and training first. <Link to="/datasets" className="font-semibold text-brand-800 underline">Open datasets</Link></p>}
          </section>

          <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <label className="block space-y-1 text-xs font-bold uppercase tracking-wider text-slate-700">
              Trained model
              <select value={activeModel?.id || ''} onChange={(event) => setSelectedModelId(event.target.value)} disabled={!trainedModels.length} className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-normal normal-case tracking-normal">
                {trainedModels.map((model) => <option key={model.id} value={model.id}>{model.name} · {model.model_type.toUpperCase()}</option>)}
              </select>
            </label>
            {!trainedModels.length && activeUpload && <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
              No trained model matches this upload and its current feature selection. Complete the pipeline for this version first.
              <div className="mt-2 flex gap-3 font-semibold"><Link to="/preprocessing" className="underline">Preprocessing</Link><Link to="/features" className="underline">Feature selection</Link><Link to="/training" className="underline">Training</Link></div>
            </div>}
            {activeModel && <p className="text-[11px] text-slate-500">Saved input columns: <span className="font-mono">{features.join(', ')}</span></p>}
          </section>

          {activeModel && <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div><h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Feature values</h2><p className="mt-1 text-[11px] text-slate-500">The saved preprocessing transformer is applied before inference. Leave unknown values blank if training included an imputer.</p></div>
              <span className="rounded border border-brand-200 bg-brand-50 px-2 py-1 text-[10px] font-semibold text-brand-800">{features.length} features</span>
            </div>
            {analysisLoading ? <p className="text-xs text-slate-500">Reading uploaded column types…</p> : <div className="grid grid-cols-1 gap-4 text-xs sm:grid-cols-2">
              {features.map((feature) => {
                const profile = analysis?.column_profiles?.[feature];
                const isNumeric = analysis?.numerical_columns?.includes(feature) ?? /^[-+]?\d+(\.\d+)?$/.test(String(profile?.sample_values?.[0] ?? ''));
                const choices = (profile?.distribution || []).flatMap((entry) => entry.value == null ? [] : [String(entry.value)]).filter((value, index, all) => all.indexOf(value) === index);
                const hasCompleteCategoryList = !!profile && profile.unique_count === choices.length;
                return <label key={feature} className="block space-y-1 font-semibold text-slate-700">
                  {feature}<span className="block text-[10px] font-normal text-slate-400">{profile?.dtype || 'Uploaded column'}</span>
                  {!isNumeric && choices.length > 0 && choices.length <= 20 && hasCompleteCategoryList ? <select value={String(inputFeatures[feature] ?? '')} onChange={(event) => setInputFeatures((current) => ({ ...current, [feature]: event.target.value || null }))} className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal">
                    <option value="">Missing / unknown</option>{choices.map((value) => <option key={value} value={value}>{value}</option>)}
                  </select> : <input type={isNumeric ? 'number' : 'text'} step={isNumeric ? 'any' : undefined} value={String(inputFeatures[feature] ?? '')} onChange={(event) => setInputFeatures((current) => ({ ...current, [feature]: event.target.value === '' ? null : isNumeric ? Number(event.target.value) : event.target.value }))} placeholder="Leave blank for missing" className="w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" />}
                </label>;
              })}
            </div>}
          </section>}
        </div>

        <aside className="space-y-4">
          <section className="card-scientific sticky top-6 space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-2"><Sliders className="h-4 w-4 text-brand-800" /><h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Inference settings</h2></div>
            <div className="flex items-center gap-2 text-[11px] text-slate-500"><Database className="h-3.5 w-3.5" /><span>{activeUpload?.dataset.name || 'No active upload'}</span></div>
            <label className="block space-y-2 text-xs"><span className="flex justify-between font-semibold text-slate-700"><span>Decision threshold</span><span>{(threshold * 100).toFixed(0)}%</span></span><input type="range" min="0" max="1" step="0.01" value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} className="w-full accent-brand-800" /><span className="block text-[11px] font-normal text-slate-500">Changes the classification cutoff only.</span></label>
            {predictMutation.isError && <p className="text-xs text-red-700">{predictMutation.error instanceof Error ? predictMutation.error.message : 'Prediction failed.'}</p>}
            <button type="button" onClick={() => predictMutation.mutate()} disabled={predictMutation.isPending || !activeModel || analysisLoading} className="btn-primary flex w-full items-center justify-center gap-2 py-3 text-xs shadow-md"><Activity className="h-4 w-4" /><span>{predictMutation.isPending ? 'Computing prediction…' : 'Generate prediction'}</span></button>
          </section>
          <MedicalNotice />
        </aside>
      </div>
    </div>
  );
};
