# 01. Problem Definition: Research Objectives, Clinical Context & Scope

## 1. Problem Background & Clinical Context
Lung cancer is one of the leading causes of cancer-related mortality worldwide. A primary factor contributing to poor prognosis is delayed diagnosis: early-stage lung malignancies are frequently asymptomatic or manifest through common, non-specific respiratory symptoms such as persistent coughing, wheezing, fatigue, and shortness of breath. Consequently, patients often present at advanced stages when curative therapeutic options are significantly diminished.

Standard clinical diagnostics rely heavily on Low-Dose Computed Tomography (LDCT) and histopathological biopsy. However, population-wide radiological screening faces operational bottlenecks, radiation exposure concerns, high false-positive rates for benign nodules, and substantial healthcare costs. Initial risk stratification using patient-reported symptoms, lifestyle indicators, and demographic profiles represents an attractive non-invasive triage tool.

## 2. Research Problem & Hypothesis
The research problem addressed in this repository is:
> **Can parameterized Variational Quantum Classifiers (VQCs) operating on compact qubit registers (4 to 8 qubits) capture complex, non-linear interactions among clinical survey features more effectively or with greater parameter efficiency than standard classical machine learning models?**

We formulate this as a supervised binary classification problem: predicting whether a patient survey record corresponds to a positive lung cancer diagnosis (`LUNG_CANCER = 1`) or a negative non-cancer diagnosis (`LUNG_CANCER = 0`).

## 3. Guiding Research Principles
1. **Prioritizing Sensitivity in Early Screening**:
   In disease screening, missing an actual cancer case (False Negative) carries severe clinical consequences, whereas flagging a patient for secondary radiological confirmation (False Positive) represents an acceptable diagnostic burden. Therefore, model sensitivity (recall on the positive class) is treated as a primary evaluation criterion alongside balanced accuracy and ROC-AUC.
2. **Strict Experimental Integrity**:
   No data leakage between training and testing partitions is permitted. All preprocessing scalers and feature selection rankings must be derived exclusively from training samples.
3. **Rigorous Scientific Objectivity**:
   All reported metrics must originate from actual model executions on an untouched holdout test partition. Quantum models are evaluated critically alongside classical counterparts without premature assertions of "quantum supremacy" or unsupported clinical diagnostic claims.

## 4. Scope and Exclusions
- **Nature of Work**: Academic computational research benchmark and prototype evaluation.
- **Dataset Boundary**: All findings apply strictly to the evaluated **Survey Lung Cancer Dataset** (`V1_dataset.csv`, 2,998 records).
- **Exclusions**: This module does not include hospital-integrated EHR software, web user interfaces, cloud microservices, or regulatory-approved medical device software.
