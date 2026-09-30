import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Database,
  UploadCloud,
  FileSpreadsheet,
  ArrowRight,
  Sparkles,
  Plus,
  CheckCircle2,
  AlertCircle,
  Trash,
} from 'lucide-react';
import { datasetsApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { EmptyState } from '../../components/common/EmptyState';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';


export const DatasetListPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [datasetName, setDatasetName] = useState('');
  const [datasetDesc, setDatasetDesc] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const { data: datasets, isLoading, error } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
  });

  const uploadMutation = useMutation({
    mutationFn: async (fileToUpload: File) => {
      setUploadStatus('Creating dataset container...');
      const created = await datasetsApi.create({
        name: datasetName || 'Uploaded dataset',
        description: datasetDesc || 'CSV dataset uploaded by the user.',
      });
      setUploadStatus('Uploading and parsing CSV...');
      await datasetsApi.uploadVersion(created.id, fileToUpload, 'v1.0');
      return created;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      setShowUploadModal(false);
      setSelectedFile(null);
      setDatasetName('');
      setDatasetDesc('');
      setUploadStatus(null);
    },
    onError: (err: any) => {
      setUploadStatus(`Error: ${err.message || 'Upload failed'}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await datasetsApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });



  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Uploaded Datasets</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Upload CSV files, inspect their actual schemas and quality, and manage dataset processing and features.
          </p>
        </div>
        <div className="flex items-center space-x-3">

          <button
            onClick={() => setShowUploadModal(true)}
            className="btn-primary text-xs flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Upload New Dataset</span>
          </button>
        </div>
      </div>

      {/* Datasets Table */}
      {isLoading ? (
        <LoadingSkeleton type="table" rows={4} />
      ) : !datasets || datasets.length === 0 ? (
        <EmptyState
          icon={Database}
          title="No Datasets Ingested Yet"
          description="Upload a CSV dataset to inspect its actual columns, data types, missing values, and distributions."
          actionText="Upload New Dataset"
          onAction={() => setShowUploadModal(true)}
        />
      ) : (
        <div className="card-scientific bg-white border border-slate-200 rounded-xl overflow-hidden p-0 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3.5 px-6">Dataset Name</th>
                  <th className="py-3.5 px-6">Status / Features</th>
                  <th className="py-3.5 px-6">Rows</th>
                  <th className="py-3.5 px-6">Columns</th>
                  <th className="py-3.5 px-6">Uploaded file</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {datasets.map((dataset) => {
                  const latestVersion = [...(dataset.versions || [])].sort((left, right) => Date.parse(right.created_at) - Date.parse(left.created_at))[0];
                  return <tr key={dataset.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-4 px-6">
                      <div className="font-semibold text-slate-900">{dataset.name}</div>
                      <div className="text-[11px] text-slate-400 line-clamp-1">{dataset.description || 'No description recorded.'}</div>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex flex-col space-y-1">
                        <div className="flex items-center space-x-2 text-[10px]">
                          <span className={`px-2 py-0.5 rounded-full ${latestVersion?.dataset_metadata?.processing_status?.preprocessed ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                            Preprocessed: {latestVersion?.dataset_metadata?.processing_status?.preprocessed ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-500 font-medium pl-1">
                          {latestVersion?.dataset_metadata?.selected_feature_count ? `${latestVersion.dataset_metadata.selected_feature_count} features` : (latestVersion?.column_count ? `${latestVersion.column_count} features (raw)` : '—')}
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6 font-semibold">
                      {latestVersion?.row_count ?? '—'}
                    </td>
                    <td className="py-4 px-6">
                      {latestVersion?.column_count ?? '—'}
                    </td>
                    <td className="py-4 px-6">
                      <span className="badge bg-slate-100 text-slate-700 border border-slate-200">
                        {latestVersion?.dataset_metadata?.filename || '—'}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Link
                          to={`/datasets/${dataset.id}`}
                          className="px-2.5 py-1 text-xs font-medium text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                        >
                          Inspect
                        </Link>
                        <Link
                          to="/preprocessing"
                          className="px-2.5 py-1 text-xs font-semibold text-brand-800 hover:text-brand-900 bg-brand-50 hover:bg-brand-100 rounded-lg transition-colors flex items-center space-x-1"
                        >
                          <span>Preprocess</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                        <button
                          onClick={() => {
                            if (window.confirm('Are you sure you want to delete this dataset? This action cannot be undone.')) {
                              deleteMutation.mutate(dataset.id);
                            }
                          }}
                          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors ml-1"
                          title="Delete dataset"
                          disabled={deleteMutation.isPending}
                        >
                          <Trash className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>;
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <FileSpreadsheet className="w-5 h-5 text-brand-800" />
                <h3 className="font-bold text-base text-slate-900">Upload CSV dataset</h3>
              </div>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Dataset Name</label>
                <input
                  type="text"
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  placeholder="e.g. Lung Cancer Patient Cohort"
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
                <input
                  type="text"
                  value={datasetDesc}
                  onChange={(e) => setDatasetDesc(e.target.value)}
                  placeholder="e.g. Clinical biomarker readings for oncology trial"
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
                />
              </div>

              {/* Drag and Drop Box */}
              <div className="relative border-2 border-dashed border-slate-300 hover:border-brand-500 rounded-xl p-6 text-center space-y-2 bg-slate-50/50 transition-colors">
                <UploadCloud className="w-8 h-8 text-slate-400 mx-auto" />
                <div className="text-xs text-slate-600">
                  <span className="font-semibold text-brand-800 hover:underline">
                    Browse local CSV file
                  </span>
                  {' '}or drag and drop here
                </div>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setSelectedFile(e.target.files[0]);
                    }
                  }}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                {selectedFile && (
                  <div className="mt-2 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 py-1.5 px-3 rounded-lg inline-flex items-center space-x-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                  </div>
                )}
              </div>

              {uploadStatus && (
                <div className="text-xs p-2.5 bg-slate-100 rounded-lg text-slate-700 font-mono">
                  {uploadStatus}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowUploadModal(false)}
                className="btn-secondary text-xs"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!selectedFile || uploadMutation.isPending}
                onClick={() => selectedFile && uploadMutation.mutate(selectedFile)}
                className="btn-primary text-xs"
              >
                {uploadMutation.isPending ? 'Validating & Ingesting...' : 'Upload & Validate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
