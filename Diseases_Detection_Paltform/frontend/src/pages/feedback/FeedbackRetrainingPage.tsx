import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Activity, RotateCcw, CheckCircle, XCircle } from 'lucide-react';
import { modelsApi, feedbackApi } from '../../api';

export const FeedbackRetrainingPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedModelId, setSelectedModelId] = useState<string>('');

  const { data: defaultModels } = useQuery({ queryKey: ['defaultModels'], queryFn: modelsApi.listDefaults });
  const { data: userModels } = useQuery({ queryKey: ['userModels'], queryFn: modelsApi.list });
  
  const models = [...(defaultModels || []), ...(userModels || [])];

  useEffect(() => {
    if (models.length > 0 && !selectedModelId) {
      setSelectedModelId(models[0].id);
    }
  }, [models, selectedModelId]);

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['feedbackStats', selectedModelId],
    queryFn: () => feedbackApi.getStats(selectedModelId),
    enabled: !!selectedModelId
  });

  const { data: feedbackList, isLoading: listLoading, refetch: refetchList } = useQuery({
    queryKey: ['feedbackList', selectedModelId],
    queryFn: () => feedbackApi.listByModel(selectedModelId),
    enabled: !!selectedModelId
  });

  const retrainMutation = useMutation({
    mutationFn: () => feedbackApi.triggerRetrain(selectedModelId),
    onSuccess: () => {
      alert('Retraining job started successfully! Check Training page.');
      refetchStats();
      refetchList();
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
    onError: (err: any) => {
      alert(`Error triggering retrain: ${err.message}`);
    }
  });

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Model Feedback & Retraining</h1>
        <p className="text-sm text-slate-500">Review clinician feedback and continuously retrain models.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        <aside className="lg:col-span-1 space-y-4">
          <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Select Model</h2>
            <select 
              value={selectedModelId} 
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            >
              {models.map(m => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </section>

          <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Feedback Statistics</h2>
            {statsLoading ? <div className="text-sm">Loading...</div> : (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Total Feedback</span>
                  <span className="font-semibold text-slate-900">{stats?.total_feedback || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Correct</span>
                  <span className="font-semibold text-emerald-600">{stats?.correct_predictions || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Incorrect</span>
                  <span className="font-semibold text-red-600">{stats?.incorrect_predictions || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Pending Retrain</span>
                  <span className="font-semibold text-amber-600">{stats?.pending_retrain_count || 0}</span>
                </div>
                <hr className="border-slate-100" />
                <div className="flex justify-between font-bold">
                  <span className="text-slate-700">Clinician Accuracy</span>
                  <span className="text-brand-700">{((stats?.clinician_accuracy || 0) * 100).toFixed(1)}%</span>
                </div>
              </div>
            )}
            
            <button 
              onClick={() => retrainMutation.mutate()}
              disabled={retrainMutation.isPending || !stats?.pending_retrain_count}
              className="btn-primary w-full flex items-center justify-center gap-2 py-2 mt-4 text-xs font-semibold"
            >
              <RotateCcw className="w-4 h-4" />
              <span>{retrainMutation.isPending ? 'Starting...' : 'Retrain on Pending'}</span>
            </button>
          </section>
        </aside>

        <div className="lg:col-span-3 space-y-5">
          <section className="card-scientific rounded-xl border border-slate-200 bg-white p-6 shadow-sm overflow-hidden">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-4">Feedback Log</h2>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="bg-slate-50 text-[10px] uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Date</th>
                    <th className="px-4 py-3 font-semibold">Status</th>
                    <th className="px-4 py-3 font-semibold">Is Correct?</th>
                    <th className="px-4 py-3 font-semibold">Verified Label</th>
                    <th className="px-4 py-3 font-semibold">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {listLoading ? (
                    <tr><td colSpan={5} className="px-4 py-4 text-center text-slate-500">Loading...</td></tr>
                  ) : feedbackList?.length === 0 ? (
                    <tr><td colSpan={5} className="px-4 py-4 text-center text-slate-500">No feedback submitted for this model yet.</td></tr>
                  ) : (
                    feedbackList?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 text-slate-500">{new Date(item.created_at).toLocaleDateString()}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded-full text-[10px] font-semibold ${item.status === 'pending' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'}`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {item.is_correct ? (
                            <span className="flex items-center text-emerald-600 gap-1"><CheckCircle className="w-3 h-3" /> Yes</span>
                          ) : (
                            <span className="flex items-center text-red-600 gap-1"><XCircle className="w-3 h-3" /> No</span>
                          )}
                        </td>
                        <td className="px-4 py-3 font-mono">{item.verified_label}</td>
                        <td className="px-4 py-3 text-slate-600 truncate max-w-[200px]">{item.notes || '-'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
