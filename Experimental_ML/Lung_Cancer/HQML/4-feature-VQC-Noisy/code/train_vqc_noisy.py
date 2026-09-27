"""
================================================================================
HYBRID QUANTUM MACHINE LEARNING PLATFORM FOR EARLY DISEASE DETECTION
Script: Train 4-Qubit Noisy Variational Quantum Classifier (VQC) with PennyLane
Application: Early Lung Cancer Screening (NISQ Realistic Noise Simulation)
================================================================================
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    recall_score,
    precision_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve,
    classification_report
)

import pennylane as qml
from pennylane import numpy as pnp

# Visualization styling
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10


def parse_args():
    parser = argparse.ArgumentParser(description="Train 4-Qubit Noisy VQC with PennyLane")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=64, help="Mini-batch size")
    parser.add_argument("--lr", type=float, default=0.03, help="Learning rate for Adam optimizer")
    parser.add_argument("--layers", type=int, default=2, help="Number of variational ansatz layers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--p_gate", type=float, default=0.005, help="1-qubit depolarizing error probability")
    parser.add_argument("--p_cnot", type=float, default=0.020, help="2-qubit CNOT depolarizing error probability")
    parser.add_argument("--p_meas", type=float, default=0.015, help="Bit-flip readout error probability")
    return parser.parse_args()


def main():
    args = parse_args()

    current_dir = Path(__file__).resolve().parent
    exp_dir = current_dir.parent
    data_dir = exp_dir.parent.parent / "data" / "processed"

    model_dir = exp_dir / "model"
    metrics_dir = exp_dir / "metrics"
    figures_dir = exp_dir / "figures"

    model_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("================================================================================")
    print("   TRAINING 4-QUBIT NOISY NISQ VQC MODEL WITH PENNYLANE")
    print("   Project: Hybrid QML Platform for Early Disease Detection")
    print("================================================================================")
    print(f"Data Directory:               {data_dir}")
    print(f"Model Directory:              {model_dir}")
    print(f"Metrics Directory:            {metrics_dir}")
    print(f"Figures Directory:            {figures_dir}")
    print(f"Random Seed:                  {args.seed}")
    print(f"Epochs:                       {args.epochs}")
    print(f"Batch Size:                   {args.batch_size}")
    print(f"Learning Rate:                {args.lr}")
    print(f"Ansatz Layers:                {args.layers}")
    print(f"Single-Qubit Depol Error:     {args.p_gate * 100:.1f}%")
    print(f"Two-Qubit CNOT Depol Error:   {args.p_cnot * 100:.1f}%")
    print(f"Readout Bit-Flip Error:       {args.p_meas * 100:.1f}%")
    print("================================================================================\n")

    np.random.seed(args.seed)
    pnp.random.seed(args.seed)

    # Ingest 4-Feature Datasets
    X_train_df = pd.read_csv(data_dir / "X_train_4.csv")
    X_val_df = pd.read_csv(data_dir / "X_validation_4.csv")
    X_test_df = pd.read_csv(data_dir / "X_test_4.csv")

    y_train = pd.read_csv(data_dir / "y_train.csv").squeeze().values.astype(float)
    y_val = pd.read_csv(data_dir / "y_validation.csv").squeeze().values.astype(float)
    y_test = pd.read_csv(data_dir / "y_test.csv").squeeze().values.astype(float)

    with open(data_dir / "selected_features.json", "r") as f:
        selected_features = json.load(f)

    X_train = X_train_df.values.astype(float)
    X_val = X_val_df.values.astype(float)
    X_test = X_test_df.values.astype(float)

    n_qubits = 4
    n_layers = args.layers
    p_gate = args.p_gate
    p_cnot = args.p_cnot
    p_meas = args.p_meas

    # Mixed-state quantum simulator for open quantum systems
    dev = qml.device("default.mixed", wires=n_qubits)

    @qml.qnode(dev)
    def noisy_circuit(x, weights):
        # 1. Angle Encoding
        for i in range(n_qubits):
            qml.RY(x[i] * np.pi, wires=i)

        # 2. Variational Layers with Noise
        for l in range(n_layers):
            for i in range(n_qubits):
                qml.RY(weights[l, i], wires=i)
                qml.DepolarizingChannel(p_gate, wires=i)

            # Linear entangling CNOT chain
            for i in range(n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])
                qml.DepolarizingChannel(p_cnot, wires=i)
                qml.DepolarizingChannel(p_cnot, wires=i + 1)

        # 3. Measurement SPAM Noise
        for i in range(n_qubits):
            qml.BitFlip(p_meas, wires=i)

        return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]

    def predict_sample(x, weights, bias):
        z_vals = noisy_circuit(x, weights)
        z_pooled = pnp.mean(pnp.stack(z_vals))
        return 1.0 / (1.0 + pnp.exp(-(z_pooled + bias)))

    def bce_loss(weights, bias, X_b, y_b):
        eps = 1e-7
        loss = 0.0
        for x, y in zip(X_b, y_b):
            p = predict_sample(x, weights, bias)
            p_clipped = pnp.clip(p, eps, 1.0 - eps)
            loss -= y * pnp.log(p_clipped) + (1.0 - y) * pnp.log(1.0 - p_clipped)
        return loss / len(X_b)

    def evaluate(X_data, y_data, weights, bias):
        preds, probs = [], []
        for x in X_data:
            p = float(predict_sample(x, weights, bias))
            probs.append(p)
            preds.append(1 if p >= 0.5 else 0)
        probs = np.array(probs)
        preds = np.array(preds)
        acc = accuracy_score(y_data, preds)
        bacc = balanced_accuracy_score(y_data, preds)
        sens = recall_score(y_data, preds, zero_division=0)
        spec = recall_score(y_data, preds, pos_label=0, zero_division=0)
        f1 = f1_score(y_data, preds, zero_division=0)
        try:
            auc = roc_auc_score(y_data, probs)
        except Exception:
            auc = 0.5
        return acc, bacc, sens, spec, f1, auc, preds, probs

    # Initialize weights
    weights = pnp.array(0.01 * np.random.randn(n_layers, n_qubits), requires_grad=True)
    bias = pnp.array(0.0, requires_grad=True)

    opt = qml.AdamOptimizer(stepsize=args.lr)
    best_val_loss = float("inf")
    best_weights, best_bias = None, None
    best_epoch = 0

    history_records = []
    print(f"Beginning Noisy VQC Training ({args.epochs} Epochs)...")

    for epoch in range(1, args.epochs + 1):
        perm = np.random.permutation(len(X_train))
        X_shuff = X_train[perm]
        y_shuff = y_train[perm]

        for b in range(0, len(X_train), args.batch_size):
            X_b = pnp.array(X_shuff[b:b + args.batch_size], requires_grad=False)
            y_b = pnp.array(y_shuff[b:b + args.batch_size], requires_grad=False)
            (weights, bias), _ = opt.step_and_cost(lambda w, b: bce_loss(w, b, X_b, y_b), weights, bias)

        val_loss = float(bce_loss(weights, bias, pnp.array(X_val, requires_grad=False), pnp.array(y_val, requires_grad=False)))
        val_acc, val_bacc, _, _, _, val_auc, _, _ = evaluate(X_val, y_val, weights, bias)

        print(f"Epoch {epoch:02d}/{args.epochs:02d} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc*100:.2f}% | Val BAcc: {val_bacc*100:.2f}% | Val AUC: {val_auc:.4f}")

        history_records.append({
            "Epoch": epoch,
            "Val Loss": val_loss,
            "Val Accuracy": val_acc,
            "Val Balanced Acc": val_bacc,
            "Val ROC-AUC": val_auc
        })

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_weights = np.array(weights)
            best_bias = float(bias)
            best_epoch = epoch

    # Save model artifacts
    np.save(model_dir / "vqc_noisy_weights.npy", best_weights)
    np.save(model_dir / "vqc_noisy_bias.npy", np.array([best_bias]))
    pd.DataFrame(history_records).to_csv(metrics_dir / "noisy_training_history.csv", index=False)

    # Evaluate on Holdout Test Set
    test_acc, test_bacc, test_sens, test_spec, test_f1, test_auc, test_preds, test_probs = evaluate(
        X_test, y_test, best_weights, best_bias
    )
    cm = confusion_matrix(y_test, test_preds)

    test_metrics = {
        "model": "4-Qubit Noisy Variational Quantum Classifier (VQC)",
        "framework": f"PennyLane {qml.__version__}",
        "device": "default.mixed (density matrix simulator)",
        "features": selected_features,
        "n_qubits": n_qubits,
        "n_layers": n_layers,
        "noise_model": {
            "single_qubit_depolarizing": p_gate,
            "two_qubit_cnot_depolarizing": p_cnot,
            "readout_bit_flip": p_meas
        },
        "test_samples": len(y_test),
        "best_training_epoch": best_epoch,
        "metrics": {
            "Accuracy": round(float(test_acc), 4),
            "Balanced Accuracy": round(float(test_bacc), 4),
            "Sensitivity": round(float(test_sens), 4),
            "Specificity": round(float(test_spec), 4),
            "Precision": round(float(precision_score(y_test, test_preds, zero_division=0)), 4),
            "F1-Score": round(float(test_f1), 4),
            "ROC-AUC": round(float(test_auc), 4)
        },
        "confusion_matrix": {
            "True Negative": int(cm[0, 0]),
            "False Positive": int(cm[0, 1]),
            "False Negative": int(cm[1, 0]),
            "True Positive": int(cm[1, 1])
        }
    }

    with open(metrics_dir / "noisy_test_metrics.json", "w") as f:
        json.dump(test_metrics, f, indent=4)

    # Save Confusion Matrix Figure
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Pred NO", "Pred YES"], yticklabels=["True NO", "True YES"])
    ax.set_title("4-Qubit Noisy VQC Confusion Matrix (Test Set)")
    plt.tight_layout()
    plt.savefig(figures_dir / "vqc_noisy_confusion_matrix.png", dpi=300)
    plt.close()

    print(f"\nNoisy VQC Training Complete. Checkpoint Epoch: {best_epoch}. Test AUC: {test_auc:.4f}")


if __name__ == "__main__":
    main()
