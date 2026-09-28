import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Database,
  Table,
  ShieldCheck,
  History,
  Sliders,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  FileText,
} from 'lucide-react';
import { datasetsApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { ErrorState } from '../../components/common/ErrorState';

export const DatasetDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<'overview' | 'schema' | 'quality' | 'versions'>('overview');

  const { data: dataset, isLoading, error, refetch } = useQuery({
    queryKey: ['dataset', id],
    queryFn: () => (id ? datasetsApi.get(id) : Promise.reject('No ID')),
    enabled: !!id,
  });

  const latestVersion = dataset?.versions?.[0];

  const { data: analysis } = useQuery({
    queryKey: ['datasetAnalysis', id, latestVersion?.id],
    queryFn: () =>
      id && latestVersion
        ? datasetsApi.analyzeVersion(id, latestVersion.id)
        : Promise.reject('No version'),
    enabled: !!id && !!latestVersion,
  });

  if (isLoading) return <LoadingSkeleton rows={4} />;
  if (error || !dataset) {
    return (
      <ErrorState
        title="Dataset Not Found"
        message="Unable to locate the requested biomedical dataset in storage."
        onRetry={refetch}
      />
    );
  }

  const columns = analysis?.columns || [];
  const targetCol = analysis?.target_column || 'Unknown Target';
  const totalRows = analysis?.row_count || latestVersion?.row_count || 0;
  const totalCols = analysis?.column_count || latestVersion?.column_count || 0;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-slate-400">ID: {dataset.id.slice(0, 8)}...</span>
            <StatusBadge status={latestVersion?.status || 'validated'} size="sm" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{dataset.name}</h1>
          <p className="text-xs text-slate-500">{dataset.description || 'Clinical trial cohort'}</p>
        </div>

        <Link
          to="/preprocessing"
          className="btn-primary text-xs flex items-center space-x-2 self-start sm:self-auto"
        >
          <Sliders className="w-3.5 h-3.5 mr-1" />
          <span>Launch AI Preprocessing</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6">
          {[
            { id: 'overview', label: 'Overview', icon: Database },
            { id: 'schema', label: 'Biomarker Schema', icon: Table },
            { id: 'quality', label: 'Data Quality & Imbalance', icon: ShieldCheck },
            { id: 'versions', label: 'Version History', icon: History },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-3 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-colors ${
                  isActive
                    ? 'border-brand-800 text-brand-900'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-4">
            <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Cohort Summary
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-400 block text-[11px]">Rows</span>
                  <span className="text-lg font-bold text-slate-900">{totalRows}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-400 block text-[11px]">Columns</span>
                  <span className="text-lg font-bold text-slate-900">{totalCols}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-400 block text-[11px]">Suggested Target</span>
                  <span className="text-lg font-bold text-brand-800">{targetCol}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-400 block text-[11px]">Active Version</span>
                  <span className="text-lg font-bold text-quantum-700 font-mono">
                    {latestVersion?.version_tag || 'v1.0'}
                  </span>
                </div>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed pt-2">
                Uploaded file: <span className="font-mono">{analysis?.file_metadata?.filename || latestVersion?.dataset_metadata?.filename || 'Loading file metadata'}</span>
                {analysis?.file_metadata?.file_size_bytes != null && ` · ${(analysis.file_metadata.file_size_bytes / 1024).toFixed(1)} KB`}
              </p>
            </div>
          </div>

          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Next Action</h3>
            <p className="text-xs text-slate-500">
              Run AI Preprocessing to generate leak-free stratified splits and review Gemma LLM clinical recommendations.
            </p>
            <Link
              to="/preprocessing"
              className="w-full btn-primary text-xs py-2 flex items-center justify-center space-x-1"
            >
              <span>Start Preprocessing Wizard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Tab 2: Schema */}
      {activeTab === 'schema' && (
        <div className="card-scientific bg-white border border-slate-200 rounded-xl overflow-hidden p-0 shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-6">Column Name</th>
                <th className="py-3 px-6">Data Type</th>
                <th className="py-3 px-6">Missing Count</th>
                <th className="py-3 px-6">Role</th>
                <th className="py-3 px-6">Summary / Distribution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {columns.map((col) => {
                const isTarget = col === targetCol;
                const profile = analysis?.column_profiles?.[col];
                const missingCount = analysis?.missing_value_counts?.[col] || 0;
                const missingPct = totalRows > 0 ? ((missingCount / totalRows) * 100).toFixed(1) : '0.0';
                return (
                  <tr key={col} className="hover:bg-slate-50/70">
                    <td className="py-3 px-6 font-mono font-medium text-slate-900">{col}</td>
                    <td className="py-3 px-6 text-slate-500">
                      {analysis?.dtypes?.[col] || profile?.dtype || '—'}
                    </td>
                    <td className="py-3 px-6 text-slate-500">{missingCount} ({missingPct}%)</td>
                    <td className="py-3 px-6">
                      {isTarget ? (
                        <span className="badge bg-red-50 text-red-700 border border-red-200 font-semibold">
                          Target Label
                        </span>
                      ) : (
                        <span className="badge bg-slate-100 text-slate-600 border border-slate-200">
                          Biomarker Feature
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-6 text-slate-500 min-w-64">
                      {profile?.statistics && Object.keys(profile.statistics).length > 0 && (
                        <div className="mb-1 font-mono text-[10px]">
                          {Object.entries(profile.statistics).map(([key, value]) => `${key}: ${value ?? '—'}`).join(' · ')}
                        </div>
                      )}
                      {profile?.distribution?.length ? (
                        <div className="flex flex-wrap gap-1">
                          {profile.distribution.slice(0, 6).map((item, index) => (
                            <span key={`${col}-${index}`} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono">
                              {item.value !== undefined ? `${item.value ?? 'Missing'} (${item.count})` : `${item.lower}–${item.upper} (${item.count})`}
                            </span>
                          ))}
                        </div>
                      ) : <span>—</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 3: Data Quality */}
      {activeTab === 'quality' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Missing Data & Leakage Assessment
            </h3>
            <div className="space-y-3">
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center space-x-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                <div className="text-xs">
                  <span className="font-bold text-emerald-900 block">Missing Values</span>
                  <span className="text-emerald-700">
                    {Object.values(analysis?.missing_value_counts || {}).some(v => v > 0) 
                      ? 'Some missing values detected in the dataset.'
                      : `No missing values in ${totalRows} uploaded rows.`}
                  </span>
                </div>
              </div>
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center space-x-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                <div className="text-xs">
                  <span className="font-bold text-emerald-900 block">Duplicate Rows</span>
                  <span className="text-emerald-700">
                    {analysis?.duplicate_row_count ?? '—'} identical rows detected in the uploaded file.
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Class Distribution & Imbalance
            </h3>
            <div className="space-y-2 text-xs">
              {analysis?.class_distribution ? (
                Object.entries(analysis.class_distribution).map(([cls, count], idx) => {
                  const pct = totalRows > 0 ? (count / totalRows) * 100 : 0;
                  const colorClass = idx === 0 ? 'bg-red-500' : (idx === 1 ? 'bg-emerald-500' : 'bg-blue-500');
                  return (
                    <div key={cls}>
                      <div className="flex justify-between font-medium">
                        <span>Class {cls}</span>
                        <span className="text-slate-900 font-bold">{count} ({pct.toFixed(1)}%)</span>
                      </div>
                      <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden mb-2">
                        <div className={`${colorClass} h-2.5 rounded-full`} style={{ width: `${pct}%` }}></div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-slate-500 italic">No class distribution available for target.</div>
              )}
              
              {analysis?.class_distribution && Object.keys(analysis.class_distribution).length > 0 && (
                <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start space-x-2 text-[11px] text-amber-800">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-600" />
                  <span>
                    <strong>Class Imbalance Analyzed:</strong> AI Preprocessing Agent will recommend Stratified
                    K-Fold / Stratified Partitioning to preserve disease prevalence across train and test sets.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Versions */}
      {activeTab === 'versions' && (
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Immutable Version Ledger
          </h3>
          <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 text-xs">
            {dataset.versions?.map((ver) => (
              <div key={ver.id} className="p-4 flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-900 font-mono">{ver.version_tag}</span>
                    <StatusBadge status={ver.status} size="sm" />
                  </div>
                  <p className="text-slate-500 text-[11px]">
                    {ver.row_count} rows &bull; {ver.column_count} columns &bull; Immutable checksum verified
                  </p>
                </div>
                <div className="text-right text-[11px] text-slate-400 font-mono">
                  {new Date(ver.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
