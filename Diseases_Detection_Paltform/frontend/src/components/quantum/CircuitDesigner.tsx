import React from 'react';
import { LucideIcon, GitMerge, Cpu, Search } from 'lucide-react';

interface QMLConfig {
  num_qubits: number;
  encoding: { type: string; gates: string[] };
  variational_layers: { layer: number; gates: string[] }[];
  entanglement: { type: string; gate: string };
  measurement: { type: string; qubits: number[] };
}

interface CircuitDesignerProps {
  config: QMLConfig;
  onChange: (config: QMLConfig) => void;
}

export const CircuitDesigner: React.FC<CircuitDesignerProps> = ({ config, onChange }) => {
  const { num_qubits, encoding, variational_layers, entanglement, measurement } = config;

  return (
    <div className="bg-slate-900 rounded-xl p-6 shadow-inner overflow-x-auto select-none border border-slate-700">
      <div className="flex items-center space-x-4 mb-6">
        <Cpu className="w-5 h-5 text-quantum-400" />
        <h4 className="text-quantum-50 text-sm font-semibold uppercase tracking-wider">Dynamic Quantum Circuit</h4>
      </div>

      <div className="inline-flex flex-col gap-3 min-w-max pb-4">
        {Array.from({ length: num_qubits }).map((_, qIdx) => (
          <div key={qIdx} className="flex items-center h-10 group">
            {/* Qubit Label */}
            <div className="w-16 flex items-center pr-2 font-mono text-xs text-slate-400 font-bold">
              |q_{qIdx}⟩
            </div>

            {/* Line / Wires container */}
            <div className="flex items-center space-x-2">
              
              {/* Encoding Layer */}
              <div className="flex items-center">
                <div className="w-4 h-px bg-slate-600"></div>
                <div className="w-12 h-10 bg-blue-900/50 border border-blue-500/50 rounded flex items-center justify-center shadow-[0_0_10px_rgba(59,130,246,0.2)]">
                  <span className="text-[10px] font-mono text-blue-200">{encoding.gates[0] || 'RY'}</span>
                </div>
                <div className="w-4 h-px bg-slate-600"></div>
              </div>

              {/* Variational Layers & Entanglement */}
              {variational_layers.map((layer, lIdx) => (
                <React.Fragment key={`v_${lIdx}_${qIdx}`}>
                  {/* Rotation Gate */}
                  <div className="flex items-center">
                    <div className="w-12 h-10 bg-purple-900/50 border border-purple-500/50 rounded flex items-center justify-center shadow-[0_0_10px_rgba(168,85,247,0.2)]">
                      <span className="text-[10px] font-mono text-purple-200">{layer.gates[0] || 'RY'}</span>
                    </div>
                    <div className="w-4 h-px bg-slate-600"></div>
                  </div>

                  {/* Entanglement (CNOT) visualization */}
                  {qIdx < num_qubits - 1 ? (
                    <div className="flex items-center relative w-8 h-10">
                      <div className="w-full h-px bg-slate-600 absolute top-1/2"></div>
                      <div className="w-2 h-2 rounded-full bg-quantum-400 absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 z-10"></div>
                      <div className="w-px h-10 bg-quantum-400/50 absolute left-1/2 translate-y-1/2"></div>
                    </div>
                  ) : (
                    <div className="flex items-center relative w-8 h-10">
                      <div className="w-full h-px bg-slate-600 absolute top-1/2"></div>
                      {/* Target CNOT */}
                      <div className="w-4 h-4 border-2 border-quantum-400 rounded-full absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 z-10 flex items-center justify-center bg-slate-900">
                        <div className="w-px h-full bg-quantum-400"></div>
                        <div className="h-px w-full bg-quantum-400 absolute"></div>
                      </div>
                      <div className="w-px h-1/2 bg-quantum-400/50 absolute left-1/2 -top-0"></div>
                    </div>
                  )}
                  <div className="w-4 h-px bg-slate-600"></div>
                </React.Fragment>
              ))}

              {/* Measurement */}
              <div className="flex items-center">
                <div className="w-10 h-10 bg-slate-800 border-2 border-pink-500/50 rounded flex items-center justify-center">
                  <span className="text-[10px] font-mono text-pink-300">M</span>
                </div>
                <div className="w-12 h-px bg-slate-600 border-b-2 border-double border-slate-600 mt-0.5"></div>
              </div>
              
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500 font-mono">
        <div>Architecture: {num_qubits} Qubits, {variational_layers.length} Layers</div>
        <div>PennyLane Statevector</div>
      </div>
    </div>
  );
};
