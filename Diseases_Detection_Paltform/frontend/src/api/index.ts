import { apiClient } from './client';
import {
  User,
  AuthResponse,
  Dataset,
  DatasetVersion,
  DatasetAnalysis,
  PreprocessingPlan,
  PreprocessingPlanStep,
  PreprocessingRunResult,
  FeatureSelectionRun,
  Model,
  ModelVersion,
  TrainingRun,
  QuantumDevice,
  PredictionResponse,
  ComprehensiveComparisonResponse,
  Experiment,
  Artifact,
  SystemHealth,
} from '../types';

export const authApi = {
  login: async (credentials: { username: string; password: string }): Promise<AuthResponse> => {
    const payload = {
      email: credentials.username,
      password: credentials.password,
    };
    const res = await apiClient.post<AuthResponse>('/auth/login', payload);
    return res.data;
  },

  register: async (payload: {
    email: string;
    password: string;
    full_name: string;
    role?: string;
  }): Promise<User> => {
    const res = await apiClient.post<{ data: User }>('/auth/register', payload);
    return res.data.data;
  },

  me: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },
};

export const datasetsApi = {
  list: async (): Promise<Dataset[]> => {
    const res = await apiClient.get<Dataset[]>('/datasets');
    return res.data;
  },

  get: async (id: string): Promise<Dataset> => {
    const res = await apiClient.get<Dataset>(`/datasets/${id}`);
    return res.data;
  },

  create: async (payload: { name: string; description?: string }): Promise<Dataset> => {
    const res = await apiClient.post<{ data: Dataset }>('/datasets', payload);
    return res.data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/datasets/${id}`);
  },

  uploadVersion: async (
    datasetId: string,
    file: File,
    versionTag: string = 'v1.0'
  ): Promise<DatasetVersion> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('version_tag', versionTag);
    const res = await apiClient.post<{ data: DatasetVersion }>(
      `/datasets/${datasetId}/versions`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return res.data.data;
  },

  analyzeVersion: async (datasetId: string, versionId: string): Promise<DatasetAnalysis> => {
    const res = await apiClient.get<DatasetAnalysis>(
      `/datasets/${datasetId}/versions/${versionId}/analysis`
    );
    return res.data;
  },
};

export const preprocessingApi = {
  generatePlan: async (payload: {
    dataset_version_id: string;
    target_column?: string;
  }): Promise<PreprocessingPlan> => {
    const res = await apiClient.post<{ data: PreprocessingPlan }>('/preprocessing/plan', payload);
    return res.data.data;
  },

  executePlan: async (payload: {
    dataset_version_id: string;
    target_column?: string;
    steps?: PreprocessingPlanStep[];
  }): Promise<PreprocessingRunResult> => {
    const res = await apiClient.post<{ data: PreprocessingRunResult }>('/preprocessing/execute', payload);
    return res.data.data;
  },
};

export const featuresApi = {
  selectFeatures: async (payload: {
    dataset_version_id: string;
    ranking_method: string;
    k_features: number;
  }): Promise<FeatureSelectionRun> => {
    const res = await apiClient.post<{ data: FeatureSelectionRun }>('/features/select', payload);
    return res.data.data;
  },
};

export const modelsApi = {
  list: async (): Promise<Model[]> => {
    const res = await apiClient.get<Model[]>('/models');
    return res.data;
  },

  listDefaults: async (): Promise<Model[]> => {
    const res = await apiClient.get<Model[]>('/models/defaults');
    return res.data;
  },

  get: async (id: string): Promise<Model> => {
    const res = await apiClient.get<Model>(`/models/${id}`);
    return res.data;
  },

  compare: async (modelIds: string[]): Promise<ComprehensiveComparisonResponse> => {
    const res = await apiClient.post<ComprehensiveComparisonResponse>('/models/compare', {
      model_ids: modelIds,
    });
    return res.data;
  },
};

export const trainingApi = {
  startRun: async (payload: {
    model_id: string;
    dataset_version_id: string;
    feature_selection_run_id: string;
  }): Promise<TrainingRun> => {
    const res = await apiClient.post<{ data: TrainingRun }>('/training', payload);
    return res.data.data;
  },

  getStatus: async (runId: string): Promise<TrainingRun> => {
    const res = await apiClient.get<TrainingRun>(`/training/${runId}`);
    return res.data;
  },
};

export const predictionsApi = {
  predict: async (payload: {
    model_id: string;
    features: Record<string, number> | Record<string, number>[];
    decision_threshold?: number;
  }): Promise<PredictionResponse> => {
    const res = await apiClient.post<PredictionResponse>('/predictions', payload);
    return res.data;
  },
};

export const quantumApi = {
  listDevices: async (): Promise<QuantumDevice[]> => {
    const res = await apiClient.get<QuantumDevice[]>('/quantum/devices');
    return res.data;
  },

  submitJob: async (payload: {
    device_id: string;
    circuit_data: Record<string, any>;
    shots?: number;
  }): Promise<{ job_id: string; status: string }> => {
    const res = await apiClient.post<{ data: { job_id: string; status: string } }>(
      '/quantum/jobs',
      payload
    );
    return res.data.data;
  },
};

export const experimentsApi = {
  list: async (): Promise<Experiment[]> => {
    const res = await apiClient.get<Experiment[]>('/experiments');
    return res.data;
  },

  create: async (payload: {
    name: string;
    description?: string;
    tags?: string[];
  }): Promise<Experiment> => {
    const res = await apiClient.post<{ data: Experiment }>('/experiments', payload);
    return res.data.data;
  },

  compareRuns: async (experimentId: string, trainingRunIds: string[]): Promise<any> => {
    const res = await apiClient.post<{ data: any }>(`/experiments/${experimentId}/compare`, {
      training_run_ids: trainingRunIds,
    });
    return res.data.data;
  },
};

export const artifactsApi = {
  list: async (): Promise<Artifact[]> => {
    const res = await apiClient.get<Artifact[]>('/artifacts');
    return res.data;
  },
};

export const healthApi = {
  getHealth: async (): Promise<SystemHealth> => {
    const res = await apiClient.get<SystemHealth>('/health');
    return res.data;
  },

  getVersion: async (): Promise<{ version: string; environment: string }> => {
    const res = await apiClient.get<{ version: string; environment: string }>('/version');
    return res.data;
  },
};
