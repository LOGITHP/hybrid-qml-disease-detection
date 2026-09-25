"""
================================================================================
HYBRID QUANTUM MACHINE LEARNING PLATFORM FOR EARLY DISEASE DETECTION
Script: Train 6-Qubit Noiseless Variational Quantum Classifier (VQC) with PennyLane
Application: Early Lung Cancer Screening with 6 Selected Clinical Features
================================================================================
"""

import os
os.environ["MPLCONFIGDIR"] = "/tmp"

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
    parser = argparse.ArgumentParser(description="Train 6-Qubit Noiseless VQC with PennyLane")
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
    current_dir = Path(__file__).resolve().parent
    base_dir = current_dir
    while not (base_dir / "artifacts").exists() and base_dir.parent != base_dir:
        base_dir = base_dir.parent
        
    prep_artifacts_dir = base_dir / "artifacts" / "preprocessing"
    vqc_4_dir = base_dir / "Train_models" / "Hybrid_Quantum_ML" / "4-feature_Vqc"
    
    figures_dir = current_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    print("================================================================================")
    print("   TRAINING 6-QUBIT NOISELESS VQC MODEL WITH PENNYLANE")
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
    # 2. Ingest 6-Feature Datasets
    # --------------------------------------------------------------------------
    X_train_path = current_dir / "X_train_6.csv"
    X_val_path = current_dir / "X_validation_6.csv"
    X_test_path = current_dir / "X_test_6.csv"
    
    y_train_path = prep_artifacts_dir / "y_train.csv"
    y_val_path = prep_artifacts_dir / "y_validation.csv"
    y_test_path = prep_artifacts_dir / "y_test.csv"
    
    features_json_path = current_dir / "selected_features_6.json"
    
    if not X_train_path.exists():
        raise FileNotFoundError(f"Missing 6-feature training set at {X_train_path}. Run feature selection first.")
        
    X_train_df = pd.read_csv(X_train_path)
    X_val_df = pd.read_csv(X_val_path)
    X_test_df = pd.read_csv(X_test_path)
    
    y_train_df = pd.read_csv(y_train_path).squeeze()
    y_val_df = pd.read_csv(y_val_path).squeeze()
    y_test_df = pd.read_csv(y_test_path).squeeze()
    
    with open(features_json_path, "r") as f:
        selected_features = json.load(f)
        
    print(f"Selected 6 Features:          {selected_features}")
    print(f"Training Samples:             {len(X_train_df):,} (6 features)")
    print(f"Validation Samples:           {len(X_val_df):,} (6 features)")
    print(f"Test Samples (Held-out):      {len(X_test_df):,} (6 features)")
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
    # 3. Define 6-Qubit Quantum Device and VQC Circuit Architecture
    # --------------------------------------------------------------------------
    n_qubits = 6
    n_layers = args.layers
    
    # Noiseless quantum statevector simulator
    dev = qml.device("default.qubit", wires=n_qubits)
    
    @qml.qnode(dev)
    def vqc_6_quantum_node(x, weights):
        """
        6-Qubit 2-Layer Variational Quantum Classifier (VQC):
        1. Data Encoding: x_j -> RY(x_j * pi) on wire j (feature vector x) for j=0..5
        2. VQC Layer 1 (trainable parameters theta):
           - RY(theta_1..theta_6) on wires 0..5
           - CNOT Entanglement (Linear chain): [0->1, 1->2, 2->3, 3->4, 4->5]
        3. VQC Layer 2 (trainable parameters theta):
           - RY(theta_7..theta_12) on wires 0..5
           - CNOT Entanglement (Linear chain): [0->1, 1->2, 2->3, 3->4, 4->5]
        4. Measurement (observable): Pauli-Z expectation across all 6 qubits: <Z_i>
        """
        # Feature Encoding Layer: RY(x_i * pi)
        for i in range(n_qubits):
            qml.RY(x[..., i] * pnp.pi, wires=i)
            
        # VQC Layer 1: RY(theta_1..theta_6)
        for i in range(n_qubits):
            qml.RY(weights[0, i], wires=i)
        # CNOT Entanglement (Linear chain across 6 qubits)
        for i in range(n_qubits - 1):
            qml.CNOT(wires=[i, i + 1])
            
        # VQC Layer 2: RY(theta_7..theta_12)
        for i in range(n_qubits):
            qml.RY(weights[1, i], wires=i)
        # CNOT Entanglement (Linear chain across 6 qubits)
        for i in range(n_qubits - 1):
            qml.CNOT(wires=[i, i + 1])
            
        # Measurement (observable): Z Expectation across all 6 qubits
        return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]
    
    # --------------------------------------------------------------------------
    # 4. Hybrid Classical-Quantum Forward Model & Loss Function
    # --------------------------------------------------------------------------
    def forward_probabilities(x, weights, bias):
        """
        Computes binary classification probability p(y=1|x):
        sigma(<Z> + bias) where <Z> is the mean Pauli-Z expectation across all 6 qubits.
        """
        res = vqc_6_quantum_node(x, weights)
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
    
    fig, ax = qml.draw_mpl(vqc_6_quantum_node)(sample_x, dummy_weights)
    fig.suptitle("6-Qubit 2-Layer Variational Quantum Circuit (VQC) Architecture", fontsize=12, fontweight="bold")
    circuit_fig_path = figures_dir / "vqc_6_circuit_diagram.png"
    fig.savefig(circuit_fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Quantum Circuit Diagram: {circuit_fig_path}\n")

    # --------------------------------------------------------------------------
    # 5. Initialize Trainable Variational Parameters & Optimizer
    # --------------------------------------------------------------------------
    weights = pnp.random.uniform(0.0, 2.0 * pnp.pi, (n_layers, n_qubits), requires_grad=True)
    bias = pnp.array(0.0, requires_grad=True)
    
    total_params = weights.size + 1
    print(f"Total Trainable Parameters:   {total_params} ({weights.size} quantum rotation angles [theta_1..theta_12] + 1 classical bias)")
    
    optimizer = qml.AdamOptimizer(stepsize=args.lr)
    
    # --------------------------------------------------------------------------
    # 6. Mini-Batch Training Loop with Validation Checkpointing
    # --------------------------------------------------------------------------
    print("\nStarting 6-Qubit Noiseless VQC Training Protocol...")
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
        
        # Evaluate on validation set
        val_loss = float(binary_cross_entropy_loss(weights, bias, X_val_pnp, y_val_pnp))
        val_probs = np.array(forward_probabilities(X_val_pnp, weights, bias))
        val_preds = (val_probs >= 0.5).astype(int)
        val_acc = accuracy_score(y_val, val_preds)
        val_bacc = balanced_accuracy_score(y_val, val_preds)
        val_auc = roc_auc_score(y_val, val_probs)
        
        epoch_duration = time.time() - epoch_start
        
        is_best = False
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_weights = weights.copy()
            best_bias = bias.copy()
            best_epoch = epoch
            is_best = True
            
        star_marker = " [*Best Model]" if is_best else ""
        print(f"Epoch {epoch:02d}/{args.epochs:02d} | "
              f"Train Loss: {train_loss:.4f} | "
              f"Val Loss: {val_loss:.4f} | "
              f"Val Balanced Acc: {val_bacc:.4f} | "
              f"Val AUC: {val_auc:.4f} "
              f"({epoch_duration:.2f}s){star_marker}")
        
        history_records.append({
            "Epoch": epoch,
            "Train_Loss": round(train_loss, 4),
            "Val_Loss": round(val_loss, 4),
            "Val_Accuracy": round(val_acc, 4),
            "Val_Balanced_Accuracy": round(val_bacc, 4),
            "Val_ROC_AUC": round(val_auc, 4),
            "Duration_Seconds": round(epoch_duration, 2)
        })
        
    total_train_duration = time.time() - start_train_time
    print("--------------------------------------------------------------------------------")
    print(f"Training Completed in {total_train_duration:.2f} seconds.")
    print(f"Optimal Checkpoint: Epoch {best_epoch:02d} with Validation Loss: {best_val_loss:.4f}\n")
    
    # Save training progression history
    history_df = pd.DataFrame(history_records)
    history_path = current_dir / "training_history_6.csv"
    history_df.to_csv(history_path, index=False)
    print(f"Saved: {history_path}")
    
    # Save model weights & classical bias
    weights_path = current_dir / "vqc_6_weights.npy"
    bias_path = current_dir / "vqc_6_bias.npy"
    np.save(weights_path, np.array(best_weights))
    np.save(bias_path, np.array(best_bias))
    print(f"Saved Model Parameters: {weights_path} and {bias_path}\n")
    
    # --------------------------------------------------------------------------
    # 7. Final Evaluation on Untouched Holdout Test Set
    # --------------------------------------------------------------------------
    X_test_pnp = pnp.array(X_test, requires_grad=False)
    test_probs = np.array(forward_probabilities(X_test_pnp, best_weights, best_bias))
    test_preds = (test_probs >= 0.5).astype(int)
    
    test_acc = accuracy_score(y_test, test_preds)
    test_bacc = balanced_accuracy_score(y_test, test_preds)
    test_sens = recall_score(y_test, test_preds, pos_label=1)
    test_spec = recall_score(y_test, test_preds, pos_label=0)
    test_prec = precision_score(y_test, test_preds, pos_label=1, zero_division=0)
    test_f1 = f1_score(y_test, test_preds, pos_label=1, zero_division=0)
    test_auc = roc_auc_score(y_test, test_probs)
    cm = confusion_matrix(y_test, test_preds)
    
    print("================================================================================")
    print(" EVALUATION ON UNTOUCHED HOLDOUT TEST SET (450 Samples) - 6-QUBIT VQC")
    print("================================================================================")
    print(f"Accuracy:                     {test_acc * 100:.2f}%")
    print(f"Balanced Accuracy:            {test_bacc * 100:.2f}%")
    print(f"Sensitivity (Recall):         {test_sens * 100:.2f}%")
    print(f"Specificity:                  {test_spec * 100:.2f}%")
    print(f"Precision:                    {test_prec * 100:.2f}%")
    print(f"F1-Score:                     {test_f1 * 100:.2f}%")
    print(f"ROC-AUC:                      {test_auc:.4f}\n")
    print("Confusion Matrix:")
    print(cm)
    print("\nClassification Report:")
    print(classification_report(y_test, test_preds, target_names=["NO (0)", "YES (1)"], digits=4))
    print("================================================================================\n")
    
    # Export metrics JSON
    metrics_summary = {
        "model": "6-Qubit Noiseless Variational Quantum Classifier (VQC)",
        "framework": f"PennyLane {qml.__version__}",
        "device": "default.qubit (statevector simulator)",
        "features": selected_features,
        "n_qubits": n_qubits,
        "n_layers": n_layers,
        "test_samples": len(y_test),
        "best_training_epoch": best_epoch,
        "metrics": {
            "Accuracy": round(float(test_acc), 4),
            "Balanced Accuracy": round(float(test_bacc), 4),
            "Sensitivity (Recall)": round(float(test_sens), 4),
            "Specificity": round(float(test_spec), 4),
            "Precision": round(float(test_prec), 4),
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
    
    metrics_path = current_dir / "test_metrics_6.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics_summary, f, indent=4)
    print(f"Saved: {metrics_path}")
    
    # --------------------------------------------------------------------------
    # 8. Visualizations
    # --------------------------------------------------------------------------
    # 1. Training & Validation Progression Curves
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].plot(history_df["Epoch"], history_df["Train_Loss"], marker="o", color="#1f77b4", lw=2, label="Train Loss (BCE)")
    axes[0].plot(history_df["Epoch"], history_df["Val_Loss"], marker="s", color="#ff7f0e", lw=2, label="Val Loss (BCE)")
    axes[0].axvline(best_epoch, color="#2ca02c", linestyle="--", alpha=0.8, label=f"Best Checkpoint (Ep {best_epoch:02d})")
    axes[0].set_title("6-Qubit VQC Training & Validation Loss Progression", fontsize=12)
    axes[0].set_xlabel("Epoch", fontsize=11)
    axes[0].set_ylabel("Binary Cross-Entropy Loss", fontsize=11)
    axes[0].legend(loc="upper right")
    
    axes[1].plot(history_df["Epoch"], history_df["Val_Balanced_Accuracy"], marker="^", color="#2ca02c", lw=2, label="Val Balanced Accuracy")
    axes[1].plot(history_df["Epoch"], history_df["Val_ROC_AUC"], marker="d", color="#9467bd", lw=2, linestyle="--", label="Val ROC-AUC")
    axes[1].axvline(best_epoch, color="#2ca02c", linestyle="--", alpha=0.8, label=f"Best Checkpoint (Ep {best_epoch:02d})")
    axes[1].set_title("6-Qubit VQC Validation Accuracy Progression", fontsize=12)
    axes[1].set_xlabel("Epoch", fontsize=11)
    axes[1].set_ylabel("Accuracy Score", fontsize=11)
    axes[1].legend(loc="lower right")
    
    plt.tight_layout()
    curves_path = figures_dir / "vqc_6_training_curves.png"
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
        cbar=False,
        xticklabels=["No Cancer (0)", "Cancer (1)"],
        yticklabels=["No Cancer (0)", "Cancer (1)"],
        annot_kws={"size": 13, "weight": "bold"}
    )
    ax.set_title("Holdout Test Confusion Matrix (6-Qubit VQC)", fontsize=12)
    ax.set_xlabel("Predicted Diagnosis", fontsize=11)
    ax.set_ylabel("Ground Truth Diagnosis", fontsize=11)
    plt.tight_layout()
    cm_path = figures_dir / "vqc_6_confusion_matrix.png"
    plt.savefig(cm_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Confusion Matrix: {cm_path}")
    
    # 3. ROC Curve
    fpr, tpr, _ = roc_curve(y_test, test_probs)
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.plot(fpr, tpr, color="#1f77b4", lw=2.5, label=f"6-Qubit VQC (AUC = {test_auc:.4f})")
    ax.plot([0, 1], [0, 1], color="navy", lw=1.5, linestyle="--", label="Chance Baseline (AUC = 0.5000)")
    ax.set_title("Receiver Operating Characteristic (ROC) - 6-Qubit VQC", fontsize=12)
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11)
    ax.legend(loc="lower right")
    plt.tight_layout()
    roc_path = figures_dir / "vqc_6_roc_curve.png"
    plt.savefig(roc_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved ROC Curve: {roc_path}")
    
    # 4. Comparison with 4-Qubit Baseline (if available)
    vqc_4_metrics_path = vqc_4_dir / "test_metrics.json"
    if vqc_4_metrics_path.exists():
        with open(vqc_4_metrics_path, "r") as f:
            vqc_4_data = json.load(f)
        v4_metrics = vqc_4_data["metrics"]
        
        comparison_labels = ["Accuracy", "Balanced Accuracy", "Sensitivity", "Specificity", "Precision", "F1-Score", "ROC-AUC"]
        v4_vals = [v4_metrics.get(k, 0.0) for k in comparison_labels]
        v6_vals = [metrics_summary["metrics"].get(k, 0.0) for k in comparison_labels]
        
        x_indices = np.arange(len(comparison_labels))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(11, 5.5))
        rects1 = ax.bar(x_indices - width/2, [v * 100 if v <= 1.0 else v for v in v4_vals], width, label="4-Qubit VQC (16-D Hilbert Space)", color="#1f77b4", edgecolor="black")
        rects2 = ax.bar(x_indices + width/2, [v * 100 if v <= 1.0 else v for v in v6_vals], width, label="6-Qubit VQC (64-D Hilbert Space)", color="#2ca02c", edgecolor="black")
        
        ax.set_ylabel("Score (%)", fontsize=11)
        ax.set_title("Quantum Scaling Benchmark: 4-Qubit vs. 6-Qubit VQC Architecture", fontsize=13, fontweight="bold")
        ax.set_xticks(x_indices)
        ax.set_xticklabels(comparison_labels, rotation=20, ha="right", fontsize=10)
        ax.legend(loc="lower right")
        ax.set_ylim(0, 100)
        
        for rect in rects1:
            h = rect.get_height()
            ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)
        for rect in rects2:
            h = rect.get_height()
            ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)
            
        plt.tight_layout()
        comp_path = figures_dir / "4_vs_6_feature_comparison.png"
        plt.savefig(comp_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved 4-Qubit vs. 6-Qubit Comparison Plot: {comp_path}")
    
    print("\n================================================================================")
    print(" 6-QUBIT NOISELESS VQC TRAINING COMPLETE")
    print("================================================================================")

if __name__ == "__main__":
    main()
