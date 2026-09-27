import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Atom, Zap, Cpu, Server, CheckCircle2, Clock, Layers } from 'lucide-react';
import { quantumApi } from '../../api';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

export const QuantumDevicesPage: React.FC = () => {
  const { data: devices, isLoading } = useQuery({
    queryKey: ['quantumDevices'],
    queryFn: quantumApi.listDevices,
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="pb-4 border-b border-slate-200">
        <div className="flex items-center space-x-2 text-xs font-semibold text-quantum-700 uppercase tracking-wider mb-1">
          <Zap className="w-4 h-4 text-quantum-600" />
          <span>Quantum Execution Backends</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Quantum Computing Registry
        </h1>
        <p className="text-xs text-slate-500">
          Statevector analytic simulators, open-system noisy NISQ devices, and physical QPU integrations
        </p>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={3} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {devices?.map((d) => {
            const isSimulator = d.device_type === 'simulator';
            const isNoisy = d.device_type === 'noisy_simulator';
            const isHardware = d.device_type === 'hardware';

            return (
              <div
                key={d.device_id}
                className="card-scientific bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <StatusBadge status={d.status} size="sm" />
                    <span className="text-[11px] font-mono text-slate-400 font-medium">
                      {d.provider}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      {isSimulator && <Atom className="w-5 h-5 text-quantum-600" />}
                      {isNoisy && <Zap className="w-5 h-5 text-amber-600" />}
                      {isHardware && <Cpu className="w-5 h-5 text-indigo-600" />}
                      <h3 className="font-bold text-sm text-slate-900 font-mono">{d.device_id}</h3>
                    </div>
                    <span className="badge bg-slate-100 text-slate-700 capitalize text-[10px]">
                      {d.device_type.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-lg space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Addressable Qubits:</span>
                      <span className="font-bold text-slate-900 font-mono">{d.qubits} Qubits</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Supported Shots:</span>
                      <span className="font-mono text-slate-700 text-[11px]">
                        {d.shots_supported?.join(', ') || 'Analytic / Exact'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Queue Latency:</span>
                      <span className="font-semibold text-emerald-700">
                        {d.average_queue_time_seconds === 0 ? 'Immediate (< 10ms)' : `${d.average_queue_time_seconds}s`}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-400">
                  {isSimulator && 'Analytic statevector evaluation via PennyLane.'}
                  {isNoisy && 'Depolarizing Kraus channel + bitflip readout noise.'}
                  {isHardware && 'IBM Quantum / AWS Braket remote API connector.'}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
