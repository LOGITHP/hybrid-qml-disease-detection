# AI Biomedical Data Preprocessing & Feature Engineering Agent

An intelligent, production-structured data engineering agent built with **LangGraph**, designed specifically to automate biomedical tabular dataset inspection, data quality verification, leakage-free transformation, quantum-aligned feature budgeting, and rigorous post-processing validation.

---

## 1. Core Architectural Principles

The system adheres strictly to the **AI Agent + Deterministic Tool Architecture**:

- **Agent / LLM Responsibilities:** Reasoning, planning, interpreting data quality reports, selecting appropriate tools, configuring parameters, orchestrating execution graphs, handling errors, and explaining decisions.
- **Deterministic Python Tools Responsibilities:** Dataframe manipulations, statistical profiling, missing-value imputation, deduplication, categorical normalization, one-hot encoding, min-max scaling, feature selection, PCA projection, stratified train/test splitting, and integrity validation.
- **No Numerical Hallucination:** The agent never fabricates metrics, values, or distributions; every logged metric is deterministically calculated by validated scikit-learn/pandas routines.
- **Dual-Engine Operation:** Fully supports LangChain LLM reasoning when API keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`) are present, and seamlessly falls back to a deterministic heuristic reasoning engine when run offline, in CI/CD, or during automated test suites.

---

## 2. LangGraph Workflow Architecture

The execution pipeline is orchestrated via a stateful `StateGraph`:

```
                    [START]
                       │
                       ▼
                 load_dataset
                       │
                       ▼
                analyze_dataset
                       │
                       ▼
              analyze_data_quality
                       │
                       ▼
          generate_preprocessing_plan
                       │
                       ▼
                approval_gate ◄─────────────────┐
                       │                        │
         ┌─────────────┴─────────────┐          │
         ▼                           ▼          │
    [APPROVED]                  [REJECTED]      │
         │                           │          │
         ▼                           ▼          │
execute_preprocessing         request_changes ──┘
         │
         ▼
feature_engineering
         │
         ▼
 feature_selection
         │
         ▼
dimensionality_reduction
         │
         ▼
 validate_dataset
         │
         ├───────────────────────────┐
         │                           ▼
      [PASSED]                    [FAILED]
         │                           │
         │                           ▼
         │                    analyze_failure
         │                           │
         │                    recoverable?
         │                     ├── YES ──► retry_node ──► execute_preprocessing
         │                     └── NO ───┐
         ▼                               │
  generate_report ◄──────────────────────┘
         │
         ▼
   save_outputs
         │
         ▼
       [END]
```

### Human-in-the-Loop Approval Gate
- **Interactive CLI Prompt:** In `mode: approval`, execution pauses at `approval_gate`, displaying detected target, task type, data quality findings, proposed transformations, and feature budgets. The user approves via terminal input `[Y/n]`.
- **LangGraph Native Interrupt:** Uses `interrupt()` and `MemorySaver` checkpointing, allowing external APIs to pause runs, inspect state via thread IDs, and resume asynchronously.

---

## 3. Strict Data Leakage Prevention

In biomedical machine learning, contamination of validation and test sets by training statistics produces artificially optimistic results. This agent enforces strict isolation:

```
                      RAW DATA
                         │
                         ▼
             Row Cleaning (Deduplication)
                         │
                         ▼
             Stratified Split (70/15/15)
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     TRAIN SET     VALIDATION SET    TEST SET
          │              │              │
          ▼              │              │
   FIT TRANSFORMERS      │              │
   - Imputer (median)    │              │
   - Encoder (one-hot)   │              │
   - Scaler (MinMax)     │              │
   - Feature Selector    │              │
          │              │              │
          ▼              ▼              ▼
      TRANSFORM      TRANSFORM      TRANSFORM
        ONLY           ONLY           ONLY
