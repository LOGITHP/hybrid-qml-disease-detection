import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { AppShell } from './components/layout/AppShell';

// Public Pages
import { LandingPage } from './pages/landing/LandingPage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';

// Authenticated Domain Pages
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { DatasetListPage } from './pages/datasets/DatasetListPage';
import { DatasetDetailPage } from './pages/datasets/DatasetDetailPage';
import { PreprocessingPage } from './pages/preprocessing/PreprocessingPage';
import { FeatureSelectionPage } from './pages/features/FeatureSelectionPage';
import { ModelListPage } from './pages/models/ModelListPage';
import { ModelDetailPage } from './pages/models/ModelDetailPage';
import { VQCConfigPage } from './pages/models/VQCConfigPage';
import { TrainingWizardPage } from './pages/training/TrainingWizardPage';
import { TrainingMonitorPage } from './pages/training/TrainingMonitorPage';
import { QuantumDevicesPage } from './pages/quantum/QuantumDevicesPage';
import { PredictionPage } from './pages/predictions/PredictionPage';
import { PredictionDetailPage } from './pages/predictions/PredictionDetailPage';
import { EvaluationPage } from './pages/evaluation/EvaluationPage';
import { ModelComparisonPage } from './pages/evaluation/ModelComparisonPage';
import { ExplainabilityPage } from './pages/explainability/ExplainabilityPage';
import { ExperimentListPage } from './pages/experiments/ExperimentListPage';
import { ExperimentDetailPage } from './pages/experiments/ExperimentDetailPage';
import { ReportListPage } from './pages/reports/ReportListPage';
import { ReportDetailPage } from './pages/reports/ReportDetailPage';
import { ArtifactListPage } from './pages/artifacts/ArtifactListPage';
import { SettingsPage } from './pages/settings/SettingsPage';

// Route Guard component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center font-sans">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-4 border-brand-800 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-slate-500 font-medium">Validating Clinical Session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { path: '/dashboard', element: <DashboardPage /> },
      
      // DATA
      { path: '/datasets', element: <DatasetListPage /> },
      { path: '/datasets/:id', element: <DatasetDetailPage /> },
      { path: '/preprocessing', element: <PreprocessingPage /> },
      { path: '/features', element: <FeatureSelectionPage /> },

      // MODELS
      { path: '/models', element: <ModelListPage /> },
      { path: '/models/:id', element: <ModelDetailPage /> },
      { path: '/models/vqc/configure', element: <VQCConfigPage /> },

      // TRAINING & QUANTUM
      { path: '/training', element: <TrainingWizardPage /> },
      { path: '/training/:id', element: <TrainingMonitorPage /> },
      { path: '/quantum', element: <QuantumDevicesPage /> },

      // RESULTS
      { path: '/predictions', element: <PredictionPage /> },
      { path: '/predictions/:predictionId', element: <PredictionDetailPage /> },
      { path: '/evaluation', element: <EvaluationPage /> },
      { path: '/evaluation/comparison', element: <ModelComparisonPage /> },
      { path: '/explainability/:predictionId', element: <ExplainabilityPage /> },

      // RESEARCH
      { path: '/experiments', element: <ExperimentListPage /> },
      { path: '/experiments/:experimentId', element: <ExperimentDetailPage /> },
      { path: '/reports', element: <ReportListPage /> },
      { path: '/reports/:reportId', element: <ReportDetailPage /> },
      { path: '/artifacts', element: <ArtifactListPage /> },

      // SYSTEM
      { path: '/settings', element: <SettingsPage /> },

      // Fallback
      { path: '*', element: <Navigate to="/dashboard" replace /> },
    ],
  },
]);
