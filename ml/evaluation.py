"""Shared evaluation helpers: classification + ranking checks."""
import numpy as np
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)


def classification_metrics(y_true, y_pred, labels=None) -> dict:
    acc = float(accuracy_score(y_true, y_pred))
    p_macro, r_macro, f_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0)
    p_w, r_w, f_w, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0)
    return {
        "accuracy": round(acc, 4),
        "precision_macro": round(float(p_macro), 4),
        "recall_macro": round(float(r_macro), 4),
        "f1_macro": round(float(f_macro), 4),
        "precision_weighted": round(float(p_w), 4),
        "recall_weighted": round(float(r_w), 4),
        "f1_weighted": round(float(f_w), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "classes": list(labels) if labels is not None else sorted(set(list(y_true) + list(y_pred))),
        "classification_report": classification_report(y_true, y_pred, zero_division=0, output_dict=True),
    }


def constraint_satisfaction_rate(items: list, satisfied: list) -> float:
    if not items:
        return 0.0
    return round(float(sum(satisfied) / len(items)), 4)
