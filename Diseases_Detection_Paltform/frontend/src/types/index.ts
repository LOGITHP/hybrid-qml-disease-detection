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
  columns: string[];
  dtypes: Record<string, string>;
  numerical_columns: string[];
  categorical_columns: string[];
  missing_value_counts: Record<string, number>;
  column_profiles: Record<string, {
    dtype: string;
    missing_count: number;
    missing_percent: number;
    unique_count: number;
    sample_values: (string | number | boolean | null)[];
    statistics?: Record<string, number | string | null>;
    distribution?: { value?: string | number | boolean | null; lower?: number; upper?: number; count: number }[];
  }>;
  file_metadata: {
    filename: string;
    format: string;
    file_size_bytes?: number;
    version_tag: string;
    created_at: string;
  };
  target_column?: string;
  target_candidates: { column_name: string; confidence: number; task_type: string; rationale: string; class_counts: Record<string, number> }[];
  class_distribution?: Record<string, number>;
  duplicate_row_count: number;
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
  preprocessing_run_id: string;
  dataset_version_id: string;
  target_column: string;
  status: string;
  train_samples: number;
  val_samples: number;
  test_samples: number;
  feature_names: string[];
  leakage_audit: string;
  outlier_rows_removed: number;
  unencoded_categorical_columns: string[];
}

export interface FeatureSelectionRun {
  id: string;
  dataset_version_id: string;
  user_id: string;
  ranking_method: string;
  target_column?: string;
  feature_count: number;
  selected_features: string[];
  ranking_scores: Record<string, number>;
  created_at: string;
}

export interface Model {
  id: string;
  user_id?: string | null;
  name: string;
  model_type: string;
  description?: string;
  is_default: boolean;
  status?: string;
  configuration?: Record<string, any>;
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
  experiment_id?: string | null;
  model_id: string;
  model_type?: string;
  user_id: string;
  dataset_version_id: string;
  feature_selection_run_id?: string;
  preprocessing_run_id?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  metrics?: Record<string, any>;
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
  threshold_low_medium?: number;
  threshold_medium_high?: number;
  medical_disclaimer?: string;
}

export interface SinglePredictionResult {
  predicted_class: number;
  predicted_label: string;
  probability?: number | null;
  risk_stratification?: RiskStratification | null;
  input_features_used: string[];
  sample_id?: string;
}

export interface PredictionResponse {
  model_id: string;
  preprocessing_run_id?: string | null;
  feature_selection_run_id?: string | null;
  decision_threshold_applied: number;
  results: SinglePredictionResult[];
  timestamp: string;
}

export interface MetricComparisonRow {
  metric_key: string;
  display_name: string;
  higher_is_better: boolean;
  values: Record<string, number | null>;
  best_model: string;
}

export interface ModelComparisonEntry {
  model_id: string;
  model_name: string;
  model_type: string;
  version_tag: string;
  feature_count: number;
  selected_features: string[];
  accuracy: number;
  sensitivity: number;
  specificity: number;
  precision: number;
  f1_score: number;
  balanced_accuracy?: number | null;
  roc_auc?: number | null;
  training_duration_sec?: number | null;
  quantum_details?: Record<string, any>;
  confusion_matrix: {
    true_positive: number;
    true_negative: number;
    false_positive: number;
    false_negative: number;
  };
}

export interface ComprehensiveComparisonResponse {
  models_compared: ModelComparisonEntry[];
  comparison_matrix: MetricComparisonRow[];
  category_winners: Record<string, string>;
  cml_vs_qml_insights: Record<string, any>;
  markdown_table: string;
  executive_summary: string;
}

export interface Experiment {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  tags?: string[];
  status: string;
  dataset_id?: string;
  dataset_version_id?: string;
  dataset_name?: string;
  preprocessing_run_id?: string;
  feature_selection_run_id?: string;
  target_column?: string;
  selected_features?: string[];
  training_run_ids?: string[];
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
