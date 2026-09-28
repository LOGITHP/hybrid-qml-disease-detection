import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Activity, ArrowRight, Database, Sliders } from 'lucide-react';
import { datasetsApi, modelsApi, predictionsApi } from '../../api';
import { MedicalNotice } from '../../components/common/MedicalNotice';
import { StatusBadge } from '../../components/common/StatusBadge';

export const PredictionPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: models } = useQuery({ queryKey: ['defaultModels'], queryFn: modelsApi.listDefaults });
  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: datasetsApi.list });
  const versionId = sessionStorage.getItem('activeDatasetVersionId');
  const dataset = datasets?.find((item) => item.versions?.some((version) => version.id === versionId));
  const version = dataset?.versions?.find((item) => item.id === versionId);
  const { data: analysis } = useQuery({
    queryKey: ['datasetAnalysis', dataset?.id, version?.id],
    queryFn: () => (dataset && version ? datasetsApi.analyzeVersion(dataset.id, version.id) : Promise.reject(new Error('No selected dataset version'))),
    enabled: !!dataset && !!version,
  });
  const [selectedModelId, setSelectedModelId] = useState('');
  const [threshold, setThreshold] = useState(0.5);
  const [inputFeatures, setInputFeatures] = useState<Record<string, string | number | boolean | null>>({});
  const selectedFeatures = (() => {
    try { return JSON.parse(sessionStorage.getItem('activeSelectedFeatures') || '[]') as string[]; }
    catch { return []; }
  })();
  const targetColumn = sessionStorage.getItem('activeTargetColumn');
  const suggestedModel = models?.find((model) => model.model_type === 'svm_linear' && model.status === 'trained')
    || models?.find((model) => model.status === 'trained');
  const activeModel = models?.find((model) => model.id === selectedModelId) || suggestedModel;

  useEffect(() => {
    setInputFeatures(Object.fromEntries(selectedFeatures.map((feature) => [feature, null])));
  }, [version?.id, selectedFeatures.join('|')]);

  const predictMutation = useMutation({
    mutationFn: async () => {
      if (!activeModel) throw new Error('Train a model on this dataset first.');
      return predictionsApi.predict({
        model_id: activeModel.id,
        features: inputFeatures,
        decision_threshold: threshold,
      });
    },
    onSuccess: (result) => {
      sessionStorage.setItem('latest_prediction', JSON.stringify(result));
      sessionStorage.setItem('latest_prediction_input', JSON.stringify(inputFeatures));
      sessionStorage.setItem('latest_prediction_model_name', activeModel?.name || 'Model');
      sessionStorage.setItem('latest_prediction_model_type', activeModel?.model_type || '');
      navigate('/predictions/result-latest');
    },
  });

  const hasAllInputs = selectedFeatures.length > 0 && selectedFeatures.every((feature) => inputFeatures[feature] !== null && inputFeatures[feature] !== '');

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1"><Activity className="w-4 h-4 text-quantum-600" /><span>Model Inference</span></div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Prediction on Selected Dataset Schema</h1>
          <p className="text-xs text-slate-500">Inference uses the selected model's saved preprocessing transformer and feature order.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-5">
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-700"><Database className="w-4 h-4" />Selected upload</div>
            <p className="text-xs text-slate-600">{analysis?.file_metadata?.filename || dataset?.name || 'Complete preprocessing and feature selection to choose a dataset.'} · {version?.version_tag || ''}</p>
            <p className="text-[11px] text-slate-500">Target: {targetColumn || '—'} · {selectedFeatures.length} feature columns</p>
          </div>

          {!version || !selectedFeatures.length ? (
            <div className="card-scientific bg-amber-50 border border-amber-200 rounded-xl p-5 space-y-2 text-xs text-amber-900">
              <p>Select and preprocess an uploaded dataset, then save its feature set before entering prediction values.</p>
              <div className="flex gap-4 font-semibold"><Link to="/preprocessing" className="underline">Preprocessing</Link><Link to="/features" className="underline">Feature selection</Link></div>
            </div>
          ) : (
            <>
              <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                <label className="block text-xs font-semibold text-slate-700">Trained model
                  <select value={activeModel?.id || ''} onChange={(event) => setSelectedModelId(event.target.value)} className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg bg-white font-normal">
                    {(models || []).filter((model) => model.status === 'trained').map((model) => <option key={model.id} value={model.id}>{model.name} ({model.model_type})</option>)}
                  </select>
                </label>
                {!activeModel && <p className="text-xs text-amber-800">No trained model is registered yet. Run training on this upload first.</p>}
              </div>

              <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div><h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Input feature values</h3><p className="text-[11px] text-slate-400">Fields follow the selected dataset's schema.</p></div>
                  <span className="badge bg-brand-50 text-brand-800 border border-brand-200">{selectedFeatures.length} selected</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  {selectedFeatures.map((feature) => {
                    const profile = analysis?.column_profiles?.[feature];
                    const categorical = analysis?.categorical_columns?.includes(feature);
                    const categories = (profile?.distribution || []).map((item) => item.value).filter((value): value is string | number | boolean => value !== null && value !== undefined);
                    return (
                      <label key={feature} className="block font-semibold text-slate-700">
                        {feature}
                        {categorical && categories.length > 0 ? (
                          <select value={String(inputFeatures[feature] ?? '')} onChange={(event) => {
                            const match = categories.find((value) => String(value) === event.target.value);
                            setInputFeatures((current) => ({ ...current, [feature]: match ?? null }));
                          }} className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg bg-white font-normal">
                            <option value="">Choose a value</option>
                            {categories.map((value) => <option key={String(value)} value={String(value)}>{String(value)}</option>)}
                          </select>
                        ) : categorical ? (
                          <input type="text" value={String(inputFeatures[feature] ?? '')} onChange={(event) => setInputFeatures((current) => ({ ...current, [feature]: event.target.value || null }))} className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg font-normal" />
                        ) : (
                          <input type="number" step="any" value={inputFeatures[feature] == null ? '' : String(inputFeatures[feature])} onChange={(event) => setInputFeatures((current) => ({ ...current, [feature]: event.target.value === '' ? null : Number(event.target.value) }))} className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg font-normal" />
                        )}
                      </label>
                    );
                  })}
                </div>
                <div className="pt-4 border-t border-slate-100 space-y-2">
                  <div className="flex items-center justify-between text-xs"><span className="font-semibold text-slate-700">Decision threshold</span><span className="font-mono font-bold text-slate-900">{(threshold * 100).toFixed(0)}%</span></div>
                  <input type="range" min="0" max="1" step="0.01" value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} className="w-full accent-brand-800" />
                  <p className="text-[11px] text-slate-500">Threshold changes only the positive/negative cutoff; it does not retrain the estimator.</p>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="space-y-4">
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-2"><Sliders className="w-4 h-4 text-brand-800" /><h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Inference</h3></div>
            <p className="text-xs text-slate-500">{activeModel ? `${activeModel.name} · ${activeModel.model_type}` : 'Train a model on this dataset to enable inference.'}</p>
            {predictMutation.isError && <p className="text-xs text-red-700">{predictMutation.error instanceof Error ? predictMutation.error.message : 'Prediction failed.'}</p>}
            <button onClick={() => predictMutation.mutate()} disabled={predictMutation.isPending || !activeModel || !hasAllInputs} className="w-full btn-primary text-xs py-3 flex items-center justify-center space-x-2 shadow-md">
              <Activity className="w-4 h-4" /><span>{predictMutation.isPending ? 'Computing prediction…' : 'Evaluate input values'}</span>
            </button>
            <Link to="/training" className="w-full text-xs text-center text-brand-800 font-semibold flex items-center justify-center gap-1">Training setup <ArrowRight className="w-3 h-3" /></Link>
          </div>
          <MedicalNotice />
        </div>
      </div>
    </div>
  );
};
