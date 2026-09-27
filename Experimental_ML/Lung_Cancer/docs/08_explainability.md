# 08. Model Explainability & Feature Attribution Framework

## 1. Clinical Imperative for Explainability
In high-stakes medical applications, black-box decision making undermines clinician trust and patient safety. Clinicians require insight into which physiological and lifestyle factors govern algorithmic risk predictions.

## 2. Multi-Tiered Feature Attribution
Because the VQC takes classical tabular inputs, our explainability methodology operates on **classical input feature contributions**:

1. **Mutual Information Attribution**:
   Identifies non-linear associations with lung cancer status:
   - Top Predictors: `COUGHING` ($	ext{MI} = 0.052$), `YELLOW_FINGERS` ($	ext{MI} = 0.048$), `PEER_PRESSURE` ($	ext{MI} = 0.041$), `AGE` ($	ext{MI} = 0.039$).
2. **Sequential Forward Selection Progression**:
   Demonstrates the incremental value of adding individual symptoms to validation balanced accuracy:
   - Step 1 (`COUGHING`): Baseline balanced accuracy 52.1%.
   - Step 2 (`+ PEER_PRESSURE`): Balanced accuracy rose to 53.4%.
   - Step 6 (`+ CHEST_PAIN`): Balanced accuracy peaked at 54.8%.

## 3. Scope & Research Distinction
We explicitly distinguish **input feature explainability** from **quantum circuit interpretability**:
- Our analysis explains *which input clinical factors* drive the model's classifications.
- It does *not* claim to track quantum superposition phases or Hilbert space state tomography during inference.
- Future work will incorporate quantum-specific attribution tools such as Quantum Shapley values.
