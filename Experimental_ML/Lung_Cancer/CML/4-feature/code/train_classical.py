"""
Classical Machine Learning Benchmark: 4-Feature Configuration
==============================================================
Evaluates Linear SVM, RBF SVM, and Logistic Regression on the
4-feature lung cancer predictor set: ['WHEEZING', 'YELLOW_FINGERS', 'AGE', 'SHORTNESS_OF_BREATH'].
"""

import os
import sys
import json
import argparse
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, recall_score,
    precision_score, f1_score, roc_auc_score, roc_curve, confusion_matrix
)

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# Relative directory resolution
CODE_DIR = os.path.dirname(os.path.abspath(__file__))
EXP_DIR = os.path.abspath(os.path.join(CODE_DIR, ".."))
DATA_DIR = os.path.abspath(os.path.join(EXP_DIR, "..", "..", "data", "processed"))
MODELS_DIR = os.path.join(EXP_DIR, "models")
FIGURES_DIR = os.path.join(EXP_DIR, "figures")
METRICS_DIR = os.path.join(EXP_DIR, "metrics")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)


def load_data(feature_count=4):
    """Load train, val, test splits for specified feature count."""
    if feature_count == 4:
        X_train = pd.read_csv(os.path.join(DATA_DIR, "X_train_4.csv"))
        X_val = pd.read_csv(os.path.join(DATA_DIR, "X_validation_4.csv"))
        X_test = pd.read_csv(os.path.join(DATA_DIR, "X_test_4.csv"))
    elif feature_count == 6:
        X_train = pd.read_csv(os.path.join(DATA_DIR, "X_train_6.csv"))
        X_val = pd.read_csv(os.path.join(DATA_DIR, "X_validation_6.csv"))
        X_test = pd.read_csv(os.path.join(DATA_DIR, "X_test_6.csv"))
    elif feature_count == 8:
        X_train = pd.read_csv(os.path.join(DATA_DIR, "X_train_8.csv"))
        X_val = pd.read_csv(os.path.join(DATA_DIR, "X_validation_8.csv"))
        X_test = pd.read_csv(os.path.join(DATA_DIR, "X_test_8.csv"))
    else:
        raise ValueError(f"Unsupported feature count: {feature_count}")

    y_train = pd.read_csv(os.path.join(DATA_DIR, "y_train.csv")).values.ravel()
    y_val = pd.read_csv(os.path.join(DATA_DIR, "y_validation.csv")).values.ravel()
    y_test = pd.read_csv(os.path.join(DATA_DIR, "y_test.csv")).values.ravel()

    X_trainval = pd.concat([X_train, X_val], axis=0).reset_index(drop=True)
    y_trainval = np.concatenate([y_train, y_val])

    return X_trainval, X_test, y_trainval, y_test, list(X_train.columns)


def evaluate_predictions(y_true, y_pred, y_prob):
    """Compute standard metrics and confusion matrix."""
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    return {
        "Accuracy": float(accuracy_score(y_true, y_pred)),
        "Balanced Accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "Sensitivity": float(recall_score(y_true, y_pred, zero_division=0)),
        "Specificity": float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,
        "Precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "F1-Score": float(f1_score(y_true, y_pred, zero_division=0)),
        "ROC-AUC": float(roc_auc_score(y_true, y_prob)),
        "Confusion Matrix": {
            "True Negative": int(tn),
            "False Positive": int(fp),
            "False Negative": int(fn),
            "True Positive": int(tp)
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Train classical models for lung cancer screening.")
    parser.add_argument("--features", type=int, default=4, choices=[4, 6, 8], help="Number of input features.")
    args = parser.parse_args()

    print(f"--- Training Classical Models ({args.features} Features) ---")
    X_trainval, X_test, y_trainval, y_test, feature_names = load_data(args.features)
    print(f"Features: {feature_names}")
    print(f"Train+Val samples: {len(X_trainval)}, Holdout Test samples: {len(X_test)}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    models = {
        f"Linear SVM ({args.features} Feats)": {
            "estimator": SVC(kernel="linear", probability=True, random_state=RANDOM_STATE),
            "params": {"C": [0.01, 0.1, 1.0, 10.0], "class_weight": [None, "balanced"]}
        },
        f"RBF SVM ({args.features} Feats)": {
            "estimator": SVC(kernel="rbf", probability=True, random_state=RANDOM_STATE),
            "params": {"C": [0.1, 1.0, 5.0, 10.0], "gamma": ["scale", "auto", 0.1, 0.2], "class_weight": [None, "balanced"]}
        },
        f"Logistic Regression ({args.features} Feats)": {
            "estimator": LogisticRegression(random_state=RANDOM_STATE, max_iter=1000),
            "params": {"C": [0.01, 0.1, 1.0, 10.0], "class_weight": [None, "balanced"]}
        }
    }

    results = []
    for model_name, cfg in models.items():
        print(f"\nTraining {model_name}...")
        grid = GridSearchCV(cfg["estimator"], cfg["params"], cv=cv, scoring="balanced_accuracy", n_jobs=1)
        grid.fit(X_trainval, y_trainval)
        best_est = grid.best_estimator_

        y_pred = best_est.predict(X_test)
        y_prob = best_est.predict_proba(X_test)[:, 1]
        metrics = evaluate_predictions(y_test, y_pred, y_prob)

        print(f"  Best CV Score: {grid.best_score_:.4f}")
        print(f"  Test Accuracy:    {metrics['Accuracy']*100:.2f}%")
        print(f"  Test Sensitivity: {metrics['Sensitivity']*100:.2f}%")
        print(f"  Test Specificity: {metrics['Specificity']*100:.2f}%")
        print(f"  Test F1-Score:    {metrics['F1-Score']*100:.2f}%")
        print(f"  Test ROC-AUC:     {metrics['ROC-AUC']:.4f}")

        clean_name = model_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        joblib.dump(best_est, os.path.join(MODELS_DIR, f"{clean_name}.joblib"))

        results.append({
            "Model Name": model_name,
            "Features Used": feature_names,
            "Best Parameters": grid.best_params_,
            "CV Balanced Accuracy": float(grid.best_score_),
            **metrics
        })

    # Save metrics
    with open(os.path.join(METRICS_DIR, f"results_{args.features}features.json"), "w") as f:
        json.dump(results, f, indent=4)

    # Save Confusion Matrix Figure
    fig, axes = plt.subplots(1, len(models), figsize=(5 * len(models), 4))
    for ax, res in zip(axes, results):
        cm = np.array([
            [res["Confusion Matrix"]["True Negative"], res["Confusion Matrix"]["False Positive"]],
            [res["Confusion Matrix"]["False Negative"], res["Confusion Matrix"]["True Positive"]]
        ])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False)
        ax.set_title(f"{res['Model Name']}\nRec: {res['Sensitivity']*100:.1f}%, Spec: {res['Specificity']*100:.1f}%")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_xticklabels(["No Cancer", "Cancer"])
        ax.set_yticklabels(["No Cancer", "Cancer"])
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, f"confusion_matrices_{args.features}features.png"), dpi=300)
    plt.close()

    print(f"\nCompleted {args.features}-feature benchmark. Artifacts saved.")


if __name__ == "__main__":
    main()
