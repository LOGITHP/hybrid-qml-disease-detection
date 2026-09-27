import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Download, ArrowRight, CheckCircle2, Printer } from 'lucide-react';

export const ReportListPage: React.FC = () => {
  const reports = [
    {
      id: 'rep-oncology-benchmark-2026',
      title: 'Clinical Lung Cancer Screening Benchmark Audit',
      type: 'Comparative Evaluation Report',
      date: 'September 2026',
      models: 'SVM Linear, SVM RBF, PennyLane VQC (4 Qubits)',
      status: 'Audited & Signed',
    },
    {
      id: 'rep-preprocessing-audit-01',
      title: 'AI Preprocessing & Data Leakage Compliance Ledger',
      type: 'Data Governance Audit',
      date: 'September 2026',
      models: 'Scikit-Learn Deterministic Pipeline & Gemma LLM',
      status: 'Verified Leak-Free',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="pb-4 border-b border-slate-200">
        <div className="flex items-center space-x-2 text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">
          <FileText className="w-4 h-4 text-quantum-600" />
          <span>Clinical Research Documentation</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Screening Audit Reports
        </h1>
        <p className="text-xs text-slate-500">
          Executive clinical summaries, benchmark tables, and regulatory reproducibility reports
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reports.map((rep) => (
          <div
            key={rep.id}
            className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between space-y-4"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="badge bg-slate-100 text-slate-700 text-[10px]">{rep.type}</span>
                <span className="text-[11px] font-mono text-slate-400">{rep.date}</span>
              </div>
              <h3 className="text-base font-bold text-slate-900">{rep.title}</h3>
              <p className="text-xs text-slate-500">Classifiers: {rep.models}</p>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-700 flex items-center">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                {rep.status}
              </span>
              <Link
                to={`/reports/${rep.id}`}
                className="btn-primary text-xs py-1.5 px-3 flex items-center space-x-1"
              >
                <span>View Full Report</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
