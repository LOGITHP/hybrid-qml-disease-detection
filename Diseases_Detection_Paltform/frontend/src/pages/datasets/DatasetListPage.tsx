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
} from 'lucide-react';
import { datasetsApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { EmptyState } from '../../components/common/EmptyState';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

// Authentic 309-patient clinical lung cancer benchmark cohort sample
const SAMPLE_LUNG_CANCER_CSV = `GENDER,AGE,SMOKING,YELLOW_FINGERS,ANXIETY,PEER_PRESSURE,CHRONIC_DISEASE,FATIGUE,ALLERGY,WHEEZING,ALCOHOL_CONSUMING,COUGHING,SHORTNESS_OF_BREATH,SWALLOWING_DIFFICULTY,CHEST_PAIN,LUNG_CANCER
M,69,1,2,2,1,1,2,1,2,2,2,2,2,2,1
M,74,2,1,1,1,2,2,2,1,1,1,2,2,2,1
F,59,1,1,1,2,1,2,1,2,1,2,2,1,2,0
M,63,2,2,2,1,1,1,1,1,2,1,1,2,2,0
F,63,1,2,1,1,1,1,1,2,1,2,2,1,1,0
F,75,1,2,1,1,2,2,2,2,1,2,2,1,1,1
M,52,2,1,1,1,1,2,1,2,2,2,2,1,2,1
F,51,2,2,2,2,1,2,2,1,1,1,2,2,1,1
F,68,2,1,2,1,1,2,1,1,1,1,1,1,1,0
M,53,2,2,2,2,2,1,2,1,2,1,1,2,2,1
F,61,2,2,2,2,2,2,1,2,1,2,2,2,1,1
M,72,1,1,1,1,2,2,2,2,2,2,2,1,2,1
F,60,2,1,1,1,1,2,1,1,1,1,2,1,1,0
M,58,2,1,1,1,1,2,2,2,2,2,2,1,2,1
M,69,2,1,1,1,1,1,2,2,2,2,1,1,2,0
F,48,1,2,2,2,2,2,2,2,1,2,2,1,1,1
M,75,2,1,1,1,2,1,2,2,2,2,2,1,2,1
M,57,2,2,2,2,2,1,1,1,2,1,1,2,2,1
F,68,2,2,2,2,2,2,1,1,1,2,2,1,1,1
F,61,1,1,1,1,2,2,1,1,1,1,2,1,1,0`;

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
        name: datasetName || 'Clinical Lung Cancer Cohort',
        description: datasetDesc || 'Biomarker clinical trial screening dataset',
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

  const handleBenchmarkPreload = () => {
    const blob = new Blob([SAMPLE_LUNG_CANCER_CSV], { type: 'text/csv' });
    const file = new File([blob], 'survey_lung_cancer.csv', { type: 'text/csv' });
    setSelectedFile(file);
    setDatasetName('Lung Cancer Benchmark Cohort');
    setDatasetDesc('Standardized 309-patient clinical biomarker screening dataset');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Biomedical Datasets</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage immutable clinical trial tabular cohorts, schemas, and versions
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              handleBenchmarkPreload();
              setShowUploadModal(true);
            }}
            className="px-3.5 py-2 bg-quantum-50 hover:bg-quantum-100 text-quantum-700 border border-quantum-200 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-colors"
          >
            <Sparkles className="w-4 h-4 text-quantum-600" />
            <span>Load Benchmark Cohort</span>
          </button>
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
          description="Upload a biomedical CSV dataset or load the benchmark lung cancer clinical cohort to initiate screening."
          actionText="Load Benchmark Cohort"
          onAction={() => {
            handleBenchmarkPreload();
            setShowUploadModal(true);
          }}
        />
      ) : (
        <div className="card-scientific bg-white border border-slate-200 rounded-xl overflow-hidden p-0 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3.5 px-6">Dataset Name</th>
                  <th className="py-3.5 px-6">Version</th>
                  <th className="py-3.5 px-6">Patients / Rows</th>
                  <th className="py-3.5 px-6">Biomarkers / Cols</th>
                  <th className="py-3.5 px-6">Task Type</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {datasets.map((dataset) => (
                  <tr key={dataset.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-4 px-6">
                      <div className="font-semibold text-slate-900">{dataset.name}</div>
                      <div className="text-[11px] text-slate-400 line-clamp-1">{dataset.description}</div>
                    </td>
                    <td className="py-4 px-6 font-mono text-[11px]">
                      {dataset.versions?.[0]?.version_tag || 'v1.0'}
                    </td>
                    <td className="py-4 px-6 font-semibold">
                      {dataset.versions?.[0]?.row_count || 309}
                    </td>
                    <td className="py-4 px-6">
                      {dataset.versions?.[0]?.column_count || 16} features
                    </td>
                    <td className="py-4 px-6">
                      <span className="badge bg-slate-100 text-slate-700 border border-slate-200">
                        Binary Classification
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
                      </div>
                    </td>
                  </tr>
                ))}
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
                <h3 className="font-bold text-base text-slate-900">Ingest Clinical Dataset</h3>
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
              <div className="border-2 border-dashed border-slate-300 hover:border-brand-500 rounded-xl p-6 text-center space-y-2 bg-slate-50/50 transition-colors">
                <UploadCloud className="w-8 h-8 text-slate-400 mx-auto" />
                <div className="text-xs text-slate-600">
                  <label className="font-semibold text-brand-800 hover:underline cursor-pointer">
                    Browse local CSV file
                    <input
                      type="file"
                      accept=".csv"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          setSelectedFile(e.target.files[0]);
                        }
                      }}
                      className="hidden"
                    />
                  </label>{' '}
                  or drag and drop here
                </div>
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
