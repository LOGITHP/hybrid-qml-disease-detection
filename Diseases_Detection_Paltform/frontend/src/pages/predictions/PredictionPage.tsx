import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Activity, ArrowRight, Database, Sliders, Star } from 'lucide-react';
import { predictionsApi } from '../../api';
import { MedicalNotice } from '../../components/common/MedicalNotice';

export const PredictionPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [threshold, setThreshold] = useState<number>(0.5);
  const [patientData, setPatientData] = useState<Record<string, any>>({});

  // 1. Fetch datasets that have completed training runs
  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['prediction-datasets'],
    queryFn: predictionsApi.getDatasets
  });

  // 2. Fetch trained models for the selected dataset
  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ['prediction-models', selectedDatasetId],
    queryFn: () => predictionsApi.getModels(selectedDatasetId),
    enabled: !!selectedDatasetId
  });

  // 3. Fetch model recommendation
  const { data: recommendation } = useQuery({
    queryKey: ['prediction-recommendation', selectedDatasetId],
    queryFn: () => predictionsApi.recommendModel(selectedDatasetId),
    enabled: !!selectedDatasetId && !!models && models.length > 0,
    retry: false
  });

  // 4. Fetch Schema for the selected model
  const { data: schema, isLoading: schemaLoading } = useQuery({
    queryKey: ['prediction-schema', selectedRunId],
    queryFn: () => predictionsApi.getSchema(selectedRunId),
    enabled: !!selectedRunId
  });

  // Sync recommendation to selection
  useEffect(() => {
    if (recommendation && !selectedRunId) {
      setSelectedRunId(recommendation.training_run_id);
    }
  }, [recommendation]);

  // Reset form when schema changes
  useEffect(() => {
    if (schema) {
      const initialData: Record<string, any> = {};
      schema.features.forEach((f: any) => {
        initialData[f.name] = null; // Wait for user input
      });
      setPatientData(initialData);
    }
  }, [schema]);

  const predictMutation = useMutation({
    mutationFn: async () => {
      if (!selectedRunId) throw new Error('Select a trained model first.');
      return predictionsApi.predict({
        training_run_id: selectedRunId,
        patient_data: patientData,
        threshold: threshold,
      });
    },
    onSuccess: (result) => {
      sessionStorage.setItem('latest_prediction', JSON.stringify(result));
      sessionStorage.setItem('latest_prediction_input', JSON.stringify(patientData));
      
      const activeModel = models?.find(m => m.training_run_id === selectedRunId);
      sessionStorage.setItem('latest_prediction_model_type', activeModel?.model_type || '');
      sessionStorage.setItem('latest_prediction_metrics', JSON.stringify(activeModel?.metrics || {}));
      
      navigate('/predictions/result');
    },
  });

  const handleInputChange = (featureName: string, value: any, type: string) => {
    let parsedValue = value;
    if (type === 'numerical') {
      parsedValue = value === '' ? null : parseFloat(value);
    }
    setPatientData(prev => ({ ...prev, [featureName]: parsedValue }));
  };

  const hasAllInputs = schema?.features.every((f: any) => patientData[f.name] !== null && patientData[f.name] !== '') ?? false;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <Activity className="w-4 h-4 text-quantum-600" />
            <span>Dataset-Aware Prediction</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Patient Prediction Form</h1>
          <p className="text-xs text-slate-500">Automatically adapting inference forms based on exact TrainingRun requirements.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-5">
          {/* STEP 1: SELECT DATASET */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">1. Select Dataset</label>
            {datasetsLoading ? <p className="text-xs">Loading datasets...</p> : (
              <select 
                value={selectedDatasetId} 
                onChange={(e) => {
                  setSelectedDatasetId(e.target.value);
                  setSelectedRunId('');
                  setPatientData({});
                }} 
                className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white font-semibold text-slate-900 text-sm"
              >
                <option value="">-- Choose a dataset --</option>
                {datasets?.map(d => (
                  <option key={d.dataset_id} value={d.dataset_id}>{d.name}</option>
                ))}
              </select>
            )}
            {!datasetsLoading && datasets?.length === 0 && (
              <p className="text-xs text-amber-700 mt-2">No trained models are available for any dataset. <Link to="/training" className="underline font-bold">Go to Training Session</Link></p>
            )}
          </div>

          {/* STEP 2: AVAILABLE MODELS & RECOMMENDATION */}
          {selectedDatasetId && (
            <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4 animate-in fade-in slide-in-from-bottom-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">2. Select Model Configuration</label>
              
              {recommendation && (
                <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Star className="w-4 h-4 text-emerald-600" />
                    <span className="font-bold text-emerald-800 text-sm">Recommended Model: {recommendation.model_type}</span>
                  </div>
                  <p className="text-[11px] text-emerald-700 mb-2">{recommendation.reason}</p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px]">
                    <div className="bg-white p-1.5 rounded border border-emerald-100">
                      <span className="block text-slate-400">Sensitivity</span>
                      <span className="font-mono font-bold">{(recommendation.metrics.sensitivity * 100).toFixed(1)}%</span>
                    </div>
                    <div className="bg-white p-1.5 rounded border border-emerald-100">
                      <span className="block text-slate-400">Specificity</span>
                      <span className="font-mono font-bold">{(recommendation.metrics.specificity * 100).toFixed(1)}%</span>
                    </div>
                    <div className="bg-white p-1.5 rounded border border-emerald-100">
                      <span className="block text-slate-400">ROC-AUC</span>
                      <span className="font-mono font-bold">{(recommendation.metrics.roc_auc).toFixed(2)}</span>
                    </div>
                    <div className="bg-white p-1.5 rounded border border-emerald-100">
                      <span className="block text-slate-400">Score</span>
                      <span className="font-mono font-bold text-emerald-600">{recommendation.recommendation_score}</span>
                    </div>
                  </div>
                  {selectedRunId !== recommendation.training_run_id && (
                    <button onClick={() => setSelectedRunId(recommendation.training_run_id)} className="mt-3 text-xs font-bold text-emerald-700 underline">
                      Use Recommended Model
                    </button>
                  )}
                </div>
              )}

              <select 
                value={selectedRunId} 
                onChange={(e) => setSelectedRunId(e.target.value)} 
                className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white font-normal text-sm"
              >
                <option value="">-- Choose a trained model --</option>
                {models?.map(m => (
                  <option key={m.training_run_id} value={m.training_run_id}>
                    {m.model_type} — Run {m.training_run_id.substring(0,8)} (Acc: {((m.metrics?.accuracy || 0) * 100).toFixed(1)}%)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* STEP 3: PATIENT INPUT FORM */}
          {selectedRunId && (
            <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4 animate-in fade-in slide-in-from-bottom-2">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">3. Patient Input</h3>
                  <p className="text-[11px] text-slate-400">Schema generated from exact PreprocessingArtifact.</p>
                </div>
                <span className="badge bg-brand-50 text-brand-800 border border-brand-200">{schema?.features.length || 0} features</span>
              </div>
              
              {schemaLoading ? <p className="text-xs">Generating input form...</p> : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  {schema?.features.map((feature: any) => (
                    <label key={feature.name} className="block font-semibold text-slate-700">
                      {feature.name}
                      <span className="block text-[9px] text-slate-400 font-normal mb-1">{feature.description}</span>
                      {feature.type === 'categorical' || feature.type === 'binary' ? (
                        <select 
                          value={patientData[feature.name] ?? ''} 
                          onChange={(e) => handleInputChange(feature.name, e.target.value, feature.type)} 
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white font-normal"
                        >
                          <option value="">Select {feature.name}</option>
                          {feature.categories?.map((cat: string) => (
                            <option key={cat} value={cat}>{cat}</option>
                          ))}
                        </select>
                      ) : (
                        <input 
                          type="number" 
                          step="any"
                          min={feature.min_value}
                          max={feature.max_value}
                          value={patientData[feature.name] ?? ''} 
                          onChange={(e) => handleInputChange(feature.name, e.target.value, feature.type)} 
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg font-normal" 
                          placeholder={`Range: ${feature.min_value} - ${feature.max_value}`}
                        />
                      )}
                    </label>
                  ))}
                </div>
              )}
              
              <div className="pt-4 border-t border-slate-100 space-y-2">
                <div className="flex items-center justify-between text-xs"><span className="font-semibold text-slate-700">Decision threshold</span><span className="font-mono font-bold text-slate-900">{(threshold * 100).toFixed(0)}%</span></div>
                <input type="range" min="0" max="1" step="0.01" value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} className="w-full accent-brand-800" />
                <p className="text-[11px] text-slate-500">Threshold changes only the positive/negative cutoff; it does not retrain the estimator.</p>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4 sticky top-6">
            <div className="flex items-center gap-2"><Sliders className="w-4 h-4 text-brand-800" /><h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Inference Action</h3></div>
            <p className="text-[11px] text-slate-500">
              The exact fitted preprocessing pipeline from the selected training run will be applied.
            </p>
            {predictMutation.isError && <p className="text-xs text-red-700">{predictMutation.error instanceof Error ? predictMutation.error.message : 'Prediction failed.'}</p>}
            
            <button 
              onClick={() => predictMutation.mutate()} 
              disabled={predictMutation.isPending || !selectedRunId || !hasAllInputs} 
              className="w-full btn-primary text-xs py-3 flex items-center justify-center space-x-2 shadow-md"
            >
              <Activity className="w-4 h-4" />
              <span>{predictMutation.isPending ? 'Computing prediction…' : 'Generate Inference'}</span>
            </button>
          </div>
          <MedicalNotice />
        </div>
      </div>
    </div>
  );
};
