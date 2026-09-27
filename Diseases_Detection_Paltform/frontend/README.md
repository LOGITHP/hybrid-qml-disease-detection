# Hybrid Quantum Machine Learning Platform for Early Disease Detection: Frontend Application

[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.3+-646CFF.svg)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC.svg)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Multi--stage_Build-2496ED.svg)](https://www.docker.com/)

A production-grade biomedical web application engineered for the:
> **Hybrid Quantum Machine Learning Platform for Early Disease Detection**

The frontend acts as the clinical and biostatistical orchestration layer, communicating directly with the containerized FastAPI backend gateway to deliver an end-to-end diagnostic and screening pipeline:
$$\text{Data Ingestion} \longrightarrow \text{AI Preprocessing} \longrightarrow \text{Canonical Feature Selection} \longrightarrow \text{Classical \& Quantum Training} \longrightarrow \text{Evaluation \& Multi-Model Comparison} \longrightarrow \text{Real-Time Prediction} \longrightarrow \text{Explainability} \longrightarrow \text{Audit Reporting}$$

---

## 1. System Architecture & Information Flow

```mermaid
graph TD
    subgraph "Browser Client (localhost:3000)"
        User([Clinician / Oncologist / Researcher]) --> Shell[AppShell Persistent Layout]
        Shell --> Router[React Router v6 - 28+ Workflows]
        Router --> Views[Domain Feature Modules]
        Views --> Cache[TanStack Query v5 Server State]
        Cache --> Client[Typed Axios Client with JWT Interceptor]
    end

    subgraph "Containerized Nginx Layer"
        Client --> Nginx[Nginx Alpine Reverse Proxy :80]
        Nginx -->|SPA Fallback| StaticBundle[Vite Production Bundle]
        Nginx -->|/api/v1/*| Gateway[FastAPI Backend Gateway :8000]
    end

    subgraph "Backend Services Layer"
        Gateway --> Auth[/auth]
        Gateway --> Datasets[/datasets]
        Gateway --> Preprocess[/preprocessing]
        Gateway --> Features[/features/select]
        Gateway --> Models[/models & /models/compare]
        Gateway --> Training[/training]
        Gateway --> Predictions[/predictions]
        Gateway --> Quantum[/quantum]
    end

    subgraph "Compute & Simulation Engines"
        Preprocess --> Gemma[Dedicated Gemma LLM :8001]
        Preprocess --> Sklearn[Leak-Free Preprocessing Transformers]
        Features --> SingleSource[Single Source of Truth Feature Subset]
        SingleSource --> SVM[Classical Linear & RBF SVM]
        SingleSource --> VQC[PennyLane Quantum Simulators]
        VQC --> IdealSim[default.qubit Statevector]
        VQC --> NoisySim[default.mixed Open System NISQ Noise]
    end
```

---

## 2. Technology Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Core Framework** | React | `18.3.1` | Component-based interactive UI with concurrent rendering |
| **Language** | TypeScript | `5.5.3` | Strict static typing matching backend Pydantic models |
| **Build Tool** | Vite | `5.3.3` | High-speed ESM bundling and zero-config compilation |
| **Styling** | Tailwind CSS | `3.4.4` | Scientific design tokens (Deep Navy, Slate Blue, Quantum Indigo) |
| **Icons** | Lucide React | `0.400.0` | Accessible, tree-shakeable iconography |
| **State & Caching** | TanStack Query | `5.51.1` | Intelligent caching, background refetching, and mutation status |
| **Routing** | React Router DOM | `6.24.1` | Client-side routing with `ProtectedRoute` session guards |
| **API Client** | Axios | `1.7.2` | Typed HTTP client with automatic Bearer token injection and error normalization |
| **Production Server**| Nginx Alpine | `1.27+` | High-performance static web server with gzip compression & API proxying |

---

## 3. Complete Architecture & Directory Structure (Frontend & Backend)

The entire development platform is organized under [`Diseases_Detection_Paltform/`](file:///Diseases_Detection_Paltform/), separating the client-side user experience from the containerized computational backend:

```
Diseases_Detection_Paltform/
│
├── frontend/                                   # Production React 18 / TypeScript Client
│   ├── public/                                 # Static assets & platform SVG favicon
│   ├── src/
│   │   ├── api/                                # Typed API client modules
│   │   │   ├── client.ts                       # Axios instance with Bearer JWT interceptor & 401 handling
│   │   │   └── index.ts                        # Endpoints: auth, datasets, preprocessing, features, models, training, etc.
│   │   ├── components/
│   │   │   ├── common/                         # Shared UI primitives
│   │   │   │   ├── MetricCard.tsx              # Quantitative KPI cards with status badges
│   │   │   │   ├── StatusBadge.tsx             # Color-coded clinical chips (completed, running, high risk)
│   │   │   │   ├── EmptyState.tsx              # Informative empty states with actionable CTAs
│   │   │   │   ├── ErrorState.tsx              # Human-readable error presentations with retry triggers
│   │   │   │   ├── LoadingSkeleton.tsx         # Animated pulse loaders for tables, cards, and charts
│   │   │   │   ├── WorkflowStepper.tsx         # 7-step visual workflow stepper
│   │   │   │   └── MedicalNotice.tsx           # Clinical decision support disclaimer banners
│   │   │   └── layout/
│   │   │       ├── AppShell.tsx                # Persistent application frame with mobile drawer
│   │   │       ├── Sidebar.tsx                 # Grouped navigation (OVERVIEW, DATA, MODELS, RESULTS, RESEARCH, SYSTEM)
│   │   │       └── Topbar.tsx                  # Breadcrumbs, live gateway connectivity pulse, quick action triggers
│   │   ├── context/
│   │   │   └── AuthContext.tsx                 # Authentication state, login/register, and one-click demo login
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   │   ├── LoginPage.tsx               # Dual-pane login with demo clinician autofill
│   │   │   │   └── RegisterPage.tsx            # Clinical investigator onboarding
│   │   │   ├── dashboard/
│   │   │   │   └── DashboardPage.tsx           # Command center: KPI summary, workflow widget, pretrained zoo
│   │   │   ├── datasets/
│   │   │   │   ├── DatasetListPage.tsx         # Ingestion registry, CSV drag-and-drop, benchmark loader
│   │   │   │   └── DatasetDetailPage.tsx       # Schema explorer, missingness analysis, immutable version ledger
│   │   │   ├── preprocessing/
│   │   │   │   └── PreprocessingPage.tsx       # 7-step AI wizard: Gemma plan formulation, approval, leakage audit
│   │   │   ├── features/
│   │   │   │   └── FeatureSelectionPage.tsx    # Single Source of Truth ranking & canonical feature subset selection
│   │   │   ├── models/
│   │   │   │   ├── ModelListPage.tsx           # Pretrained model zoo (Linear/RBF SVM, 4/6/8-Qubit VQC)
│   │   │   │   ├── ModelDetailPage.tsx         # Model hyperparameters, architecture specifications, metrics
│   │   │   │   └── VQCConfigPage.tsx           # PennyLane circuit topology viewer & qubit compatibility validator
│   │   │   ├── training/
│   │   │   │   ├── TrainingWizardPage.tsx      # 5-step model training dispatch wizard
│   │   │   │   └── TrainingMonitorPage.tsx     # Live convergence monitor & loss history ledger
│   │   │   ├── quantum/
│   │   │   │   └── QuantumDevicesPage.tsx      # Quantum backend registry (Statevector, Noisy NISQ, QPU)
│   │   │   ├── predictions/
│   │   │   │   ├── PredictionPage.tsx          # Real-time screening input form & threshold tuning slider
│   │   │   │   └── PredictionDetailPage.tsx    # Probability bar gauge & risk category stratification
│   │   │   ├── evaluation/
│   │   │   │   ├── EvaluationPage.tsx          # Accuracy, sensitivity, ROC-AUC, confusion matrix, threshold curves
│   │   │   │   └── ModelComparisonPage.tsx     # Multi-model side-by-side benchmark table & winner designation
│   │   │   ├── explainability/
│   │   │   │   └── ExplainabilityPage.tsx      # Biomarker feature attribution bars & technical quantum provenance
│   │   │   ├── experiments/
│   │   │   │   ├── ExperimentListPage.tsx      # Screening campaign index
│   │   │   │   └── ExperimentDetailPage.tsx    # End-to-end reproducibility timeline
│   │   │   ├── reports/
│   │   │   │   ├── ReportListPage.tsx          # Audit documentation index
│   │   │   │   └── ReportDetailPage.tsx        # Print-ready clinical research report with PDF export
│   │   │   ├── artifacts/
│   │   │   │   └── ArtifactListPage.tsx        # Cryptographic checksums and serialized model binaries
│   │   │   └── settings/
│   │   │       └── SettingsPage.tsx            # Clinician profile, security, and live subsystem telemetry
│   │   ├── types/
│   │   │   └── index.ts                        # TypeScript interfaces matching backend models
│   │   ├── index.css                           # Tailwind CSS directives, custom scrollbars, and design tokens
│   │   ├── main.tsx                            # Root React entry point mounting QueryClient & AuthProvider
│   │   └── router.tsx                          # Complete 28+ route tree protected by session guards
│   ├── .env.example                            # Frontend environment template
│   ├── Dockerfile                              # Multi-stage production container (Node 20 build -> Nginx Alpine)
│   ├── nginx.conf                              # Nginx configuration: SPA fallback & reverse proxy to backend
│   ├── package.json                            # NPM dependencies and build scripts
│   ├── tailwind.config.js                      # Custom scientific color palette configuration
│   ├── tsconfig.json                           # Strict TypeScript compiler options
│   └── vite.config.ts                          # Vite build config with path aliases & dev proxy
│
└── backend/                                    # Production FastAPI Application Layer
    ├── app/
    │   ├── agents/
    │   │   └── preprocessing_agent/            # Integrated AI Preprocessing Agent
    │   │       ├── agent/                      # LangGraph graph definition & state machine
    │   │       ├── pipeline/                   # Pipeline execution orchestrator & leak-free transformer
    │   │       ├── reporting/                  # Markdown & JSON audit logging generator
    │   │       ├── schemas/                    # Pydantic schemas for data profiling & transformation logs
    │   │       ├── tools/                      # Scikit-Learn data cleaning, imputers, scalers, encoders
    │   │       ├── utils/                      # Helper utilities
    │   │       └── interface.py                # PreprocessingAgent service combining Gemma LLM with deterministic tools
    │   ├── api/v1/                             # FastAPI REST Endpoints
    │   │   ├── auth.py                         # User registration, Argon2id password hashing, OAuth2 JWT login
    │   │   ├── datasets.py                     # Dataset creation, CSV ingestion, statistical profiling
    │   │   ├── preprocessing.py                # Dedicated AI plan generation (/plan) and leak-free execution (/execute)
    │   │   ├── features.py                     # Single Source of Truth canonical feature selection (/select)
    │   │   ├── models.py                       # Model listing, default zoo, and multi-model comparison (/compare)
    │   │   ├── training.py                     # Classical & Quantum training execution and status tracking
    │   │   ├── predictions.py                  # Real-time inference, threshold tuning, and risk stratification
    │   │   ├── quantum.py                      # Quantum backend listing and circuit job dispatch
    │   │   ├── experiments.py                  # Campaign tracking & comparative benchmark aggregation
    │   │   ├── artifacts.py                    # Secure artifact inspection and download
    │   │   ├── health.py                       # Live health checks for Database, Redis, LLM, and Simulators
    │   │   └── router.py                       # Master API v1 router bundling all domain routers
    │   ├── core/                               # Application Core
    │   │   ├── config.py                       # Pydantic settings loading from environment variables
    │   │   ├── dependencies.py                 # FastAPI dependency injection (DB sessions, auth user, services)
    │   │   ├── exceptions.py                   # Normalized error hierarchy (401, 403, 404, 422, 500)
    │   │   ├── logging.py                      # Structured JSON logging
    │   │   └── security.py                     # Argon2id password hashing & HS256 JWT encoding/decoding
    │   ├── database/                           # Persistence Layer
    │   │   ├── base.py                         # SQLAlchemy declarative base
    │   │   ├── session.py                      # Async SQLAlchemy engine with connection pooling
    │   │   └── models/                         # Relational Database Models (19 Tables)
    │   │       ├── user.py                     # User account & role-based access control
    │   │       ├── dataset.py                  # Dataset container & immutable DatasetVersion
    │   │       ├── preprocessing.py            # PreprocessingRun & transformation plan records
    │   │       ├── feature_selection.py        # FeatureSelectionRun (canonical selected feature list)
    │   │       ├── model.py                    # Model & ModelVersion with is_default support
    │   │       ├── training.py                 # TrainingRun logs & duration
    │   │       ├── evaluation.py               # EvaluationRun metrics (Acc, Sens, Spec, Prec, F1, AUC)
    │   │       ├── prediction.py               # Patient screening inference logs & risk scores
    │   │       ├── quantum.py                  # QuantumJob execution logs
    │   │       ├── experiment.py               # Experiment campaign grouping
    │   │       ├── artifact.py                 # Stored file metadata & checksums
    │   │       └── audit.py                    # Audit log for HIPAA compliance
    │   ├── interfaces/                         # Abstract Base Contracts
    │   │   ├── model.py                        # IModel interface for both SVM and VQC
    │   │   ├── preprocessing.py                # IPreprocessingEngine interface
    │   │   └── quantum.py                      # IQuantumBackend interface
    │   ├── llm/                                # Clinical Reasoning Integration
    │   │   ├── base.py                         # ILLMProvider interface
    │   │   ├── gemma.py                        # HTTP client communicating with Gemma microservice (:8001)
    │   │   └── factory.py                      # Provider factory
    │   ├── ml/                                 # Machine Learning Engines
    │   │   ├── classical/svm/                  # Linear & RBF Support Vector Machines with Platt scaling
    │   │   ├── quantum/vqc/                    # PennyLane Variational Quantum Classifier (noiseless & noisy NISQ)
    │   │   └── loader.py                       # PretrainedModelLoader initializing pre-trained models
    │   ├── quantum/                            # Quantum Computing Infrastructure
    │   │   └── registry.py                     # Device registry: default.qubit, default.mixed, physical QPU connector
    │   ├── repositories/                       # Clean Data Access Layer (Repositories)
    │   ├── schemas/                            # Pydantic Request & Response Schemas
    │   ├── services/                           # Business Logic Layer (Services)
    │   └── workers/                            # Celery asynchronous task queues
    ├── config/                                 # Default configuration files
    ├── gemma/                                  # Dedicated Isolated Gemma LLM Inference Microservice (:8001)
    │   ├── Dockerfile                          # Lightweight Python container
    │   ├── requirements.txt                    # Dependencies for Gemma inference server
    │   └── server.py                           # FastAPI microservice serving clinical reasoning
    ├── migrations/                             # Alembic asynchronous database migrations
    ├── models/pretrained/                      # Stored pre-trained models accessible by default to all users
    │   ├── classical_linear_svm_4_feats.joblib # 4-feature Linear SVM binary
    │   ├── classical_rbf_svm_4_feats.joblib    # 4-feature RBF SVM binary
    │   ├── vqc_4_weights.npy & bias            # 4-Qubit Noiseless VQC parameters
    │   ├── vqc_noisy_4_weights.npy & bias      # 4-Qubit Noisy NISQ VQC parameters
    │   ├── vqc_6_weights.npy & bias            # 6-Qubit VQC parameters
    │   ├── vqc_8_weights.npy & bias            # 8-Qubit VQC parameters
    │   └── metadata.json                       # Catalog of benchmark evaluation scores
    ├── artifacts/                              # Local directory for immutable datasets & serialized models
    ├── tests/                                  # Unit, API, and Integration Test Suite
    ├── Dockerfile                              # Backend multi-stage production container
    ├── docker-compose.yml                      # Backend service stack specification
    ├── requirements.txt                        # Python dependencies
    └── README.md                               # Detailed backend documentation
```

---

## 4. Scientific Design System

The platform strictly avoids generic templates, neon gimmicks, or oversaturated gaming interfaces, implementing a restrained clinical palette:

- **Primary Brand:** Deep Navy (`#0B192C` / `#1E3E62`) — navigation bars, primary CTAs, major headers.
- **Secondary / Borders:** Cool Slate (`#334155` / `#64748B`) — card outlines, table headers, metadata chips.
- **Quantum Accent:** Quantum Indigo / Violet (`#6366F1` / `#4F46E5`) — qubit wire indicators, PennyLane topology badges, VQC highlights.
- **Clinical Indicators:**
  - Emerald Green (`#10B981`): Low risk, high sensitivity, completed jobs, verified integrity.
  - Clinical Amber (`#F59E0B`): Moderate risk, class imbalance alerts, running jobs.
  - Clinical Red (`#EF4444`): High disease risk, critical missed false negatives, failed tasks.
- **Typography:** Inter sans-serif with JetBrains Mono for biomedical telemetry, mathematical formulas, and parameters.

---

## 4. Step-by-Step Clinical Screening Workflow

### Step 1: Authentication & Demonstration Mode
- Navigate to `/login`.
- **Autofill Demo Button:** Click **"Autofill Demo"** to log in immediately with pre-seeded clinician credentials (`clinician@hybridqml.org` / `DoctorPass123!`).
- Registration for biostatisticians and oncology researchers is available at `/register`.

### Step 2: Biomedical Dataset Ingestion
- Navigate to `/datasets`.
- **One-Click Benchmark Loader:** Click **"Load Benchmark Cohort"** to immediately ingest the authentic 309-patient lung cancer clinical trial cohort (`survey_lung_cancer.csv`), or drag-and-drop any standard tabular CSV.
- Inspect row counts, column counts, missing values, and data types on `/datasets/:id`.

### Step 3: AI Preprocessing Agent (Zero Data Leakage Protocol)
- Navigate to `/preprocessing`.
- The 7-step interactive wizard guides the user through:
  1. **Dataset Selection:** Choose active clinical trial cohort.
  2. **Statistical Telemetry Analysis:** Review missingness and class balance.
  3. **AI Strategy Formulation:** Gemma LLM analyzes metadata and proposes a step-by-step transformation plan.
  4. **Human-in-the-Loop Review:** Clinician inspects plan steps, rationale, and parameter settings.
  5. **Plan Approval:** Approve or modify the transformation rules.
  6. **Deterministic Execution:** The engine applies stratified partitioning (70% Train, 15% Validation, 15% Test), median imputation, and MinMax scaling.
  7. **Leakage Audit:** Verifies that transformers were fitted strictly on training samples ($X_{\text{train}}$) and never refit on validation/test sets.

### Step 4: Canonical Feature Selection (Single Source of Truth)
- Navigate to `/features`.
- Select ranking method: **Mutual Information**, **Random Forest Gini**, or **ANOVA F-Test**.
- Adjust the canonical feature slider ($k \in [2, 8]$, recommended: $k = 4$).
- Top ranked clinical biomarkers: `WHEEZING`, `YELLOW_FINGERS`, `AGE`, `SHORTNESS_OF_BREATH`.
- **Crucial Architectural Guarantee:** This selected feature set is locked as the **Single Source of Truth** and fed identically to both Classical SVM and PennyLane VQC models. Neither model family configures features independently.

### Step 5: Model Zoo & PennyLane VQC Architecture
- Navigate to `/models`.
- Browse production pre-trained models:
  - **Classical Linear SVM:** Convex linear boundary with calibrated probabilities.
  - **Classical RBF SVM:** Radial Basis Function kernel capturing non-linear feature interactions.
  - **PennyLane 4-Qubit VQC (Noiseless):** Ideal statevector simulation (`default.qubit`).
  - **PennyLane 4-Qubit VQC (Noisy NISQ):** Open-system simulation with depolarizing noise ($p=0.5\%$) and readout error ($p=1.5\%$) (`default.mixed`).
  - **PennyLane 6-Qubit & 8-Qubit VQC:** Scaled quantum circuit variants.
- Configure quantum circuits on `/models/vqc/configure`:
  - AngleEmbedding: $RY(x_i \cdot \pi)$ state preparation.
  - Ansatz: 2 variational layers with linear CNOT entanglement topology.
  - Measurement: Pauli-Z expectation pooling $\frac{1}{N}\sum \langle Z_i \rangle$.
  - Compatibility Checker: Confirms that required qubits match the canonical selected feature count.

### Step 6: Training Orchestration & Convergence Monitoring
- Navigate to `/training`.
- Select model archetype, link canonical features, choose execution backend (Simulator or Noisy NISQ), and dispatch training.
- Live monitor on `/training/:id` displays loss progression, convergence curves, and validation accuracy.

### Step 7: Multi-Model Evaluation & Comparative Benchmarking
- Navigate to `/evaluation/comparison`.
- **Multi-Model Selector:** Check 2 or more models (e.g. Linear SVM, RBF SVM, 4-Qubit VQC Noiseless, 4-Qubit VQC Noisy).
- The system calls `POST /api/v1/models/compare` and renders a comprehensive comparison:
  1. **All 8 Evaluation Metrics:** Accuracy, Balanced Accuracy, Sensitivity (Recall), Specificity, Precision, F1-Score, ROC-AUC, Training Time.
  2. **Side-by-Side Confusion Matrices:** True Positives ($TP$), False Negatives ($FN$), False Positives ($FP$), True Negatives ($TN$).
  3. **Category Winners:** Best Accuracy, Best Sensitivity (essential for minimizing missed diagnoses in early cancer screening), Best F1, and Best ROC-AUC.
  4. **CML vs QML Benchmark Insights:** Explanatory analysis comparing classical vs quantum performance and noise resilience.

### Step 8: Patient Risk Inference & Decision Threshold Tuning
- Navigate to `/predictions`.
- Enter patient biomarker telemetry or click **"Preset: High Risk Profile"** / **"Preset: Low Risk Profile"**.
- Adjust the **Decision Threshold Slider** ($\tau \in [0.10, 0.90]$).
- Click **"Evaluate Patient Risk"** to execute real-time inference.
- View detailed results on `/predictions/:predictionId`:
  - Predicted Class: `POSITIVE` or `NEGATIVE`
  - Probability Gauge: e.g. `82.4%`
  - Stratified Risk Category: `LOW` (emerald), `MEDIUM` (amber), `HIGH` (crimson).
  - Medical Decision Support Notice: Clearly reinforces that output is a computational screening estimate.

### Step 9: Clinical Explainability & Research Audit Reports
- Navigate to `/explainability/:predictionId`:
  - Inspect biomarker feature attribution bars demonstrating relative mathematical contributions.
  - Review technical provenance: quantum backend device, circuit layers, and data scaling bounds.
- Navigate to `/experiments` to trace the complete unbroken reproducibility chain:
  $$\text{Dataset Version} \longrightarrow \text{Preprocessing Run} \longrightarrow \text{Feature Selection Run} \longrightarrow \text{Model Version} \longrightarrow \text{Training Run} \longrightarrow \text{Evaluation}$$
- Navigate to `/reports` for print-ready, auditable clinical research documentation with one-click PDF export.

---

## 5. Configuration & Environment Variables

Create `.env` in `Diseases_Detection_Paltform/frontend/`:

```env
# URL for the FastAPI backend gateway
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Nginx Reverse Proxy (`nginx.conf`)
During containerized deployment, Nginx serves the compiled SPA from `/usr/share/nginx/html` and transparently proxies all requests matching `/api/v1/` directly to `http://backend:8000/api/v1/` on the internal Docker network.

---

## 6. How to Run with Docker

### Option A: Complete 6-Service Stack (Recommended)
From the repository root, start the entire containerized platform:

```bash
docker-compose up --build -d
```

#### Services Started:
- **Clinical Frontend Application:** `http://localhost:3000`
- **FastAPI Backend Gateway:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/api/v1/docs`
- **Dedicated Gemma LLM Microservice:** `http://localhost:8001`
- **PostgreSQL 16 Database:** `localhost:5432`
- **Redis 7 Broker & Cache:** `localhost:6379`
- **Celery Worker:** Asynchronous background training & QPU execution

### Option B: Standalone Frontend Docker Container
To build and run only the frontend container:

```bash
cd Diseases_Detection_Paltform/frontend
docker build -t hybrid-qml-frontend:latest .
docker run -p 3000:80 -e VITE_API_BASE_URL=http://localhost:8000/api/v1 hybrid-qml-frontend:latest
```

Access the application in your browser at:
```
http://localhost:3000
```

---

## 7. Medical Safety & Clinical Notice

> **IMPORTANT MEDICAL NOTICE:**
> The Hybrid Quantum Machine Learning Platform for Early Disease Detection is a research and computational screening tool. Predictions, estimated probabilities, and risk stratifications (`LOW`, `MEDIUM`, `HIGH`) are statistical model outputs and do **NOT** constitute definitive medical diagnoses or clinical guarantees. All findings must be evaluated by licensed medical practitioners alongside conventional diagnostic modalities.
