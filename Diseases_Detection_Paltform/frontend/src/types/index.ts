export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'clinician' | 'researcher' | 'admin';
  institution?: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Dataset {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  versions?: DatasetVersion[];
}

export interface DatasetVersion {
  id: string;
  dataset_id: string;
  user_id: string;
  version_tag: string;
  row_count: number;
  column_count: number;
  status: string;
  dataset_metadata?: {
    columns: string[];
    dtypes: Record<string, string>;
    filename: string;
  };
  created_at: string;
}

export interface DatasetAnalysis {
  dataset_id: string;
  version_id: string;
  row_count: number;
  column_count: number;
  numerical_columns: string[];
  categorical_columns: string[];
  missing_value_counts: Record<string, number>;
}

export interface PreprocessingPlanStep {
  step_id: number;
  tool_name: string;
  rationale: string;
  parameters: Record<string, any>;
  fit_on_train_only: boolean;
}

export interface PreprocessingPlan {
  dataset_id: string;
  dataset_version_id: string;
  steps: PreprocessingPlanStep[];
  summary: string;
  leakage_prevention_guarantee: string;
}

export interface PreprocessingRunResult {
  run_id: string;
  dataset_version_id: string;
  status: string;
  train_samples: number;
  val_samples: number;
  test_samples: number;
  feature_names: string[];
  leakage_audit: string;
}

export interface FeatureSelectionRun {
  id: string;
  dataset_version_id: string;
  user_id: string;
  ranking_method: string;
  feature_count: number;
  selected_features: string[];
  ranking_scores: Record<string, number>;
  created_at: string;
}

export interface Model {
  id: string;
  user_id?: string | null;
  name: string;
  model_type: 'SVM_LINEAR' | 'SVM_RBF' | 'VQC';
  description?: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  versions?: ModelVersion[];
}

export interface ModelVersion {
  id: string;
  model_id: string;
  version_tag: string;
  dataset_version_id?: string;
  feature_selection_run_id?: string;
  hyperparameters?: Record<string, any>;
  quantum_config?: {
    qubit_count: number;
    layers: number;
    backend_type: string;
    entanglement: string;
  };
  metrics?: {
    accuracy: number;
    balanced_accuracy?: number;
    sensitivity: number;
    specificity: number;
    precision: number;
    f1_score: number;
    roc_auc: number;
    training_time_seconds?: number;
    inference_time_ms?: number;
    confusion_matrix?: {
      tp: number;
      tn: number;
      fp: number;
      fn: number;
    };
  };
  is_default: boolean;
  status: string;
  created_at: string;
}

export interface TrainingRun {
  id: string;
  model_id: string;
  user_id: string;
  dataset_version_id: string;
  feature_selection_run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  metrics?: Record<string, number>;
  loss_history?: number[];
  error_message?: string;
}

export interface QuantumDevice {
  device_id: string;
  provider: string;
  device_type: 'simulator' | 'noisy_simulator' | 'hardware';
  qubits: number;
  shots_supported: number[];
  status: 'ONLINE' | 'OFFLINE' | 'BUSY';
  average_queue_time_seconds: number;
}

export interface QuantumJob {
  job_id: string;
  device_id: string;
  provider: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  submitted_at: string;
  completed_at?: string;
  shots: number;
  circuit_depth?: number;
}

export interface RiskStratification {
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  score: number;
}

export interface SinglePredictionResult {
  predicted_class: number;
  predicted_label: 'POSITIVE' | 'NEGATIVE';
  probability: number;
  risk_stratification: RiskStratification;
  input_features_used: string[];
  sample_id?: string;
}

export interface PredictionResponse {
  model_id: string;
  decision_threshold_applied: number;
  results: SinglePredictionResult[];
  timestamp: string;
}

export interface MetricComparisonRow {
  metric_name: string;
  unit: string;
  higher_is_better: boolean;
  values: Record<string, number>;
}

export interface ModelComparisonEntry {
  model_id: string;
  model_name: string;
  model_type: string;
  version_tag: string;
  is_quantum: boolean;
  feature_count: number;
  selected_features: string[];
  accuracy: number;
  balanced_accuracy: number;
  sensitivity: number;
  specificity: number;
  precision: number;
  f1_score: number;
  roc_auc: number;
  training_time_seconds: number;
  confusion_matrix: {
    tp: number;
    tn: number;
    fp: number;
    fn: number;
  };
}

export interface ComprehensiveComparisonResponse {
  timestamp: string;
  models_compared_count: number;
  models: ModelComparisonEntry[];
  metrics_matrix: MetricComparisonRow[];
  best_performer: {
    by_accuracy: string;
    by_sensitivity_recall: string;
    by_f1_score: string;
    by_roc_auc: string;
  };
  cml_vs_qml_insights: string[];
  markdown_comparison_table: string;
}

export interface Experiment {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  tags?: string[];
  created_at: string;
  reproducibility_chain?: {
    dataset_version_id: string;
    feature_selection_run_id: string;
    training_run_ids: string[];
    models_evaluated: string[];
  };
}

export interface Artifact {
  id: string;
  user_id: string;
  name: string;
  artifact_type: string;
  relative_path: string;
  size_bytes: number;
  created_at: string;
}

export interface SystemHealth {
  status: string;
  version: string;
  database: 'healthy' | 'unhealthy';
  redis: 'healthy' | 'unhealthy';
  llm_service: 'healthy' | 'unhealthy';
  quantum_simulator: 'healthy' | 'unhealthy';
}
