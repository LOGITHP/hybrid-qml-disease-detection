import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Atom,
  Cpu,
  Layers,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sliders,
  Sparkles,
  Zap,
} from 'lucide-react';

export const VQCConfigPage: React.FC = () => {
  const navigate = useNavigate();

  const [qubits, setQubits] = useState<number>(4);
  const [layers, setLayers] = useState<number>(2);
  const [backendType, setBackendType] = useState<'default.qubit' | 'default.mixed'>('default.qubit');
  const [epochs, setEpochs] = useState<number>(100);
  const [learningRate, setLearningRate] = useState<number>(0.05);

  // Canonical feature count locked from feature selection
  const canonicalSelectedFeatures = 4;
  const isCompatible = qubits === canonicalSelectedFeatures;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-quantum-700 uppercase tracking-wider mb-1">
            <Atom className="w-4 h-4 text-quantum-600 animate-spin" />
            <span>PennyLane Variational Quantum Circuit</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            VQC Architecture & Circuit Configuration
          </h1>
          <p className="text-xs text-slate-500">
            Configure quantum gates, state preparation, and noise models aligned with experimental benchmarks
          </p>
        </div>

        <Link
          to="/training"
          className="btn-primary text-xs flex items-center space-x-2 self-start sm:self-auto"
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>Launch Training with VQC</span>
        </Link>
      </div>

      {/* Compatibility Banner */}
      <div
        className={`p-4 rounded-xl border flex items-start space-x-3 text-xs ${
          isCompatible
            ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
            : 'bg-amber-50 border-amber-200 text-amber-900'
        }`}
      >
        {isCompatible ? (
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        )}
        <div className="space-y-1">
          <div className="flex items-center space-x-3 font-bold text-xs">
            <span>Canonical Selected Features: {canonicalSelectedFeatures}</span>
            <span>&bull;</span>
            <span>Configured Qubits: {qubits}</span>
            <span>&bull;</span>
            <span>Status: {isCompatible ? 'COMPATIBLE' : 'INCOMPATIBLE'}</span>
          </div>
          <p className="text-[11px] leading-relaxed">
            {isCompatible
              ? 'Circuit configuration perfectly maps each canonical biomarker feature to an AngleEmbedding qubit wire.'
              : `Warning: Feature selection locked ${canonicalSelectedFeatures} biomarkers, but circuit is configured for ${qubits} qubits. Each feature requires an assigned qubit in AngleEmbedding.`}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left 2 Cols: Circuit Design Form */}
        <div className="md:col-span-2 space-y-6">
          {/* Circuit Topology */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              1. Quantum Circuit Topology
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">State Preparation</label>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="font-bold text-slate-900 block font-mono">AngleEmbedding</span>
                  <span className="text-[11px] text-slate-500">
                    Encodes normalized biomarker values into qubit rotation angles: $RY(x_i \cdot \pi)$
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Entangling Ansatz</label>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="font-bold text-slate-900 block font-mono">Linear CNOT Layers</span>
                  <span className="text-[11px] text-slate-500">
                    Two-qubit CNOT gates between adjacent wires with parameterised $RY(\theta)$ rotations
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-2">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Qubit Count (Wires)
                </label>
                <select
                  value={qubits}
                  onChange={(e) => setQubits(parseInt(e.target.value, 10))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white font-medium"
                >
                  <option value={2}>2 Qubits (Fast)</option>
                  <option value={4}>4 Qubits (Canonical Baseline &bull; Recommended)</option>
                  <option value={6}>6 Qubits</option>
                  <option value={8}>8 Qubits</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Variational Repetitions ($L$)
                </label>
                <select
                  value={layers}
                  onChange={(e) => setLayers(parseInt(e.target.value, 10))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white font-medium"
                >
                  <option value={1}>1 Layer (Shallow)</option>
                  <option value={2}>2 Layers (Optimal Depth &bull; Validated)</option>
                  <option value={3}>3 Layers</option>
                </select>
              </div>
            </div>
          </div>

          {/* Quantum Backend & Noise Model */}
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              2. Quantum Execution Backend & NISQ Simulation
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div
                onClick={() => setBackendType('default.qubit')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  backendType === 'default.qubit'
                    ? 'border-quantum-600 bg-quantum-50/50 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1.5">
                  <Atom className="w-4 h-4 text-quantum-600" />
                  <span className="text-xs font-bold text-slate-900">Noiseless Statevector</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  PennyLane <code className="font-mono text-quantum-800">default.qubit</code> device. Exact quantum state evolution without decoherence.
                </p>
              </div>

              <div
                onClick={() => setBackendType('default.mixed')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  backendType === 'default.mixed'
                    ? 'border-quantum-600 bg-quantum-50/50 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1.5">
                  <Zap className="w-4 h-4 text-amber-600" />
                  <span className="text-xs font-bold text-slate-900">Noisy NISQ Open System</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  PennyLane <code className="font-mono text-amber-800">default.mixed</code> with depolarizing noise ($p=0.5\%$) and bit-flip readout error ($p=1.5\%$).
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Circuit Visualization & Summary */}
        <div className="space-y-4">
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              VQC Layer Blueprint
            </h3>
            <div className="p-3 bg-slate-900 text-slate-100 rounded-xl font-mono text-[11px] space-y-1.5 overflow-x-auto">
              <div className="text-quantum-400 font-bold">// PennyLane Circuit Graph</div>
              <div>|0⟩ ─ RY(x₀·π) ─ [Rot] ─●─── ... ─ ⟨Z₀⟩</div>
              <div>|0⟩ ─ RY(x₁·π) ─ [Rot] ─X─●─ ... ─ ⟨Z₁⟩</div>
              <div>|0⟩ ─ RY(x₂·π) ─ [Rot] ───X─ ... ─ ⟨Z₂⟩</div>
              <div>|0⟩ ─ RY(x₃·π) ─ [Rot] ───── ... ─ ⟨Z₃⟩</div>
              <div className="pt-2 text-slate-400 text-[10px]">
                Pooling: z = (1/N) ∑ ⟨Z_i⟩ + b
              </div>
              <div className="text-emerald-400 text-[10px]">
                Output: P(Cancer) = σ(z)
              </div>
            </div>
          </div>

          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Ready for Training
            </h3>
            <p className="text-xs text-slate-500">
              Launch model training with this PennyLane circuit configuration.
            </p>
            <Link
              to="/training"
              className="w-full btn-primary text-xs py-2 flex items-center justify-center space-x-1"
            >
              <span>Train Model</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
