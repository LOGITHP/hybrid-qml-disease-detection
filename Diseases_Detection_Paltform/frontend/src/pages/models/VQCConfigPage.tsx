import React, { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Atom, ArrowRight, CircleSlash2, Layers, Save, Zap, Settings2, Server } from 'lucide-react';
import { CircuitDesigner } from '../../components/quantum/CircuitDesigner';

type CircuitConfig = {
  n_qubits: number;
  n_layers: number;
  epochs: number;
  encoding_method: 'angle_ry' | 'angle_rx';
  variational_gate: 'RY' | 'RZ';
  entanglement_strategy: 'linear_cnot' | 'ring_cnot' | 'none';
  backend_type: 'default.qubit' | 'default.mixed' | 'hardware';
  noise_params: { p_gate: number; p_cnot: number; p_meas: number };
};

const PRESETS: Record<string, Partial<CircuitConfig>> = {
  hardware_efficient: {
    n_layers: 2,
    encoding_method: 'angle_ry',
    variational_gate: 'RY',
    entanglement_strategy: 'linear_cnot',
  },
  deep_entangled: {
    n_layers: 4,
    encoding_method: 'angle_rx',
    variational_gate: 'RZ',
    entanglement_strategy: 'ring_cnot',
  },
  shallow_independent: {
    n_layers: 1,
    encoding_method: 'angle_ry',
    variational_gate: 'RY',
    entanglement_strategy: 'none',
  }
};

const readFeatures = (): string[] => {
  try { return JSON.parse(sessionStorage.getItem('activeSelectedFeatures') || '[]') as string[]; }
  catch { return []; }
};

