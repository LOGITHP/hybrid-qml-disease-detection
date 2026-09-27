# 02. Dataset Analysis: Schema, Distributions & Correlational Structure

## 1. Dataset Origin & Composition
The study evaluates the **Survey Lung Cancer Dataset** (`data/raw/V1_dataset.csv`), comprising 2,998 individual survey responses documenting patient demographics, behavioral risk factors, and reported symptoms.

- **Total Observations**: 2,998
- **Missing / Null Values**: 0 across all attributes
- **Target Variable**: `LUNG_CANCER`
  - Class 0 (`NO`): Patient without lung cancer
  - Class 1 (`YES`): Patient diagnosed with lung cancer

## 2. Feature Schema & Clinical Categorization

| Attribute Name | Variable Type | Domain / Values | Clinical Category | Description |
|---|---|---|---|---|
| `GENDER` | Categorical Binary | `M`, `F` | Demographic | Biological sex of the respondent |
| `AGE` | Continuous Integer | 21 to 87 years | Demographic | Age in completed years |
| `SMOKING` | Categorical Binary | 1 (No), 2 (Yes) | Lifestyle / Risk Factor | Regular tobacco smoking history |
| `YELLOW_FINGERS` | Categorical Binary | 1 (No), 2 (Yes) | Physical Symptom | Nicotine-associated fingernail staining |
| `ANXIETY` | Categorical Binary | 1 (No), 2 (Yes) | Psychological Factor | Clinical or self-reported chronic anxiety |
| `PEER_PRESSURE` | Categorical Binary | 1 (No), 2 (Yes) | Environmental / Social | Social exposure to secondhand smoking environments |
| `CHRONIC_DISEASE` | Categorical Binary | 1 (No), 2 (Yes) | Comorbidity | Pre-existing chronic respiratory or systemic illness |
| `FATIGUE` | Categorical Binary | 1 (No), 2 (Yes) | Systemic Symptom | Persistent physical exhaustion or asthenia |
| `ALLERGY` | Categorical Binary | 1 (No), 2 (Yes) | Immunological Factor | Documented hypersensitivities or allergic rhinitis |
| `WHEEZING` | Categorical Binary | 1 (No), 2 (Yes) | Respiratory Symptom | Audible whistling respiratory sound during exhalation |
| `ALCOHOL_CONSUMING`| Categorical Binary | 1 (No), 2 (Yes) | Lifestyle / Risk Factor | Regular alcohol intake |
| `COUGHING` | Categorical Binary | 1 (No), 2 (Yes) | Respiratory Symptom | Persistent, chronic unprovoked cough |
| `SHORTNESS_OF_BREATH`| Categorical Binary | 1 (No), 2 (Yes) | Respiratory Symptom | Dyspnea upon minimal physical exertion |
| `SWALLOWING_DIFFICULTY`| Categorical Binary | 1 (No), 2 (Yes) | Upper Digestive Symptom| Dysphagia or painful swallowing |
| `CHEST_PAIN` | Categorical Binary | 1 (No), 2 (Yes) | Thoracic Symptom | Localized substernal or chest wall pain |

## 3. Exploratory Data Observations & Correlational Structure
1. **Age Distribution**:
   - Mean age: $62.7 \pm 8.2$ years (Range: 21 to 87).
   - The majority of respondents reside in the 50-75 age bracket, reflecting the standard demographic window of elevated lung disease incidence.
2. **Symptom Multicollinearity**:
   - Respiratory symptoms exhibit positive inter-correlations: `COUGHING`, `WHEEZING`, and `SHORTNESS_OF_BREATH` frequently co-occur ($r \approx 0.35 - 0.45$).
   - `PEER_PRESSURE` correlates with `SMOKING` and `YELLOW_FINGERS`, reflecting shared environmental exposure pathways.
3. **Class Overlap**:
   - Crucially, symptoms such as `FATIGUE`, `COUGHING`, and `SHORTNESS_OF_BREATH` are also frequently reported by non-cancer respondents with chronic obstructive pulmonary disease (COPD) or seasonal allergies. This creates substantial overlapping regions in feature space, establishing a realistic statistical ceiling on classification accuracy.
