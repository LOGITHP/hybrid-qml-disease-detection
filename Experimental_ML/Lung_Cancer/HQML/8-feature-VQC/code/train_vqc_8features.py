"""
Train 8-Qubit Noiseless Variational Quantum Classifier (VQC)
Project: Hybrid QML Platform for Early Disease Detection (Lung Cancer)

Architecture:
- 8 Qubits on default.qubit (Statevector Simulator)
- Data Encoding: Angle Embedding RY(x_i * pi)
- 2 Layers: RY rotations + Linear CNOT ladder
- Total Parameters: 16 quantum angles + 1 classical bias = 17 parameters
- Loss: Binary Cross-Entropy (BCE)
- Optimizer: Adam (stepsize=0.03)
- Batch Size: 64, Epochs: 20
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

import pennylane as qml
from pennylane import numpy as pnp
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)


def parse_args():
    parser = argparse.ArgumentParser(description="Train 8-Qubit Noiseless VQC on Lung Cancer Dataset")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=64, help="Mini-batch size")
    parser.add_argument("--lr", type=float, default=0.03, help="Adam optimizer learning rate")
    parser.add_argument("--layers", type=int, default=2, help="Number of ansatz entangling layers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Setup directory paths relative to script location
    code_dir = Path(__file__).resolve().parent
    exp_dir = code_dir.parent
    data_dir = exp_dir.parent.parent / "data" / "processed"
    
    model_dir = exp_dir / "model"
    metrics_dir = exp_dir / "metrics"
    figures_dir = exp_dir / "figures"
    
    model_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    print("================================================================================")
    print("   TRAINING 8-QUBIT NOISELESS VQC MODEL WITH PENNYLANE")
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
    print("================================================================================\n")
    
    np.random.seed(args.seed)
    pnp.random.seed(args.seed)
    
    # Ingest 8-Feature Datasets
    X_train_path = data_dir / "X_train_8.csv"
    X_val_path = data_dir / "X_validation_8.csv"
    X_test_path = data_dir / "X_test_8.csv"
    
    y_train_path = data_dir / "y_train.csv"
    y_val_path = data_dir / "y_validation.csv"
    y_test_path = data_dir / "y_test.csv"
    
    features_json_path = data_dir / "selected_features_8.json"
    
    if not X_train_path.exists():
        raise FileNotFoundError(f"Missing 8-feature training set at {X_train_path}.")
        
    X_train_df = pd.read_csv(X_train_path)
    X_val_df = pd.read_csv(X_val_path)
    X_test_df = pd.read_csv(X_test_path)
    
    y_train_df = pd.read_csv(y_train_path).squeeze()
    y_val_df = pd.read_csv(y_val_path).squeeze()
    y_test_df = pd.read_csv(y_test_path).squeeze()
    
    with open(features_json_path, "r") as f:
        selected_features = json.load(f)
        
    print(f"Selected 8 Features:          {selected_features}")
    print(f"Training Samples:             {len(X_train_df):,} (8 features)")
    print(f"Validation Samples:           {len(X_val_df):,} (8 features)")
    print(f"Test Samples (Held-out):      {len(X_test_df):,} (8 features)")
    print("--------------------------------------------------------------------------------\n")
    
    X_train = X_train_df.values.astype(float)
    X_val = X_val_df.values.astype(float)
    X_test = X_test_df.values.astype(float)
    
    y_train = y_train_df.values.astype(float)
    y_val = y_val_df.values.astype(float)
    y_test = y_test_df.values.astype(float)
    
    n_qubits = 8
    n_layers = args.layers
    
    # 8-Qubit Quantum Device
    dev = qml.device("default.qubit", wires=n_qubits)
    
    @qml.qnode(dev)
    def vqc_8_circuit(x, weights):
        # 1. Feature Map: Angle Embedding RY(x_i * pi)
        for i in range(n_qubits):
            qml.RY(x[..., i] * pnp.pi, wires=i)
            
        # 2. VQC Layers: RY(theta) + Linear CNOT Entanglement
        for l in range(n_layers):
            for i in range(n_qubits):
                qml.RY(weights[l, i], wires=i)
            for i in range(n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])
                
        # 3. Measurement: Pauli-Z expectation on each qubit
        return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]
        
    def forward_probabilities(x, weights, bias):
        res = vqc_8_circuit(x, weights)
        stacked = pnp.stack(res, axis=-1)
        z_mean = pnp.mean(stacked, axis=-1)
        logits = z_mean + bias
        return 1.0 / (1.0 + pnp.exp(-logits))
        
    def loss_fn(weights, bias, x, y):
        probs = forward_probabilities(x, weights, bias)
        probs_clipped = pnp.clip(probs, 1e-7, 1.0 - 1e-7)
        return -pnp.mean(y * pnp.log(probs_clipped) + (1.0 - y) * pnp.log(1.0 - probs_clipped))
        
    # Draw circuit
    sample_x = pnp.array(X_train[0], requires_grad=False)
    sample_w = pnp.zeros((n_layers, n_qubits), requires_grad=False)
    try:
        fig, ax = qml.draw_mpl(vqc_8_circuit)(sample_x, sample_w)
        fig.suptitle("8-Qubit 2-Layer Variational Quantum Circuit (VQC) Architecture", fontsize=12, fontweight="bold")
        plt.savefig(figures_dir / "vqc_8_circuit_diagram.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    except Exception as e:
        print(f"Warning: Could not save circuit diagram image ({e})")
        
    # Initialize Parameters
    init_weights = 0.01 * pnp.random.randn(n_layers, n_qubits, requires_grad=True)
    init_bias = pnp.array(0.0, requires_grad=True)
    
    weights = pnp.copy(init_weights)
    bias = pnp.copy(init_bias)
    
    opt = qml.AdamOptimizer(stepsize=args.lr)
    
    n_train = len(X_train)
    batch_size = args.batch_size
    n_batches = int(np.ceil(n_train / batch_size))
    
    best_val_loss = float("inf")
    best_weights = None
    best_bias = None
    best_epoch = -1
    history_records = []
    
    print(f"Starting Training for {args.epochs} Epochs ({n_batches} batches/epoch)...")
    start_train_time = time.time()
    
    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        
        perm = np.random.permutation(n_train)
        X_train_shuffled = X_train[perm]
        y_train_shuffled = y_train[perm]
        
        batch_losses = []
        for b in range(n_batches):
            b_start = b * batch_size
            b_end = min(b_start + batch_size, n_train)
            
            x_batch = pnp.array(X_train_shuffled[b_start:b_end], requires_grad=False)
            y_batch = pnp.array(y_train_shuffled[b_start:b_end], requires_grad=False)
            
            [weights, bias], b_loss = opt.step_and_cost(
                lambda w, b: loss_fn(w, b, x_batch, y_batch),
                weights,
                bias
            )
            batch_losses.append(float(b_loss))
            
        train_loss = float(np.mean(batch_losses))
        
        X_val_pnp = pnp.array(X_val, requires_grad=False)
        y_val_pnp = pnp.array(y_val, requires_grad=False)
        val_loss = float(loss_fn(weights, bias, X_val_pnp, y_val_pnp))
        
        val_probs = np.array(forward_probabilities(X_val_pnp, weights, bias))
        val_preds = (val_probs >= 0.5).astype(int)
        val_acc = accuracy_score(y_val, val_preds)
        val_bacc = balanced_accuracy_score(y_val, val_preds)
        val_auc = roc_auc_score(y_val, val_probs)
        
        epoch_duration = time.time() - epoch_start
        
        checkpoint_flag = ""
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_weights = pnp.copy(weights)
            best_bias = pnp.copy(bias)
            best_epoch = epoch
            checkpoint_flag = "  <-- [Saved Best Checkpoint]"
            
        print(f"Epoch {epoch:02d}/{args.epochs:02d} | "
              f"Train Loss: {train_loss:.4f} | "
              f"Val Loss: {val_loss:.4f} | "
              f"Val Acc: {val_acc * 100:.2f}% | "
              f"Val BAcc: {val_bacc * 100:.2f}% | "
              f"Val AUC: {val_auc:.4f} | "
              f"Time: {epoch_duration:.1f}s{checkpoint_flag}")
              
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
    history_path = metrics_dir / "training_history_8.csv"
    history_df.to_csv(history_path, index=False)
    print(f"Saved: {history_path}")
    
    # Save model weights & classical bias
    weights_path = model_dir / "vqc_8_weights.npy"
    bias_path = model_dir / "vqc_8_bias.npy"
    np.save(weights_path, np.array(best_weights))
    np.save(bias_path, np.array(best_bias))
    print(f"Saved Model Parameters: {weights_path} and {bias_path}\n")
    
    # Final Evaluation on Holdout Test Set
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
    print(" EVALUATION ON UNTOUCHED HOLDOUT TEST SET (450 Samples) - 8-QUBIT VQC")
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
        "model": "8-Qubit Noiseless Variational Quantum Classifier (VQC)",
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
    
    metrics_path = metrics_dir / "test_metrics_8.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics_summary, f, indent=4)
    print(f"Saved: {metrics_path}")
    
    # Visualizations
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].plot(history_df["Epoch"], history_df["Train_Loss"], marker="o", color="#1f77b4", lw=2, label="Train Loss (BCE)")
    axes[0].plot(history_df["Epoch"], history_df["Val_Loss"], marker="s", color="#ff7f0e", lw=2, label="Val Loss (BCE)")
    axes[0].axvline(best_epoch, color="#2ca02c", linestyle="--", alpha=0.8, label=f"Best Checkpoint (Ep {best_epoch:02d})")
    axes[0].set_title("8-Qubit VQC Training & Validation Loss Progression", fontsize=12)
    axes[0].set_xlabel("Epoch", fontsize=11)
    axes[0].set_ylabel("Binary Cross-Entropy Loss", fontsize=11)
    axes[0].legend(loc="upper right")
    
    axes[1].plot(history_df["Epoch"], history_df["Val_Balanced_Accuracy"], marker="^", color="#2ca02c", lw=2, label="Val Balanced Accuracy")
    axes[1].plot(history_df["Epoch"], history_df["Val_ROC_AUC"], marker="d", color="#9467bd", lw=2, linestyle="--", label="Val ROC-AUC")
    axes[1].axvline(best_epoch, color="#2ca02c", linestyle="--", alpha=0.8, label=f"Best Checkpoint (Ep {best_epoch:02d})")
    axes[1].set_title("8-Qubit VQC Validation Accuracy Progression", fontsize=12)
    axes[1].set_xlabel("Epoch", fontsize=11)
    axes[1].set_ylabel("Accuracy Score", fontsize=11)
    axes[1].legend(loc="lower right")
    
    plt.tight_layout()
    curves_path = figures_dir / "vqc_8_training_curves.png"
    plt.savefig(curves_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Training Curves: {curves_path}")
    
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
    ax.set_title("Holdout Test Confusion Matrix (8-Qubit VQC)", fontsize=12)
    ax.set_xlabel("Predicted Diagnosis", fontsize=11)
    ax.set_ylabel("Ground Truth Diagnosis", fontsize=11)
    plt.tight_layout()
    cm_path = figures_dir / "vqc_8_confusion_matrix.png"
    plt.savefig(cm_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Confusion Matrix: {cm_path}")


if __name__ == "__main__":
    main()