export const VQCConfigPage: React.FC = () => {
  const navigate = useNavigate();
  const features = readFeatures();
  const initial = (() => {
    try { return JSON.parse(sessionStorage.getItem('vqc_circuit_config') || '{}') as Partial<CircuitConfig>; }
    catch { return {}; }
  })();
  const [config, setConfig] = useState<CircuitConfig>({
    n_qubits: Number(initial.n_qubits || Math.max(1, features.length || 4)),
    n_layers: initial.n_layers || 2,
    epochs: initial.epochs || 50,
    encoding_method: initial.encoding_method || 'angle_ry',
    variational_gate: initial.variational_gate || 'RY',
    entanglement_strategy: initial.entanglement_strategy || 'linear_cnot',
    backend_type: initial.backend_type || 'default.qubit',
    noise_params: initial.noise_params || { p_gate: 0.01, p_cnot: 0.02, p_meas: 0.01 },
  });
  const [saved, setSaved] = useState(false);
  const mapping = useMemo(() => features.map((feature, index) => ({ feature, qubit: index })), [features]);
  const isCompatible = features.length > 0 && config.n_qubits === features.length && config.n_qubits <= 8;

  const update = <K extends keyof CircuitConfig>(key: K, value: CircuitConfig[K]) => {
    setSaved(false);
    setConfig((current) => ({ ...current, [key]: value }));
  };

  const applyPreset = (presetKey: string) => {
    if (!PRESETS[presetKey]) return;
    setSaved(false);
    setConfig((current) => ({ ...current, ...PRESETS[presetKey] }));
  };

  const save = () => {
    sessionStorage.setItem('vqc_circuit_config', JSON.stringify(config));
    setSaved(true);
  };

  // Map to QMLConfig for CircuitDesigner
  const qmlConfig = useMemo(() => ({
    num_qubits: config.n_qubits,
    encoding: {
      type: 'angle',
      gates: Array(config.n_qubits).fill(config.encoding_method === 'angle_ry' ? 'RY' : 'RX')
    },
    variational_layers: Array.from({ length: config.n_layers }).map((_, i) => ({
      layer: i,
      gates: Array(config.n_qubits).fill(config.variational_gate)
    })),
    entanglement: {
      type: config.entanglement_strategy === 'none' ? 'none' : 'cnot',
      gate: config.entanglement_strategy === 'none' ? '' : 'CNOT'
    },
    measurement: {
      type: 'expectation',
      qubits: Array.from({ length: config.n_qubits }).map((_, i) => i)
    }
  }), [config]);

  return <div className="space-y-6">
    <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-4 sm:flex-row sm:items-center">
      <div>
        <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-quantum-700"><Atom className="h-4 w-4" /><span>PennyLane simulator circuit designer</span></div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Configure the VQC circuit</h1>
        <p className="text-xs text-slate-500">Design your quantum layers, select a preset, and map features to qubits.</p>
      </div>
      <div className="flex gap-3">
        <select onChange={(e) => applyPreset(e.target.value)} className="btn-secondary px-3 py-1.5 text-xs bg-slate-50 cursor-pointer">
          <option value="">Select Preset Design...</option>
          <option value="hardware_efficient">Hardware Efficient (2 Layers, RY, Linear CNOT)</option>
          <option value="deep_entangled">Deeply Entangled (4 Layers, RZ, Ring CNOT)</option>
          <option value="shallow_independent">Shallow Independent (1 Layer, RY, No CNOT)</option>
        </select>
        <Link to="/training" className="btn-secondary inline-flex items-center gap-2 text-xs"><span>Back to training</span><ArrowRight className="h-3.5 w-3.5" /></Link>
      </div>
    </header>

    <div className={`rounded-xl border p-4 text-xs ${isCompatible ? 'border-emerald-200 bg-emerald-50 text-emerald-900' : 'border-amber-200 bg-amber-50 text-amber-900'}`}>
      {features.length ? <><b>{features.length} selected source features.</b> This circuit uses one qubit per transformed feature, so set the qubit count to the transformed feature width. Encoders may expand categorical columns.</> : <>Select a dataset and feature set in the training workflow before finalizing feature-to-qubit mapping.</>}
      {features.length > 0 && <span className="ml-1">Current mapping check: {isCompatible ? 'compatible' : `configured for ${config.n_qubits} qubits; check selected features and encoding output`}.</span>}
    </div>

    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="space-y-5 lg:col-span-2">

        {/* Dynamic Visual Circuit Designer */}
        <CircuitDesigner config={qmlConfig} onChange={() => {}} />

        <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2"><Settings2 className="w-4 h-4"/> Layer & Gate Configuration</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <label className="space-y-1 text-xs font-semibold text-slate-700">Qubit count
              <input type="number" min={1} max={8} value={config.n_qubits} onChange={(event) => update('n_qubits', Number(event.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal" />
            </label>
            <label className="space-y-1 text-xs font-semibold text-slate-700">Variational Layers
              <input type="number" min={1} max={10} value={config.n_layers} onChange={(event) => update('n_layers', Number(event.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal" />
            </label>
            <label className="space-y-1 text-xs font-semibold text-slate-700">Training Epochs
              <input type="number" min={1} max={1000} value={config.epochs} onChange={(event) => update('epochs', Number(event.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal" />
            </label>
            <label className="space-y-1 text-xs font-semibold text-slate-700">Encoding method
              <select value={config.encoding_method} onChange={(event) => update('encoding_method', event.target.value as CircuitConfig['encoding_method'])} className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-normal">
                <option value="angle_ry">Angle encoding · RY(xπ)</option><option value="angle_rx">Angle encoding · RX(xπ)</option>
              </select>
            </label>
            <label className="space-y-1 text-xs font-semibold text-slate-700">Trainable rotation gate
              <select value={config.variational_gate} onChange={(event) => update('variational_gate', event.target.value as CircuitConfig['variational_gate'])} className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-normal"><option value="RY">RY</option><option value="RZ">RZ</option></select>
            </label>
            <label className="space-y-1 text-xs font-semibold text-slate-700">Entanglement strategy
              <select value={config.entanglement_strategy} onChange={(event) => update('entanglement_strategy', event.target.value as CircuitConfig['entanglement_strategy'])} className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-normal"><option value="linear_cnot">Linear CNOT chain</option><option value="ring_cnot">Ring CNOT</option><option value="none">No entanglement</option></select>
            </label>
          </div>
          <p className="text-[11px] text-slate-500">Measurement is fixed to per-qubit Pauli-Z expectation pooled by mean. Readout shots are analytic in PennyLane simulators.</p>
        </section>

        <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Execution backend</h2>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <button type="button" onClick={() => update('backend_type', 'default.qubit')} className={`rounded-xl border p-4 text-left ${config.backend_type === 'default.qubit' ? 'border-quantum-500 bg-quantum-50' : 'border-slate-200'}`}><span className="flex items-center gap-2 text-sm font-semibold"><Atom className="h-4 w-4 text-quantum-700" />Noiseless simulation</span><span className="mt-2 block text-[11px] text-slate-600">PennyLane default.qubit · idealized execution without noise channels.</span></button>
            <button type="button" onClick={() => update('backend_type', 'default.mixed')} className={`rounded-xl border p-4 text-left ${config.backend_type === 'default.mixed' ? 'border-amber-400 bg-amber-50' : 'border-slate-200'}`}><span className="flex items-center gap-2 text-sm font-semibold"><Zap className="h-4 w-4 text-amber-600" />Noisy simulation</span><span className="mt-2 block text-[11px] text-slate-600">PennyLane default.mixed · configured depolarizing and readout channels.</span></button>
            <button type="button" onClick={() => update('backend_type', 'hardware')} className={`rounded-xl border p-4 text-left ${config.backend_type === 'hardware' ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200'}`}><span className="flex items-center gap-2 text-sm font-semibold"><Server className="h-4 w-4 text-indigo-600" />Real hardware</span><span className="mt-2 block text-[11px] text-slate-600">Execute on real quantum hardware (e.g. IBM, Rigetti, IonQ).</span></button>
          </div>
          {config.backend_type === 'default.mixed' && <div className="grid grid-cols-3 gap-3 text-xs">{(['p_gate', 'p_cnot', 'p_meas'] as const).map((key) => <label key={key} className="space-y-1 text-slate-700">{key.replace('p_', 'P(')}<input type="number" min={0} max={0.5} step={0.005} value={config.noise_params[key]} onChange={(event) => { setSaved(false); setConfig((current) => ({ ...current, noise_params: { ...current.noise_params, [key]: Number(event.target.value) } })); }} className="w-full rounded-lg border border-slate-300 px-2 py-2" /></label>)}</div>}
          {config.backend_type === 'hardware' && <div className="flex items-start gap-2 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-3 text-xs text-slate-600"><CircleSlash2 className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" /><span><b>Hardware credentials not found.</b> Currently, real quantum hardware requests will be routed to a noisy simulator fallback until a provider token is configured.</span></div>}
        </section>
      </div>

      <aside className="space-y-5">
        <section className="card-scientific space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2"><Layers className="h-4 w-4 text-quantum-700" /><h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Feature-to-qubit mapping</h2></div>
          {mapping.length ? <ol className="space-y-2">{mapping.map(({ feature, qubit }) => <li key={feature} className="flex justify-between rounded-lg bg-slate-50 px-3 py-2 text-xs"><span className="truncate font-mono">{feature}</span><span className="font-semibold text-quantum-800">q{qubit}</span></li>)}</ol> : <p className="text-xs text-slate-500">No selected feature list is available yet.</p>}
          <div className="border-t border-slate-100 pt-3 text-[11px] text-slate-500 font-mono">
            z = mean(⟨Zᵢ⟩) + bias
          </div>
        </section>
        <section className="card-scientific space-y-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Save configuration</h2>
          <p className="text-[11px] text-slate-500">The circuit topology and training configuration is stored locally until training begins.</p>
          {saved && <p role="status" className="text-xs font-semibold text-emerald-700 bg-emerald-50 p-2 rounded">Circuit configuration successfully saved.</p>}
          <button type="button" onClick={save} disabled={config.n_qubits < 1 || config.n_qubits > 8 || config.n_layers < 1 || (config.backend_type === 'default.mixed' && Object.values(config.noise_params).some((value) => value < 0 || value > 0.5))} className="btn-secondary flex w-full items-center justify-center gap-2 text-xs disabled:opacity-50"><Save className="h-4 w-4" /><span>Save circuit settings</span></button>
          <button type="button" onClick={() => { save(); navigate('/training'); }} disabled={config.n_qubits < 1 || config.n_qubits > 8 || !isCompatible} className="btn-primary flex w-full items-center justify-center gap-2 text-xs disabled:opacity-50"><span>Save and return to training</span><ArrowRight className="h-4 w-4" /></button>
        </section>
      </aside>
    </div>
  </div>;
};
