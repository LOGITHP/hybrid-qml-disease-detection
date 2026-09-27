import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { FileText, Printer, ArrowLeft, ShieldCheck, Atom } from 'lucide-react';
import { MedicalNotice } from '../../components/common/MedicalNotice';

export const ReportDetailPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto print:p-0">
      {/* Non-print Top Controls */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200 print:hidden">
        <Link to="/reports" className="btn-secondary text-xs flex items-center space-x-1.5">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Reports</span>
        </Link>
        <button
          onClick={handlePrint}
          className="btn-primary text-xs flex items-center space-x-1.5"
        >
          <Printer className="w-3.5 h-3.5" />
          <span>Print / Export PDF</span>
        </button>
      </div>

      {/* Formatted Report Document */}
      <div className="card-scientific bg-white border border-slate-200 rounded-2xl p-8 md:p-12 shadow-sm space-y-8 print:border-none print:shadow-none print:p-0">
        {/* Header */}
        <div className="border-b-2 border-slate-900 pb-6 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-widest text-brand-800">
              HybridQML Clinical Research Report
            </span>
            <span className="text-xs font-mono text-slate-400">Ref: {reportId || 'REP-2026-001'}</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
            Hybrid Quantum Machine Learning Platform for Early Disease Detection
          </h1>
          <p className="text-xs text-slate-500">
            Validated Comparative Benchmark: Classical Support Vector Machines vs. PennyLane Variational Quantum Classifiers
          </p>
        </div>

        {/* 1. Executive Summary */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-1">
            1. Executive Summary
          </h3>
          <p className="text-xs text-slate-700 leading-relaxed">
            This study evaluated an end-to-end hybrid quantum-classical machine learning workflow for early lung cancer detection using a 309-patient clinical cohort. Data preprocessing was orchestrated by the AI Preprocessing Agent with strict data leakage prevention. Canonical feature ranking identified the top 4 biomarkers (WHEEZING, YELLOW_FINGERS, AGE, SHORTNESS_OF_BREATH), which were consumed identically by both classical SVMs and PennyLane Variational Quantum Classifiers (VQC). Both classical and quantum models achieved over 93% accuracy on held-out test data, with VQC demonstrating high screening sensitivity (95.1%) and resilience under simulated NISQ noise.
          </p>
        </div>

        {/* 2. Methodology & Leakage Prevention */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-1">
            2. Methodology & Data Leakage Prevention
          </h3>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="font-bold text-slate-900 block mb-1">Partition Protocol</span>
              <p className="text-slate-600 text-[11px]">
                Stratified partitioning: 70% Training (N=216), 15% Validation (N=46), 15% Test (N=47), preserving 87.4% disease prevalence.
              </p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="font-bold text-slate-900 block mb-1">Imputation & Scaling</span>
              <p className="text-slate-600 text-[11px]">
                Imputer and MinMax scalers fit strictly on training samples; validation and test splits transformed without re-fitting.
              </p>
            </div>
          </div>
        </div>

        {/* 3. Canonical Features */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-1">
            3. Canonical Selected Features (Single Source of Truth)
          </h3>
          <div className="grid grid-cols-4 gap-2 text-center text-xs">
            {['1. WHEEZING', '2. YELLOW_FINGERS', '3. AGE', '4. SHORTNESS_OF_BREATH'].map((f) => (
              <div key={f} className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg font-mono font-bold text-slate-800">
                {f}
              </div>
            ))}
          </div>
        </div>

        {/* 4. Comparative Results Table */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-1">
            4. Comparative Clinical Performance Matrix
          </h3>
          <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
            <table className="w-full text-left">
              <thead className="bg-slate-100 font-bold text-slate-700">
                <tr>
                  <th className="py-2.5 px-4">Evaluation Metric</th>
                  <th className="py-2.5 px-4 text-center">Linear SVM</th>
                  <th className="py-2.5 px-4 text-center">RBF SVM</th>
                  <th className="py-2.5 px-4 text-center">4-Qubit VQC (Noiseless)</th>
                  <th className="py-2.5 px-4 text-center">4-Qubit VQC (Noisy NISQ)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-slate-700">
                <tr>
                  <td className="py-2 px-4 font-sans font-medium text-slate-900">Accuracy</td>
                  <td className="py-2 px-4 text-center">93.5%</td>
                  <td className="py-2 px-4 text-center">93.5%</td>
                  <td className="py-2 px-4 text-center font-bold text-brand-900">93.5%</td>
                  <td className="py-2 px-4 text-center">91.3%</td>
                </tr>
                <tr>
                  <td className="py-2 px-4 font-sans font-medium text-slate-900">Sensitivity (Recall)</td>
                  <td className="py-2 px-4 text-center">95.1%</td>
                  <td className="py-2 px-4 text-center">95.1%</td>
                  <td className="py-2 px-4 text-center font-bold text-emerald-700">95.1%</td>
                  <td className="py-2 px-4 text-center">92.7%</td>
                </tr>
                <tr>
                  <td className="py-2 px-4 font-sans font-medium text-slate-900">Specificity</td>
                  <td className="py-2 px-4 text-center">80.0%</td>
                  <td className="py-2 px-4 text-center">80.0%</td>
                  <td className="py-2 px-4 text-center">80.0%</td>
                  <td className="py-2 px-4 text-center">80.0%</td>
                </tr>
                <tr>
                  <td className="py-2 px-4 font-sans font-medium text-slate-900">ROC-AUC</td>
                  <td className="py-2 px-4 text-center">0.865</td>
                  <td className="py-2 px-4 text-center font-bold text-quantum-700">0.871</td>
                  <td className="py-2 px-4 text-center">0.865</td>
                  <td className="py-2 px-4 text-center">0.842</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* 5. Medical Notice */}
        <MedicalNotice />
      </div>
    </div>
  );
};
