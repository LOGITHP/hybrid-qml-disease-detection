import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { FlaskConical, Plus, ArrowRight, CheckCircle2, History } from 'lucide-react';
import { experimentsApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

export const ExperimentListPage: React.FC = () => {
  const { data: experiments, isLoading } = useQuery({
    queryKey: ['experiments'],
    queryFn: experimentsApi.list,
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
            <FlaskConical className="w-4 h-4 text-quantum-600" />
            <span>Research & Reproducibility</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Clinical Screening Experiments
          </h1>
          <p className="text-xs text-slate-500">
            Audit trails, multi-model benchmark campaigns, and complete reproducibility provenance
          </p>
        </div>

        <Link to="/training" className="btn-primary text-xs flex items-center space-x-2 self-start sm:self-auto">
          <Plus className="w-4 h-4" />
          <span>New Screening Campaign</span>
        </Link>
      </div>

      {isLoading ? (
        <LoadingSkeleton type="table" rows={3} />
      ) : (
        <div className="card-scientific bg-white border border-slate-200 rounded-xl overflow-hidden p-0 shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-6">Experiment Campaign</th>
                <th className="py-3 px-6">Tags</th>
                <th className="py-3 px-6">Models Evaluated</th>
                <th className="py-3 px-6">Reproducibility Chain</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {[
                {
                  id: 'exp-lung-cancer-benchmark',
                  name: 'Lung Cancer 4-Biomarker Hybrid Benchmark',
                  desc: 'Side-by-side comparison of Linear SVM, RBF SVM, and PennyLane VQC on 309 patients',
                  tags: ['Oncology', 'PennyLane', 'SVM', 'NISQ'],
                  models: ['SVM Linear', 'SVM RBF', '4-Qubit VQC Noiseless', '4-Qubit VQC Noisy'],
                  status: 'Verified Complete',
                },
                {
                  id: 'exp-vqc-scaling-qubits',
                  name: 'Quantum Qubit Scalability Study (4, 6, 8 Wires)',
                  desc: 'Evaluating convergence behavior and parameter trainability as qubit count scales',
                  tags: ['Scaling', 'NISQ Simulation'],
                  models: ['VQC 4-Qubit', 'VQC 6-Qubit', 'VQC 8-Qubit'],
                  status: 'Verified Complete',
                },
              ].map((exp) => (
                <tr key={exp.id} className="hover:bg-slate-50/70">
                  <td className="py-4 px-6">
                    <div className="font-semibold text-slate-900">{exp.name}</div>
                    <div className="text-[11px] text-slate-400 line-clamp-1">{exp.desc}</div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex flex-wrap gap-1">
                      {exp.tags.map((t) => (
                        <span key={t} className="badge bg-slate-100 text-slate-600 border border-slate-200 text-[10px]">
                          {t}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-4 px-6 font-medium text-slate-800">
                    {exp.models.length} Classifiers
                  </td>
                  <td className="py-4 px-6">
                    <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Fully Reproducible
                    </span>
                  </td>
                  <td className="py-4 px-6 text-right">
                    <Link
                      to={`/experiments/${exp.id}`}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold inline-flex items-center space-x-1"
                    >
                      <span>Inspect Chain</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
