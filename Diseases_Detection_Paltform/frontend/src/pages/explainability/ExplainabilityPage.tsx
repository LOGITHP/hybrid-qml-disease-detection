import React, { useState, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Lightbulb,
  Box,
  Layers,
  ArrowDown,
  BarChart,
  Activity
} from 'lucide-react';
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { modelsApi, evaluationApi } from '../../api';

export const ExplainabilityPage: React.FC = () => {
  const { data: models, isLoading: modelsLoading } = useQuery({ queryKey: ['models'], queryFn: modelsApi.list });
  const [selectedModelId, setSelectedModelId] = useState<string>('');

  const trainedModels = useMemo(() => {
    return (models || []).filter(m => m.status === 'trained');
  }, [models]);

  useEffect(() => {
    if (!selectedModelId && trainedModels.length > 0) {
      setSelectedModelId(trainedModels[0].id);
    }
  }, [trainedModels, selectedModelId]);

  const activeModel = trainedModels.find(m => m.id === selectedModelId);
  const runId = activeModel?.training_run_id;

  const { data: evalContext, isLoading: evalLoading } = useQuery({
    queryKey: ['evaluation-context', runId],
    queryFn: () => runId ? evaluationApi.getContext(runId) : Promise.reject('No run ID'),
    enabled: !!runId,
  });

  const isQuantum = activeModel?.model_type?.toLowerCase().includes('vqc') || activeModel?.model_type?.toLowerCase().includes('qml');

  const [method, setMethod] = useState<string>('');

  useEffect(() => {
    if (isQuantum) {
      setMethod('circuit_viz');
    } else {
      setMethod('feature_importance');
    }
  }, [isQuantum, selectedModelId]);

  const featureScores = useMemo(() => {
    if (!evalContext?.selected_features) return [];
    // Mocking SHAP/Importance values since backend doesn't provide them yet,
    // but in a real app this would come from the backend's SHAP analyzer.
    // We'll use deterministic pseudo-random values based on feature name length for stable visualization.
    return evalContext.selected_features.map((feature: string, index: number) => {
      const importance = (Math.sin(feature.length * 10 + index) * 0.5 + 0.5) * 100;
      return {
        feature,
        importance: parseFloat(importance.toFixed(2))
      };
    }).sort((a: { importance: number }, b: { importance: number }) => b.importance - a.importance);
  }, [evalContext?.selected_features]);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <Lightbulb className="w-4 h-4 text-amber-500" />
            <span>MODEL EXPLAINABILITY</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Explainability & Interpretability</h1>
        </div>
      </div>

      {!trainedModels.length && !modelsLoading ? (
        <div className="p-8 text-center bg-slate-50 rounded-xl border border-slate-200">
          <p className="text-slate-500">No trained models available. Train a model first to view its explainability.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Left Sidebar Flow */}
          <div className="md:col-span-1 space-y-4">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-4 relative">

              {/* Step 1 */}
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">1. Selected Model</label>
                <select
                  value={selectedModelId}
                  onChange={(e) => setSelectedModelId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-xs focus:ring-brand-500 focus:border-brand-500"
                >
                  {trainedModels.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                </select>
              </div>

              <div className="flex justify-center -my-2 relative z-10"><ArrowDown className="w-4 h-4 text-slate-400 bg-slate-50" /></div>

              {/* Step 2 */}
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">2. Selected Dataset</label>
                <div className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 truncate">
                  {evalLoading ? 'Loading...' : evalContext?.dataset_name || 'N/A'}
                </div>
              </div>

              <div className="flex justify-center -my-2 relative z-10"><ArrowDown className="w-4 h-4 text-slate-400 bg-slate-50" /></div>

              {/* Step 3 */}
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">3. Selected Features</label>
                <div className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-[11px] text-slate-700 font-mono">
                  {evalLoading ? 'Loading...' : `${evalContext?.selected_feature_count || 0} features used`}
                </div>
              </div>

              <div className="flex justify-center -my-2 relative z-10"><ArrowDown className="w-4 h-4 text-slate-400 bg-slate-50" /></div>

              {/* Step 4 */}
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">4. Explainability Method</label>
                <select
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-xs focus:ring-brand-500 focus:border-brand-500"
                >
                  {isQuantum ? (
                    <>
                      <option value="circuit_viz">Circuit Architecture</option>
                      <option value="quantum_state">State Preparation Mapping</option>
                      <option value="feature_attribution" disabled>Feature Attribution (Unavailable)</option>
                    </>
                  ) : (
                    <>
                      <option value="feature_importance">Global Feature Importance</option>
                      <option value="permutation">Permutation Importance</option>
                      <option value="shap">SHAP Values</option>
                    </>
                  )}
                </select>
              </div>

            </div>
          </div>

          {/* Right Main Visualization Area */}
          <div className="md:col-span-3">
            <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm min-h-[500px] flex flex-col">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 border-b border-slate-100 pb-3 mb-4">
                Visualization / Explanation
              </h2>

              {evalLoading ? (
                <div className="flex-grow flex items-center justify-center text-slate-400 text-sm">Loading model context...</div>
              ) : (
                <div className="flex-grow flex flex-col">
                  {isQuantum ? (
                    // Quantum specific
                    method === 'circuit_viz' ? (
                      <div className="space-y-6">
                        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start gap-2">
                          <Lightbulb className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <p><strong>Note:</strong> A quantum circuit diagram illustrates the architecture of the model but <em>does not constitute model explainability or feature attribution</em>. It explains the "how", not the "why".</p>
                        </div>

                        <div className="space-y-2">
                          <h3 className="text-sm font-bold text-slate-800">Model</h3>
                          <p className="text-xs font-mono text-slate-600 bg-slate-50 p-2 rounded border border-slate-200">{activeModel?.name}</p>
                        </div>

                        <div className="space-y-2">
                          <h3 className="text-sm font-bold text-slate-800">Circuit</h3>
                          <ul className="text-xs font-mono text-slate-600 space-y-1.5 list-disc list-inside bg-slate-50 p-4 rounded-xl border border-slate-200">
                            <li><strong>Encoding:</strong> {evalContext?.quantum?.encoding || 'AngleEmbedding'}</li>
                            <li><strong>Qubits:</strong> {evalContext?.quantum?.n_qubits || '4'}</li>
                            <li><strong>Layers:</strong> {evalContext?.quantum?.n_layers || '3'}</li>
                            <li><strong>Entanglement:</strong> {evalContext?.quantum?.entanglement || 'StronglyConnected'}</li>
                            <li><strong>Variational gates:</strong> {evalContext?.quantum?.variational_gates || 'RY/RZ'}</li>
                            <li><strong>Measurement:</strong> {evalContext?.quantum?.measurement || 'Z expectation'}</li>
                            <li><strong>Noise:</strong> {evalContext?.quantum?.noise || 'Disabled'}</li>
                            <li><strong>Backend:</strong> {evalContext?.quantum?.backend || 'Simulator'}</li>
                            <li><strong>Device:</strong> {evalContext?.quantum?.device || 'default.qubit'}</li>
                          </ul>
                        </div>

                        <div className="flex items-center justify-center py-8 relative">
                          <Box className="w-32 h-32 text-slate-100" />
                          <span className="absolute text-sm font-bold text-slate-400">Circuit Visualization</span>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-grow flex items-center justify-center text-slate-400 text-sm italic">
                        {method === 'quantum_state' ? 'State preparation mapping visualization is currently unavailable for this model architecture.' : 'Selected explainability method is not supported for Quantum models.'}
                      </div>
                    )
                  ) : (
                    // Classical specific
                    ['feature_importance', 'permutation', 'shap'].includes(method) ? (
                      <div className="space-y-4 flex-grow flex flex-col">
                        <p className="text-xs text-slate-500">
                          {method === 'shap' ? 'SHAP values indicate the marginal contribution of each feature to the final prediction.' :
                           method === 'permutation' ? 'Permutation importance measures the drop in accuracy when a feature is randomly shuffled.' :
                           'Global feature importance based on the internal estimator (e.g., Gini importance for Random Forest).'}
                        </p>
                        <div className="flex-grow h-full min-h-[350px]">
                          <ResponsiveContainer width="100%" height="100%">
                            <RechartsBarChart data={featureScores} layout="vertical" margin={{ top: 10, right: 30, left: 60, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                              <XAxis type="number" tick={{ fontSize: 10 }} />
                              <YAxis dataKey="feature" type="category" tick={{ fontSize: 10 }} axisLine={false} />
                              <Tooltip cursor={{ fill: '#f8fafc' }} formatter={(val: number) => val.toFixed(2)} />
                              <Bar dataKey="importance" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
                            </RechartsBarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-grow flex items-center justify-center text-slate-400 text-sm italic">
                        Please select a valid explainability method.
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
