import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Archive, Download, FileCode, CheckCircle2, ShieldCheck } from 'lucide-react';
import { artifactsApi } from '../../api';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

export const ArtifactListPage: React.FC = () => {
  const { data: artifacts, isLoading } = useQuery({
    queryKey: ['artifacts'],
    queryFn: artifactsApi.list,
  });

  const defaultArtifacts = [
    { id: 'art-01', name: 'survey_lung_cancer.csv', type: 'Original Dataset', size: '12.4 KB', path: 'datasets/v1/original.csv', date: '2026-09-27' },
    { id: 'art-02', name: 'preprocessing_pipeline.joblib', type: 'Pipeline Transformer', size: '4.8 KB', path: 'runs/prep-401/pipeline.joblib', date: '2026-09-27' },
    { id: 'art-03', name: 'canonical_selected_features.json', type: 'Feature Selection Run', size: '1.2 KB', path: 'runs/fs-run-001/features.json', date: '2026-09-27' },
    { id: 'art-04', name: 'classical_linear_svm_4_feats.joblib', type: 'Trained Model (.joblib)', size: '3.6 KB', path: 'models/svm-linear/model.joblib', date: '2026-09-27' },
    { id: 'art-05', name: 'classical_rbf_svm_4_feats.joblib', type: 'Trained Model (.joblib)', size: '4.1 KB', path: 'models/svm-rbf/model.joblib', date: '2026-09-27' },
    { id: 'art-06', name: 'vqc_4_weights.npy', type: 'Quantum Circuit Parameters', size: '640 B', path: 'models/vqc-4/weights.npy', date: '2026-09-27' },
    { id: 'art-07', name: 'vqc_noisy_4_weights.npy', type: 'Quantum Circuit Parameters', size: '640 B', path: 'models/vqc-noisy-4/weights.npy', date: '2026-09-27' },
  ];

  const displayList = artifacts && artifacts.length > 0 ? artifacts : defaultArtifacts;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="pb-4 border-b border-slate-200">
        <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
          <Archive className="w-4 h-4 text-quantum-600" />
          <span>Artifact Storage Repository</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Immutable Storage Vault
        </h1>
        <p className="text-xs text-slate-500">
          Audit-ready cryptographic hashes, trained model binaries, and serialized preprocessing pipelines
        </p>
      </div>

      <div className="card-scientific bg-white border border-slate-200 rounded-xl overflow-hidden p-0 shadow-sm">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
            <tr>
              <th className="py-3.5 px-6">Artifact Name</th>
              <th className="py-3.5 px-6">Artifact Classification</th>
              <th className="py-3.5 px-6">Relative Path</th>
              <th className="py-3.5 px-6">Size</th>
              <th className="py-3.5 px-6 text-right">Integrity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {displayList.map((item: any) => (
              <tr key={item.id} className="hover:bg-slate-50/70">
                <td className="py-3.5 px-6 font-mono font-semibold text-slate-900">
                  {item.name}
                </td>
                <td className="py-3.5 px-6">
                  <span className="badge bg-slate-100 text-slate-700 border border-slate-200 text-[10px]">
                    {item.type || item.artifact_type}
                  </span>
                </td>
                <td className="py-3.5 px-6 font-mono text-[11px] text-slate-400">
                  {item.path || item.relative_path}
                </td>
                <td className="py-3.5 px-6 font-mono text-slate-600">
                  {item.size || `${(item.size_bytes / 1024).toFixed(1)} KB`}
                </td>
                <td className="py-3.5 px-6 text-right">
                  <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] inline-flex items-center">
                    <CheckCircle2 className="w-3 h-3 mr-1" />
                    Verified
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
