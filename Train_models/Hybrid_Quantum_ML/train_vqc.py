"""
================================================================================
HYBRID QUANTUM MACHINE LEARNING PLATFORM FOR EARLY DISEASE DETECTION
Script: Train 4-Qubit Noiseless Variational Quantum Classifier (VQC) with PennyLane
Application: Early Lung Cancer Screening
================================================================================
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# Core computation & scientific libraries
import numpy as np
import pandas as pd

# Scikit-learn evaluation metrics
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

# Visualization libraries
import matplotlib.pyplot as plt
import seaborn as sns

# PennyLane Quantum Machine Learning framework
import pennylane as qml
from pennylane import numpy as pnp

# Configure visualization styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 150
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.labelsize'] = 11

def parse_args():
    parser = argparse.ArgumentParser(description="Train 4-Qubit Noiseless VQC with PennyLane")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=64, help="Mini-batch size")
    parser.add_argument("--lr", type=float, default=0.03, help="Learning rate for Adam optimizer")
    parser.add_argument("--layers", type=int, default=2, help="Number of variational ansatz layers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # --------------------------------------------------------------------------
    # 1. Directory and Path Configuration
    # --------------------------------------------------------------------------
    base_dir = Path(__file__).resolve().parent.parent.parent
    fs_artifacts_dir = base_dir / "artifacts" / "feature_selection"
    prep_artifacts_dir = base_dir / "artifacts" / "preprocessing"
    
    current_dir = Path(__file__).resolve().parent
    figures_dir = current_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    print("================================================================================")
    print("   TRAINING 4-QUBIT NOISELESS VQC MODEL WITH PENNYLANE")
    print("   Project: Hybrid QML Platform for Early Disease Detection")
    print("================================================================================")
    print(f"Base Directory:               {base_dir}")
    print(f"Model Output Directory:       {current_dir}")
    print(f"Figures Directory:            {figures_dir}")
    print(f"Random Seed:                  {args.seed}")
    print(f"Epochs:                       {args.epochs}")
    print(f"Batch Size:                   {args.batch_size}")
    print(f"Learning Rate:                {args.lr}")
    print(f"Ansatz Layers:                {args.layers}")
    print("================================================================================\n")
    
    # Set random seeds
    np.random.seed(args.seed)
    pnp.random.seed(args.seed)
    
    # --------------------------------------------------------------------------
    # 2. Ingest Selected 4-Feature Datasets
    # --------------------------------------------------------------------------
    X_train_path = fs_artifacts_dir / "X_train_4.csv"
    X_val_path = fs_artifacts_dir / "X_validation_4.csv"
    X_test_path = fs_artifacts_dir / "X_test_4.csv"
    
    y_train_path = prep_artifacts_dir / "y_train.csv"
    y_val_path = prep_artifacts_dir / "y_validation.csv"
    y_test_path = prep_artifacts_dir / "y_test.csv"
    
    features_json_path = fs_artifacts_dir / "selected_features.json"
    
    if not X_train_path.exists():
        raise FileNotFoundError(f"Missing 4-feature training set at {X_train_path}")
        
    X_train_df = pd.read_csv(X_train_path)
    X_val_df = pd.read_csv(X_val_path)
    X_test_df = pd.read_csv(X_test_path)
    
    y_train_df = pd.read_csv(y_train_path).squeeze("columns")
    y_val_df = pd.read_csv(y_val_path).squeeze("columns")
    y_test_df = pd.read_csv(y_test_path).squeeze("columns")
    
    with open(features_json_path, "r") as f:
        selected_features = json.load(f)
        
    print(f"Selected 4 Features:          {selected_features}")
    print(f"Training Samples:             {len(X_train_df):,}")
    print(f"Validation Samples:           {len(X_val_df):,}")
    print(f"Test Samples (Held-out):      {len(X_test_df):,}")
    print(f"Feature Space Bounds:         [{X_train_df.min().min():.2f}, {X_train_df.max().max():.2f}]")
    print("--------------------------------------------------------------------------------\n")
    
    # Convert to numpy arrays
    X_train = X_train_df.values.astype(float)
    X_val = X_val_df.values.astype(float)
    X_test = X_test_df.values.astype(float)
    
    y_train = y_train_df.values.astype(float)
    y_val = y_val_df.values.astype(float)
    y_test = y_test_df.values.astype(float)
    
    # --------------------------------------------------------------------------
    # 3. Define 4-Qubit Quantum Device and VQC Circuit Architecture
    # --------------------------------------------------------------------------
    n_qubits = 4
    n_layers = args.layers
    
    # Noiseless quantum statevector simulator
    dev = qml.device("default.qubit", wires=n_qubits)
    
    @qml.qnode(dev)
    def vqc_quantum_node(x, weights):
        """
        4-Qubit 2-Layer Variational Quantum Classifier (VQC):
        1. Data Encoding: x_j -> RY(x_j * pi) on wire j (feature vector x)
        2. VQC Layer 1 (trainable parameters theta):
           - RY(theta_1), RY(theta_3), RY(theta_5), RY(theta_7) on wires 0, 1, 2, 3
           - CNOT Entanglement (Linear chain): [0->1, 1->2, 2->3]
        3. VQC Layer 2 (trainable parameters theta):
           - RY(theta_2), RY(theta_4), RY(theta_6), RY(theta_8) on wires 0, 1, 2, 3
           - CNOT Entanglement (Linear chain): [0->1, 1->2, 2->3]
        4. Measurement (observable): Pauli-Z expectation across all 4 qubits: <Z_i>
        """
        # Data Encoding (feature vector x)
        for i in range(n_qubits):
            qml.RY(x[..., i] * pnp.pi, wires=i)
            
        # VQC Layer 1: RY(theta_1, theta_3, theta_5, theta_7)
        for i in range(n_qubits):
            qml.RY(weights[0, i], wires=i)
        # CNOT Entanglement (Linear chain)
        for i in range(n_qubits - 1):
            qml.CNOT(wires=[i, i + 1])
            
        # VQC Layer 2: RY(theta_2, theta_4, theta_6, theta_8)
        for i in range(n_qubits):
            qml.RY(weights[1, i], wires=i)
        # CNOT Entanglement (Linear chain)
        for i in range(n_qubits - 1):
            qml.CNOT(wires=[i, i + 1])
            
        # Measurement (observable): Z Expectation across all 4 qubits
        return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]
    
    # --------------------------------------------------------------------------
    # 4. Hybrid Classical-Quantum Forward Model & Loss Function
    # --------------------------------------------------------------------------
    def forward_probabilities(x, weights, bias):
        """
        Computes binary classification probability p(y=1|x):
        sigma(<Z> + bias) where <Z> is the mean Pauli-Z expectation across all 4 qubits.
        """
        res = vqc_quantum_node(x, weights)
        stacked = pnp.stack(res, axis=-1)
        z_mean = pnp.mean(stacked, axis=-1)
        logits = z_mean + bias
        probs = 1.0 / (1.0 + pnp.exp(-logits))
        return probs
    
    def binary_cross_entropy_loss(weights, bias, x, y):
        """
        Numerically stable Binary Cross-Entropy (BCE) loss with epsilon clipping.
        """
        probs = forward_probabilities(x, weights, bias)
        probs_clipped = pnp.clip(probs, 1e-7, 1.0 - 1e-7)
        loss = -pnp.mean(y * pnp.log(probs_clipped) + (1.0 - y) * pnp.log(1.0 - probs_clipped))
        return loss

    # Save Circuit Diagram visualization
    sample_x = pnp.array(X_train[0], requires_grad=False)
    dummy_weights = pnp.zeros((n_layers, n_qubits), requires_grad=False)
    
    fig, ax = qml.draw_mpl(vqc_quantum_node)(sample_x, dummy_weights)
    fig.suptitle("4-Qubit 2-Layer Variational Quantum Circuit (VQC) Architecture", fontsize=12, fontweight="bold")
    circuit_fig_path = figures_dir / "vqc_circuit_diagram.png"
    fig.savefig(circuit_fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Quantum Circuit Diagram: {circuit_fig_path}\n")

    # --------------------------------------------------------------------------
    # 5. Initialize Trainable Variational Parameters & Optimizer
    # --------------------------------------------------------------------------
    weights = pnp.random.uniform(0.0, 2.0 * pnp.pi, (n_layers, n_qubits), requires_grad=True)
    bias = pnp.array(0.0, requires_grad=True)
    
    total_params = weights.size + 1
    print(f"Total Trainable Parameters:   {total_params} ({weights.size} quantum rotation angles [theta_1..theta_8] + 1 classical bias)")
    
    optimizer = qml.AdamOptimizer(stepsize=args.lr)
    
    # --------------------------------------------------------------------------
    # 6. Mini-Batch Training Loop with Validation Checkpointing
    # --------------------------------------------------------------------------
    print("\nStarting Noiseless VQC Training Protocol...")
    print("--------------------------------------------------------------------------------")
    
    best_val_loss = float("inf")
    best_weights = weights.copy()
    best_bias = bias.copy()
    best_epoch = 0
    
    history_records = []
    start_train_time = time.time()
    
    X_val_pnp = pnp.array(X_val, requires_grad=False)
    y_val_pnp = pnp.array(y_val, requires_grad=False)
    
    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        
        # Shuffle training set
        permutation = np.random.permutation(len(X_train))
        X_train_shuffled = X_train[permutation]
        y_train_shuffled = y_train[permutation]
        
        # Mini-batch gradient updates
        batch_losses = []
        for i in range(0, len(X_train), args.batch_size):
            xb = pnp.array(X_train_shuffled[i:i + args.batch_size], requires_grad=False)
            yb = pnp.array(y_train_shuffled[i:i + args.batch_size], requires_grad=False)
            
            (weights, bias), batch_loss = optimizer.step_and_cost(
                lambda w, b: binary_cross_entropy_loss(w, b, xb, yb),
                weights,
                bias
            )
            batch_losses.append(float(batch_loss))
            
        train_loss = float(np.mean(batch_losses))
        
        # Evaluate on entire training set
        train_probs = np.array(forward_probabilities(pnp.array(X_train, requires_grad=False), weights, bias))
        train_preds = (train_probs >= 0.5).astype(int)
        train_acc = accuracy_score(y_train, train_preds)
        train_bacc = balanced_accuracy_score(y_train, train_preds)
        
        # Evaluate on validation set
        val_loss = float(binary_cross_entropy_loss(weights, bias, X_val_pnp, y_val_pnp))
        val_probs = np.array(forward_probabilities(X_val_pnp, weights, bias))
        val_preds = (val_probs >= 0.5).astype(int)
        val_acc = accuracy_score(y_val, val_preds)
        val_bacc = balanced_accuracy_score(y_val, val_preds)
        val_sens = recall_score(y_val, val_preds, zero_division=0)
        val_spec = recall_score(y_val, val_preds, pos_label=0, zero_division=0)
        val_auc = roc_auc_score(y_val, val_probs)
        
        epoch_duration = time.time() - epoch_start
        
        # Model Checkpointing (Best Validation Loss)
        is_best = ""
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_weights = weights.copy()
            best_bias = bias.copy()
            best_epoch = epoch
            is_best = " [*Best Model]"
            
        history_records.append({
            "Epoch": epoch,
            "Train Loss": round(train_loss, 4),
            "Train Accuracy": round(train_acc, 4),
            "Train Balanced Acc": round(train_bacc, 4),
            "Val Loss": round(val_loss, 4),
            "Val Accuracy": round(val_acc, 4),
            "Val Balanced Acc": round(val_bacc, 4),
            "Val Sensitivity": round(val_sens, 4),
            "Val Specificity": round(val_spec, 4),
            "Val ROC-AUC": round(val_auc, 4),
            "Epoch Time (s)": round(epoch_duration, 2)
        })
        
        print(f"Epoch {epoch:02d}/{args.epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
              f"Val Balanced Acc: {val_bacc:.4f} | Val AUC: {val_auc:.4f} ({epoch_duration:.2f}s){is_best}")

    total_training_time = time.time() - start_train_time
    print("--------------------------------------------------------------------------------")
    print(f"Training Completed in {total_training_time:.2f} seconds.")
    print(f"Optimal Checkpoint: Epoch {best_epoch:02d} with Validation Loss: {best_val_loss:.4f}\n")
    
    # Save training history
    history_df = pd.DataFrame(history_records)
    history_df.to_csv(current_dir / "training_history.csv", index=False)
    print(f"Saved: {current_dir / 'training_history.csv'}")
    
    # Save best model parameters
    np.save(current_dir / "vqc_weights.npy", np.array(best_weights))
    np.save(current_dir / "vqc_bias.npy", np.array(best_bias))
    print(f"Saved Model Parameters: {current_dir / 'vqc_weights.npy'} and vqc_bias.npy")

    # --------------------------------------------------------------------------
    # 7. Final Evaluation on Holdout Test Set (X_test_4, y_test)
    # --------------------------------------------------------------------------
    print("\n================================================================================")
    print(" EVALUATION ON UNTOUCHED HOLDOUT TEST SET (450 Samples)")
    print("================================================================================")
    
    X_test_pnp = pnp.array(X_test, requires_grad=False)
    test_probs = np.array(forward_probabilities(X_test_pnp, best_weights, best_bias))
    test_preds = (test_probs >= 0.5).astype(int)
    
    test_acc = float(accuracy_score(y_test, test_preds))
    test_bacc = float(balanced_accuracy_score(y_test, test_preds))
    test_sens = float(recall_score(y_test, test_preds, zero_division=0))
    test_spec = float(recall_score(y_test, test_preds, pos_label=0, zero_division=0))
    test_prec = float(precision_score(y_test, test_preds, zero_division=0))
    test_f1 = float(f1_score(y_test, test_preds, zero_division=0))
    test_auc = float(roc_auc_score(y_test, test_probs))
    
    cm = confusion_matrix(y_test, test_preds)
    
    test_metrics = {
        "model": "4-Qubit Noiseless Variational Quantum Classifier (VQC)",
        "framework": f"PennyLane {qml.__version__}",
        "device": "default.qubit (statevector simulator)",
        "features": selected_features,
        "n_qubits": n_qubits,
        "n_layers": n_layers,
        "test_samples": len(y_test),
        "best_training_epoch": best_epoch,
        "metrics": {
            "Accuracy": round(test_acc, 4),
            "Balanced Accuracy": round(test_bacc, 4),
            "Sensitivity (Recall)": round(test_sens, 4),
            "Specificity": round(test_spec, 4),
            "Precision": round(test_prec, 4),
            "F1-Score": round(test_f1, 4),
            "ROC-AUC": round(test_auc, 4)
        },
        "confusion_matrix": {
            "True Negative": int(cm[0, 0]),
            "False Positive": int(cm[0, 1]),
            "False Negative": int(cm[1, 0]),
            "True Positive": int(cm[1, 1])
        }
    }
    
    with open(current_dir / "test_metrics.json", "w") as f:
        json.dump(test_metrics, f, indent=4)
        
    print(f"Accuracy:                     {test_acc * 100:.2f}%")
    print(f"Balanced Accuracy:            {test_bacc * 100:.2f}%")
    print(f"Sensitivity (Recall):         {test_sens * 100:.2f}%")
    print(f"Specificity:                  {test_spec * 100:.2f}%")
    print(f"Precision:                    {test_prec * 100:.2f}%")
    print(f"F1-Score:                     {test_f1 * 100:.2f}%")
    print(f"ROC-AUC:                      {test_auc:.4f}")
    print("\nConfusion Matrix:")
    print(cm)
    print("\nClassification Report:")
    print(classification_report(y_test, test_preds, target_names=["NO (0)", "YES (1)"]))
    print(f"Saved: {current_dir / 'test_metrics.json'}\n")

    # --------------------------------------------------------------------------
    # 8. Generate Visualizations (Loss, Accuracy, Confusion Matrix, ROC)
    # --------------------------------------------------------------------------
    # 1. Training Curves (Loss & Balanced Accuracy)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    epochs_range = history_df["Epoch"]
    axes[0].plot(epochs_range, history_df["Train Loss"], label="Train Loss", color="#428bca", linewidth=2)
    axes[0].plot(epochs_range, history_df["Val Loss"], label="Val Loss", color="#d9534f", linewidth=2, linestyle="--")
    axes[0].axvline(best_epoch, color="gray", linestyle=":", label=f"Best Checkpoint (Ep {best_epoch})")
    axes[0].set_title("VQC Optimization Loss (Binary Cross-Entropy)", fontsize=12)
    axes[0].set_xlabel("Epoch", fontsize=11)
    axes[0].set_ylabel("Loss", fontsize=11)
    axes[0].legend(loc="upper right")
    
    axes[1].plot(epochs_range, history_df["Train Balanced Acc"], label="Train Balanced Acc", color="#2e7d32", linewidth=2)
    axes[1].plot(epochs_range, history_df["Val Balanced Acc"], label="Val Balanced Acc", color="#e65100", linewidth=2, linestyle="--")
    axes[1].axvline(best_epoch, color="gray", linestyle=":", label=f"Best Checkpoint (Ep {best_epoch})")
    axes[1].set_title("VQC Balanced Accuracy Trajectory", fontsize=12)
    axes[1].set_xlabel("Epoch", fontsize=11)
    axes[1].set_ylabel("Balanced Accuracy", fontsize=11)
    axes[1].legend(loc="lower right")
    
    plt.tight_layout()
    curves_path = figures_dir / "vqc_training_curves.png"
    plt.savefig(curves_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Training Curves: {curves_path}")
    
    # 2. Confusion Matrix Heatmap
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Pred NO", "Pred YES"],
        yticklabels=["True NO", "True YES"],
        cbar=False,
        annot_kws={"size": 13, "weight": "bold"}
    )
    ax.set_title("4-Qubit Noiseless VQC Confusion Matrix (Test Set)", fontsize=12)
    plt.tight_layout()
    cm_path = figures_dir / "vqc_confusion_matrix.png"
    plt.savefig(cm_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Confusion Matrix: {cm_path}")
    
    # 3. ROC Curve
    fpr, tpr, _ = roc_curve(y_test, test_probs)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, color="#2e7d32", linewidth=2.5, label=f"4-Qubit VQC (AUC = {test_auc:.4f})")
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1.5, label="Random Chance (AUC = 0.5000)")
    ax.set_title("Receiver Operating Characteristic (ROC) Curve - Test Set", fontsize=12)
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11)
    ax.legend(loc="lower right")
    plt.tight_layout()
    roc_path = figures_dir / "vqc_roc_curve.png"
    plt.savefig(roc_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved ROC Curve: {roc_path}")

    print("\n================================================================================")
    print(" NOISELESS VQC TRAINING COMPLETE")
    print("================================================================================")

if __name__ == "__main__":
    main()