```

1. **Zero Global Fitting:** Imputers, scalers, encoders, and feature selectors are fitted **strictly on `X_train`**.
2. **Transform Only:** `X_val` and `X_test` are strictly transformed using the frozen parameters learned from `X_train`.
3. **Leakage Verification:** The validation engine explicitly checks for target presence in feature matrices, finite values, and train-test duplicate overlap.

---

## 4. Quantum Compatibility & Feature Budgeting

To prepare tabular biomedical features for downstream **Variational Quantum Classifiers (VQC)**:

- **Target Feature Budget:** Configurable via `target_feature_count: 4` (or 6, 8, null).
- **Quantum Angle Embedding Readiness:** Features are scaled to $[0, 1]$ via `MinMaxScaler`, directly compatible with quantum rotation gates ($R_x(x_i \cdot \pi)$, $R_y$, $R_z$).
- **Non-Linear Selection:** Defaults to **Mutual Information** (`mutual_info_classif`) to capture complex feature-target relationships before quantum state encoding.

---

## 5. Project Directory Structure

```
ai_preprocessing_agent/
│
├── README.md                           # Comprehensive documentation
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variable template
├── .gitignore                          # Git ignore rules
│
├── config/
│   ├── default.yaml                    # Base configuration template
│   └── lung_cancer.yaml                # Lung cancer prototype configuration
│
├── app/
│   ├── __init__.py
│   │
│   ├── agent/                          # LangGraph agent orchestration
│   │   ├── __init__.py
│   │   ├── preprocessing_agent.py      # High-level clean service interface
│   │   ├── graph.py                    # LangGraph workflow definition
│   │   ├── state.py                    # Serializable PreprocessingState TypedDict
│   │   ├── prompts.py                  # LLM system prompts and templates
│   │   └── routing.py                  # Conditional edge routing rules
│   │
│   ├── tools/                          # Deterministic Python tools
│   │   ├── __init__.py
│   │   ├── dataset_loader.py           # Multi-format dataset ingestion
│   │   ├── dataset_analysis.py         # Profiling & candidate target ranking
│   │   ├── quality_analysis.py         # Duplicates, missing, imbalance, leakage
│   │   ├── cleaning.py                 # Deduplication, string cleaning, imputation
│   │   ├── encoding.py                 # One-hot, ordinal, target label encoding
│   │   ├── scaling.py                  # MinMaxScaler, StandardScaler, RobustScaler
│   │   ├── outliers.py                 # IQR retention and clipping
│   │   ├── feature_engineering.py      # Justified composite feature generator
│   │   ├── feature_selection.py        # Mutual info, ANOVA F-test, Random Forest
│   │   ├── dimensionality_reduction.py # Train-fitted PCA projection
│   │   ├── splitting.py                # Stratified train/val/test splitting
│   │   └── validation.py               # Post-processing integrity validation
│   │
│   ├── schemas/                        # Strongly typed Pydantic models
│   │   ├── __init__.py
│   │   ├── dataset.py                  # DatasetAnalysis, ColumnProfile
│   │   ├── quality.py                  # DataQualityReport, QualityFinding
│   │   ├── preprocessing.py            # PreprocessingPlan, TransformationResult
│   │   ├── features.py                 # FeatureSelectionResult, FeatureScore
│   │   ├── validation.py               # ValidationResult, ValidationErrorItem
│   │   └── result.py                   # AgentRunResult, DatasetSplitResult
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── preprocessing_pipeline.py   # Serializable inference pipeline
│   │
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── report_generator.py         # 15-section Markdown & JSON reports
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py                  # Structured run-level logging
│       ├── file_utils.py               # Safe file I/O & YAML/JSON serialization
│       └── reproducibility.py          # Random state seeding & version auditing
│
├── data/
│   ├── input/
│   │   └── lung_cancer.csv             # Primary prototype dataset (3,000 cases)
│   └── output/                         # Generated artifacts (CSVs, JSON, Joblib)
│
├── tests/                              # Pytest test suite (17 passed)
│   ├── conftest.py
│   ├── test_dataset_analysis.py
│   ├── test_quality.py
│   ├── test_cleaning.py
│   ├── test_encoding.py
│   ├── test_scaling.py
│   ├── test_feature_selection.py
│   ├── test_split.py
│   ├── test_validation.py
│   └── test_agent.py
│
├── examples/
│   └── run_agent.py                    # Production CLI runner
│
└── notebooks/
    └── agent_testing.ipynb             # Interactive testing & verification
```

---

## 6. Quick Start & CLI Usage

### Installation
```bash
pip install -r requirements.txt
```

### Running the Lung Cancer Prototype
```bash
python examples/run_agent.py \
    --dataset data/input/lung_cancer.csv \
    --config config/lung_cancer.yaml \
    --mode auto \
    --output-dir data/output
```

### Running in Approval Mode (Human-in-the-Loop)
```bash
python examples/run_agent.py \
    --dataset data/input/lung_cancer.csv \
    --config config/lung_cancer.yaml \
    --mode approval
```

### CLI Overrides
```bash
python examples/run_agent.py \
    --dataset data/input/lung_cancer.csv \
    --target-column LUNG_CANCER \
    --feature-count 4 \
    --mode auto
```

---

## 7. Generated Output Artifacts

Running the agent on a dataset produces the complete suite in `data/output/`:

| Artifact | Type | Description |
| :--- | :--- | :--- |
| `X_train.csv` | CSV | Preprocessed feature matrix for training (70% partition). |
| `X_validation.csv` | CSV | Preprocessed feature matrix for validation (15% partition). |
| `X_test.csv` | CSV | Preprocessed feature matrix for held-out test (15% partition). |
| `y_train.csv` | CSV | Encoded integer target labels (0 = NO, 1 = YES). |
| `y_validation.csv` | CSV | Validation target labels. |
| `y_test.csv` | CSV | Held-out test target labels. |
| `processed_dataset.csv` | CSV | Full combined dataset with selected features and target. |
| `fitted_pipeline.joblib` | Binary | Serialized `PreprocessingPipeline` container for inference. |
| `preprocessing_summary.md` | Markdown | Standardized 15-section human-readable report. |
| `preprocessing_report.json`| JSON | Machine-readable profiling and validation metrics. |
| `preprocessing_config.json`| JSON | Exact configuration parameters used during execution. |
| `feature_selection.json` | JSON | Complete feature ranking scores and selected subsets. |
| `agent_run.json` | JSON | Serialized `AgentRunResult` with run ID and audit trail. |

---

## 8. Python API Integration Contract

Future backend and frontend platforms can interface with the agent without modifying graph internals:

```python
from app.agent.preprocessing_agent import PreprocessingAgent
from app.pipeline.preprocessing_pipeline import PreprocessingPipeline

# 1. Initialize agent with YAML or dictionary configuration
agent = PreprocessingAgent(config_path="config/lung_cancer.yaml")

# 2. Execute full workflow
result = agent.run(
    dataset_path="data/input/lung_cancer.csv",
    mode="auto",
    output_dir="data/output"
)

# 3. Access structured results
print(f"Run ID: {result.run_id}")
print(f"Selected Features: {result.feature_selection.selected_features}")
print(f"Validation Passed: {result.validation.passed}")

# 4. Use serialized pipeline for single-patient inference
pipeline = PreprocessingPipeline.load("data/output/fitted_pipeline.joblib")
transformed_patient_features = pipeline.transform(new_patient_dataframe)
```

---

## 9. Running Tests

Execute the comprehensive unit and integration test suite:

```bash
pytest tests/ -v
```

All 17 tests validate schema extraction, data quality anomaly detection, train-only fitting, feature budgeting, leakage prevention, serialization, and end-to-end LangGraph execution.
