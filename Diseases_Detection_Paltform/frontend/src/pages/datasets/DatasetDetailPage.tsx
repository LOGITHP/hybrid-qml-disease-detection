import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Database,
  Table,
  ShieldCheck,
  History,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  BarChart,
} from 'lucide-react';
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { DatasetVisualizations } from '../../components/datasets/DatasetVisualizations';
import { datasetsApi, preprocessingApi, featuresApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { ErrorState } from '../../components/common/ErrorState';

export const DatasetDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<'overview' | 'schema' | 'quality' | 'visualizations' | 'versions'>('overview');

  const { data: dataset, isLoading, error, refetch } = useQuery({
    queryKey: ['dataset', id],
    queryFn: () => (id ? datasetsApi.get(id) : Promise.reject('No ID')),
    enabled: !!id,
  });

  const activeVersionId = sessionStorage.getItem('activeDatasetVersionId');
  const latestVersion = dataset?.versions?.find((version) => version.id === activeVersionId)
    || [...(dataset?.versions || [])].sort((left, right) => Date.parse(right.created_at) - Date.parse(left.created_at))[0];

  const { data: analysis } = useQuery({
    queryKey: ['datasetAnalysis', id, latestVersion?.id],
    queryFn: () =>
      id && latestVersion
        ? datasetsApi.analyzeVersion(id, latestVersion.id)
        : Promise.reject('No version'),
    enabled: !!id && !!latestVersion,
  });

  const { data: preprocessingArtifacts } = useQuery({
    queryKey: ['preprocessingArtifacts', latestVersion?.id],
    queryFn: () => latestVersion ? preprocessingApi.listArtifacts(latestVersion.id) : Promise.reject('No version'),
    enabled: !!latestVersion,
  });

  const { data: featureSelectionRuns } = useQuery({
    queryKey: ['featureSelectionRuns', latestVersion?.id],
    queryFn: () => latestVersion ? featuresApi.listRuns(latestVersion.id) : Promise.reject('No version'),
    enabled: !!latestVersion,
  });

  const processingStatus = latestVersion?.dataset_metadata?.processing_status || {};
  const isPreprocessed = processingStatus.preprocessed || (preprocessingArtifacts && preprocessingArtifacts.length > 0);
  const isFeatureSelected = processingStatus.feature_selection || (featureSelectionRuns && featureSelectionRuns.length > 0);
  const latestFS = featureSelectionRuns?.[0];
  // all_features = every column available in the dataset (excl. target) — stored on FS run or version metadata
  const allFeatures: string[] = latestFS?.all_features || latestVersion?.dataset_metadata?.all_features || latestVersion?.dataset_metadata?.columns || [];
  // selected_features = the active subset the user picked
  const selectedFeatures: string[] = latestFS?.selected_features || latestVersion?.dataset_metadata?.selected_features || [];


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

  const columns = analysis?.columns || latestVersion?.dataset_metadata?.columns || [];
  const targetCol = analysis?.target_column || 'Not selected';
  const totalRows = analysis?.row_count ?? latestVersion?.row_count ?? '—';
  const totalCols = analysis?.column_count ?? latestVersion?.column_count ?? '—';
  const missingCounts = analysis?.missing_value_counts;
  const hasMissingValues = missingCounts ? Object.values(missingCounts).some((count) => count > 0) : undefined;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-slate-400">ID: {dataset.id.slice(0, 8)}...</span>
            <StatusBadge status={latestVersion?.status || 'No version'} size="sm" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{dataset.name}</h1>
          <p className="text-xs text-slate-500">{dataset.description || 'No description recorded.'}</p>
        </div>

      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6">
          {[
            { id: 'overview', label: 'Overview', icon: Database },
            { id: 'schema', label: 'Column Schema', icon: Table },
            { id: 'quality', label: 'Data Quality & Target', icon: ShieldCheck },
            { id: 'visualizations', label: 'Visualizations', icon: BarChart },
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
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3 md:col-span-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Dataset processing status</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs">
              {[['Uploaded', true], ['Preprocessed', !!isPreprocessed], ['Feature selection', !!isFeatureSelected]].map(([label, done]) => <div key={String(label)} className={`flex items-center gap-2 rounded-lg border p-3 ${done ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-slate-200 bg-slate-50 text-slate-500'}`}><CheckCircle2 className="h-4 w-4" /><span>{label}: <b>{done ? 'Done' : 'Not done'}</b></span></div>)}
            </div>
            {isFeatureSelected && (
              <div className="space-y-2">
                <p className="text-xs text-slate-600">
                  <b>All features in dataset:</b> {allFeatures.length || latestVersion?.dataset_metadata?.column_count || 0} columns
                  {' '}<span className="text-slate-400">·</span>{' '}
                  <b>Active selection:</b> {selectedFeatures.length} feature{selectedFeatures.length !== 1 ? 's' : ''}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {allFeatures.map((f) => (
                    <span key={f} className={`rounded px-2 py-0.5 font-mono text-[10px] border ${
                      selectedFeatures.includes(f)
                        ? 'bg-brand-50 border-brand-200 text-brand-800 font-bold'
                        : 'bg-slate-50 border-slate-200 text-slate-400'
                    }`}>{f}{selectedFeatures.includes(f) ? ' ✓' : ''}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="md:col-span-2 space-y-4">
            <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Uploaded Dataset Summary
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
                    {latestVersion?.version_tag || '—'}
                  </span>
                </div>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed pt-2">
                Uploaded file: <span className="font-mono">{analysis?.file_metadata?.filename || latestVersion?.dataset_metadata?.filename || '—'}</span>
                {analysis?.file_metadata?.file_size_bytes != null && ` · ${(analysis.file_metadata.file_size_bytes / 1024).toFixed(1)} KB`}
              </p>
            </div>


            {preprocessingArtifacts && preprocessingArtifacts.length > 0 && (
              <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Preprocessed Datasets
                </h3>
                <div className="space-y-3">
                  {preprocessingArtifacts.map((artifact: any) => (
                    <div key={artifact.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 border border-slate-200 rounded-lg bg-slate-50 text-xs">
                      <div className="space-y-1">
                        <div className="font-semibold text-slate-800">Preprocessed Run: {artifact.id.slice(0, 8)}</div>
                        <div className="text-[11px] text-slate-500">Rows: {artifact.final_row_count} | Columns: {artifact.final_column_count}</div>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono mt-2 sm:mt-0">
                        {new Date(artifact.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {featureSelectionRuns && featureSelectionRuns.length > 0 && (
              <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Feature Selection Runs
                </h3>
                <div className="space-y-3">
                  {featureSelectionRuns.map((run: any) => (
                    <div key={run.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 border border-slate-200 rounded-lg bg-slate-50 text-xs">
                      <div className="space-y-1">
                        <div className="font-semibold text-slate-800">Features Selected: {run.feature_count}</div>
                        <div className="text-[11px] text-slate-500 line-clamp-1">Method: {run.ranking_method} | Target: {run.target_column}</div>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono mt-2 sm:mt-0">
                        {new Date(run.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

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
                const missingCount = analysis?.missing_value_counts?.[col];
                const missingPct = typeof missingCount === 'number' && typeof totalRows === 'number' && totalRows > 0
                  ? `${((missingCount / totalRows) * 100).toFixed(1)}%`
                  : '—';
                return (
                  <tr key={col} className="hover:bg-slate-50/70">
                    <td className="py-3 px-6 font-mono font-medium text-slate-900">{col}</td>
                    <td className="py-3 px-6 text-slate-500">
                      {analysis?.dtypes?.[col] || latestVersion?.dataset_metadata?.dtypes?.[col] || profile?.dtype || '—'}
                    </td>
                    <td className="py-3 px-6 text-slate-500">{typeof missingCount === 'number' ? `${missingCount} (${missingPct})` : '—'}</td>
                    <td className="py-3 px-6">
                      {isTarget ? (
                        <span className="badge bg-red-50 text-red-700 border border-red-200 font-semibold">
                          Target Label
                        </span>
                      ) : (
                        <span className="badge bg-slate-100 text-slate-600 border border-slate-200">
                          Feature
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
              Data Quality Summary
            </h3>
            <div className="space-y-3">
              <div className={`p-3 rounded-lg flex items-center space-x-3 ${hasMissingValues === undefined ? 'bg-slate-50 border border-slate-200' : hasMissingValues ? 'bg-amber-50 border border-amber-200' : 'bg-emerald-50 border border-emerald-200'}`}>
                {hasMissingValues === undefined ? <AlertTriangle className="w-5 h-5 text-slate-500 flex-shrink-0" /> : hasMissingValues ? <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" /> : <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />}
                <div className="text-xs">
                  <span className="font-bold text-slate-900 block">Missing Values</span>
                  <span className="text-slate-700">
                    {hasMissingValues === undefined ? 'File quality analysis is not available yet.' : hasMissingValues ? `Missing values were found in ${Object.values(missingCounts || {}).filter((count) => count > 0).length} columns.` : `No missing values found in ${totalRows} uploaded rows.`}
                  </span>
                </div>
              </div>
              <div className={`p-3 rounded-lg flex items-center space-x-3 ${analysis ? 'bg-emerald-50 border border-emerald-200' : 'bg-slate-50 border border-slate-200'}`}>
                {analysis ? <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" /> : <AlertTriangle className="w-5 h-5 text-slate-500 flex-shrink-0" />}
                <div className="text-xs">
                  <span className="font-bold text-slate-900 block">Duplicate Rows</span>
                  <span className="text-slate-700">
                    {analysis ? `${analysis.duplicate_row_count} identical rows detected in the uploaded file.` : 'File quality analysis is not available yet.'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Target Distribution
            </h3>
            <div className="space-y-2 text-xs">
              {analysis?.class_distribution ? (
                Object.entries(analysis.class_distribution).map(([cls, count], idx) => {
                  const pct = typeof totalRows === 'number' && totalRows > 0 ? (count / totalRows) * 100 : 0;
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
                    <strong>Target class distribution recorded.</strong> Review the preprocessing split strategy before training so the evaluation partition reflects these class counts.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Visualizations */}
      {activeTab === 'visualizations' && (
        <DatasetVisualizations analysis={analysis as any} />
      )}

      {/* Tab 5: Versions */}
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
                    {ver.row_count} rows &bull; {ver.column_count} columns &bull; {ver.dataset_metadata?.filename || 'Uploaded file'}
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
