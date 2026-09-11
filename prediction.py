
# ============================================================
# QUANTUM + SVM DIABETES PREDICTION
# ============================================================

import numpy as np
import pandas as pd
import kagglehub

from kagglehub import KaggleDatasetAdapter

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score
)

import pennylane as qml


# ============================================================
# 1. LOAD DATASET
# ============================================================
import kagglehub
import pandas as pd
import os

# Download dataset
dataset_path = kagglehub.dataset_download(
    "iammustafatz/diabetes-prediction-dataset"
)

print("Dataset downloaded to:")
print(dataset_path)

print("\nFiles:")
print(os.listdir(dataset_path))

# CSV path
csv_path = os.path.join(
    dataset_path,
    "diabetes_prediction_dataset.csv"
)

# Read CSV
df = pd.read_csv(csv_path)

print("\nDataset shape:")
print(df.shape)

print("\nFirst 5 records:")
print(df.head())


# ============================================================
# 2. PREPROCESSING
# ============================================================

print("\n" + "=" * 60)
print("PREPROCESSING")
print("=" * 60)

# Remove duplicates
df = df.drop_duplicates()

# Convert categorical features
df = pd.get_dummies(
    df,
    columns=["gender", "smoking_history"],
    drop_first=True
)

# Features and target
X = df.drop("diabetes", axis=1)
y = df["diabetes"]

# Convert everything to numerical
X = X.astype(float)

print("Features:")
print(X.columns.tolist())


# ============================================================
# 3. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ============================================================
# 4. CLASSICAL PREPROCESSING
# ============================================================

print("\n" + "=" * 60)
print("FEATURE SCALING")
print("=" * 60)

# Standardize features
standard_scaler = StandardScaler()

X_train_scaled = standard_scaler.fit_transform(X_train)
X_test_scaled = standard_scaler.transform(X_test)


# ============================================================
# 5. FEATURE SELECTION
# ============================================================

print("\n" + "=" * 60)
print("FEATURE SELECTION")
print("=" * 60)

# Current quantum prototype uses 4 qubits
n_qubits = 4

selector = SelectKBest(
    score_func=f_classif,
    k=n_qubits
)

X_train_selected = selector.fit_transform(
    X_train_scaled,
    y_train
)

X_test_selected = selector.transform(
    X_test_scaled
)

selected_features = X.columns[
    selector.get_support()
]

print("Selected features:")

for feature in selected_features:
    print(" -", feature)


# ============================================================
# 6. SCALE FEATURES FOR QUANTUM ENCODING
# ============================================================

print("\n" + "=" * 60)
print("QUANTUM ENCODING")
print("=" * 60)

# RY rotations work with angles.
# Map features approximately to [-pi, pi].

quantum_scaler = MinMaxScaler(
    feature_range=(-np.pi, np.pi)
)

X_train_quantum_input = quantum_scaler.fit_transform(
    X_train_selected
)

X_test_quantum_input = quantum_scaler.transform(
    X_test_selected
)

print("Quantum input shape:",
      X_train_quantum_input.shape)


# ============================================================
# 7. CREATE QUANTUM DEVICE
# ============================================================

dev = qml.device(
    "default.qubit",
    wires=n_qubits
)


# ============================================================
# 8. VARIATIONAL QUANTUM CIRCUIT
# ============================================================

@qml.qnode(dev)
def quantum_circuit(x, weights):

    # --------------------------------------------------------
    # Feature Encoding
    # --------------------------------------------------------

    for i in range(n_qubits):

        qml.RY(
            x[i],
            wires=i
        )

    # --------------------------------------------------------
    # Variational Layer
    # --------------------------------------------------------

    for i in range(n_qubits):

        qml.RY(
            weights[i],
            wires=i
        )

    # --------------------------------------------------------
    # Entanglement
    # --------------------------------------------------------

    for i in range(n_qubits - 1):

        qml.CNOT(
            wires=[i, i + 1]
        )

    # --------------------------------------------------------
    # Measurement
    # --------------------------------------------------------

    return [
        qml.expval(
            qml.PauliZ(i)
        )
        for i in range(n_qubits)
    ]


# ============================================================
# 9. INITIALIZE QUANTUM PARAMETERS
# ============================================================

np.random.seed(42)

weights = np.random.uniform(
    -np.pi,
    np.pi,
    n_qubits
)

print("\nInitial quantum parameters:")
print(weights)


# ============================================================
# 10. GENERATE QUANTUM FEATURES
# ============================================================

def quantum_feature_map(X):

    features = []

    for sample in X:

        result = quantum_circuit(
            sample,
            weights
        )

        features.append(result)

    return np.array(features)


print("\nGenerating quantum features...")

X_train_q = quantum_feature_map(
    X_train_quantum_input
)

X_test_q = quantum_feature_map(
    X_test_quantum_input
)

print("\nQuantum feature shape:")
print(X_train_q.shape)

print("\nExample quantum feature vector:")
print(X_train_q[0])


# ============================================================
# 11. SVM CLASSIFIER
# ============================================================

print("\n" + "=" * 60)
print("TRAINING SVM ON QUANTUM FEATURES")
print("=" * 60)

svm = SVC(
    kernel="rbf",
    probability=True,
    random_state=42
)

svm.fit(
    X_train_q,
    y_train
)


# ============================================================
# 12. PREDICTION
# ============================================================

prediction = svm.predict(
    X_test_q
)

probability = svm.predict_proba(
    X_test_q
)[:, 1]


# ============================================================
# 13. EVALUATION
# ============================================================

accuracy = accuracy_score(
    y_test,
    prediction
)

auc = roc_auc_score(
    y_test,
    probability
)

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

print(
    f"\nQuantum + SVM Accuracy: "
    f"{accuracy * 100:.2f}%"
)

print(
    f"Quantum + SVM ROC-AUC: "
    f"{auc:.4f}"
)

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        prediction
    )
)

print("\nConfusion Matrix:")

print(
    confusion_matrix(
        y_test,
        prediction
    )
)


# ============================================================
# 14. TEST ONE PATIENT
# ============================================================

def predict_patient(patient_data):

    """
    patient_data must contain the same features
    used during training.
    """

    # Convert to DataFrame
    patient_df = pd.DataFrame(
        [patient_data]
    )

    # Apply categorical encoding
    patient_df = pd.get_dummies(
        patient_df,
        columns=["gender", "smoking_history"],
        drop_first=True
    )

    # Match training columns
    patient_df = patient_df.reindex(
        columns=X.columns,
        fill_value=0
    )

    patient_df = patient_df.astype(float)

    # Standard scaling
    patient_scaled = standard_scaler.transform(
        patient_df
    )

    # Feature selection
    patient_selected = selector.transform(
        patient_scaled
    )

    # Quantum scaling
    patient_quantum = quantum_scaler.transform(
        patient_selected
    )

    # Quantum circuit
    quantum_features = quantum_feature_map(
        patient_quantum
    )

    # SVM prediction
    pred = svm.predict(
        quantum_features
    )[0]

    prob = svm.predict_proba(
        quantum_features
    )[0][1]

    return pred, prob


print("\n" + "=" * 60)
print("QUANTUM + SVM PIPELINE COMPLETED")
print("=" * 60)