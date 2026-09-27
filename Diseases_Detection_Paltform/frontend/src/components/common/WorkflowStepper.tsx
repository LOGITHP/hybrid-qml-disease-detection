import React from 'react';
import { Check, ChevronRight } from 'lucide-react';

export interface StepItem {
  id: number;
  label: string;
  description?: string;
}

interface WorkflowStepperProps {
  steps: StepItem[];
  currentStep: number;
  onStepClick?: (stepId: number) => void;
}

export const WorkflowStepper: React.FC<WorkflowStepperProps> = ({
  steps,
  currentStep,
  onStepClick,
}) => {
  return (
    <div className="w-full bg-white border border-slate-200 rounded-xl p-4 shadow-sm overflow-x-auto">
      <nav aria-label="Progress">
        <ol className="flex items-center justify-between min-w-[700px]">
          {steps.map((step, index) => {
            const isCompleted = step.id < currentStep;
            const isCurrent = step.id === currentStep;
            const isUpcoming = step.id > currentStep;

            return (
              <li key={step.id} className="relative flex-1 flex items-center">
                <div
                  onClick={() => onStepClick && onStepClick(step.id)}
                  className={`group flex items-center space-x-3 ${
                    onStepClick ? 'cursor-pointer' : ''
                  }`}
                >
                  <span
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${
                      isCompleted
                        ? 'bg-emerald-600 text-white'
                        : isCurrent
                        ? 'bg-brand-800 text-white ring-4 ring-brand-100'
                        : 'bg-slate-100 text-slate-500 group-hover:bg-slate-200'
                    }`}
                  >
                    {isCompleted ? <Check className="w-4 h-4" /> : step.id}
                  </span>
                  <div className="flex flex-col">
                    <span
                      className={`text-xs font-semibold ${
                        isCurrent
                          ? 'text-brand-900'
                          : isCompleted
                          ? 'text-slate-800'
                          : 'text-slate-400'
                      }`}
                    >
                      {step.label}
                    </span>
                    {step.description && (
                      <span className="text-[10px] text-slate-400 hidden lg:inline">
                        {step.description}
                      </span>
                    )}
                  </div>
                </div>

                {index < steps.length - 1 && (
                  <div className="flex-1 mx-3 flex items-center">
                    <div
                      className={`h-0.5 w-full transition-colors ${
                        isCompleted ? 'bg-emerald-500' : 'bg-slate-200'
                      }`}
                    />
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    </div>
  );
};
