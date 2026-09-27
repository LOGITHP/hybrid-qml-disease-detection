import React from 'react';
import { ShieldAlert } from 'lucide-react';

export const MedicalNotice: React.FC<{ compact?: boolean }> = ({ compact = false }) => {
  if (compact) {
    return (
      <div className="flex items-center text-xs text-slate-500 bg-slate-100/70 border border-slate-200 px-3 py-1.5 rounded-lg">
        <ShieldAlert className="w-3.5 h-3.5 text-slate-400 mr-2 flex-shrink-0" />
        <span>Research screening tool. Outputs do not constitute definitive clinical diagnoses.</span>
      </div>
    );
  }

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-start space-x-3 text-xs text-slate-600">
      <div className="p-1.5 bg-slate-200/60 rounded-md text-slate-600 mt-0.5">
        <ShieldAlert className="w-4 h-4 text-slate-600" />
      </div>
      <div>
        <h4 className="font-semibold text-slate-800 uppercase tracking-wider text-[11px] mb-1">
          Clinical Decision Support Notice
        </h4>
        <p className="leading-relaxed">
          The Hybrid Quantum Machine Learning Platform for Early Disease Detection is a research and computational screening instrument.
          All predicted classes, probability distributions, and risk stratifications (<span className="font-medium text-emerald-700">LOW</span>, <span className="font-medium text-amber-700">MEDIUM</span>, <span className="font-medium text-red-700">HIGH</span>) represent mathematical estimations and must be independently evaluated by licensed healthcare professionals alongside diagnostic imaging and clinical laboratory assays.
        </p>
      </div>
    </div>
  );
};
