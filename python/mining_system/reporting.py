from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

from mining_system.config import CARE_RISK_EXCEL_PATH, CHARTS_DIR, DASHBOARD_PATH, HIGH_RISK_EXCEL_PATH, HIGH_RISK_PATH, METRICS_PATH, MODEL_PATH, PREDICTION_TEMPLATE_PATH, TARGET_COLUMN


matplotlib.use("Agg")
import matplotlib.pyplot as plt


def extract_feature_importance(
    model: Any, feature_names: list[str], top_n: int = 20
) -> pd.Series:
    if hasattr(model, "feature_importances_"):
        values = model.feature_importances_
    elif hasattr(model, "coef_"):
        values = np.abs(model.coef_[0])
    else:
        return pd.Series(dtype=float)

    return pd.Series(values, index=feature_names).sort_values(ascending=False).head(top_n)


def generate_charts(
    raw_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    best_model_name: str,
    best_model: Any,
    feature_names: list[str],
    y_test: pd.Series,
    best_predictions: np.ndarray,
) -> dict[str, str]:
    chart_paths: dict[str, str] = {}

    churn_counts = raw_df[TARGET_COLUMN].value_counts().reindex(["No", "Yes"]).fillna(0)
    plt.figure(figsize=(6, 4))
    churn_counts.plot(kind="bar", color=["#2a9d8f", "#e76f51"])
    plt.title("Churn Distribution")
    plt.ylabel("Customers")
    plt.xticks(rotation=0)
    churn_path = CHARTS_DIR / "churn_distribution.png"
    plt.tight_layout()
    plt.savefig(churn_path, dpi=150)
    plt.close()
    chart_paths["churn_distribution"] = churn_path.name

    plt.figure(figsize=(8, 4))
    plt.bar(metrics_df["model"], metrics_df["f1"], color="#457b9d")
    plt.title("Model Comparison by F1 Score")
    plt.ylabel("F1 Score")
    plt.xticks(rotation=15)
    comparison_path = CHARTS_DIR / "model_comparison_f1.png"
    plt.tight_layout()
    plt.savefig(comparison_path, dpi=150)
    plt.close()
    chart_paths["model_comparison"] = comparison_path.name

    cm = confusion_matrix(y_test, best_predictions)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["No", "Yes"])
    disp.plot(cmap="Blues", values_format="d")
    plt.title(f"Confusion Matrix - {best_model_name}")
    confusion_path = CHARTS_DIR / "confusion_matrix.png"
    plt.tight_layout()
    plt.savefig(confusion_path, dpi=150)
    plt.close()
    chart_paths["confusion_matrix"] = confusion_path.name

    importance = extract_feature_importance(best_model, feature_names)
    if not importance.empty:
        plt.figure(figsize=(9, 6))
        importance.sort_values().plot(kind="barh", color="#f4a261")
        plt.title(f"Top Feature Importance - {best_model_name}")
        plt.xlabel("Importance")
        importance_path = CHARTS_DIR / "feature_importance.png"
        plt.tight_layout()
        plt.savefig(importance_path, dpi=150)
        plt.close()
        chart_paths["feature_importance"] = importance_path.name

    return chart_paths


def render_dashboard(summary: dict[str, Any], metrics_df: pd.DataFrame, chart_paths: dict[str, str]) -> None:
    metric_rows = "\n".join(
        f"<tr><td>{row['model']}</td><td>{row['accuracy']:.4f}</td><td>{row['precision']:.4f}</td>"
        f"<td>{row['recall']:.4f}</td><td>{row['f1']:.4f}</td><td>{row['roc_auc']:.4f}</td></tr>"
        for _, row in metrics_df.iterrows()
    )
    image_blocks = "\n".join(
        f"<section><h3>{key.replace('_', ' ').title()}</h3><img src='charts/{value}' alt='{key}' /></section>"
        for key, value in chart_paths.items()
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Telco Churn Mining Dashboard</title>
  <style>
    body {{ font-family: "Segoe UI", sans-serif; margin: 0; background: linear-gradient(135deg, #f1faee, #e9f5db); color: #1d3557; }}
    header {{ background: #1d3557; color: white; padding: 24px 32px; }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .card, section {{ background: white; border-radius: 14px; padding: 16px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08); }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08); margin-bottom: 24px; }}
    th, td {{ padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: left; }}
    th {{ background: #457b9d; color: white; }}
    section {{ margin-bottom: 20px; }}
    img {{ width: 100%; max-width: 1000px; display: block; margin: 12px auto 0; border-radius: 10px; }}
  </style>
</head>
<body>
  <header>
    <h1>Telco Customer Churn Mining System</h1>
    <p>Prototype dashboard generated from the Python training pipeline</p>
  </header>
  <main>
    <div class="cards">
      <div class="card"><strong>Dataset Rows</strong><div>{summary['dataset_rows']}</div></div>
      <div class="card"><strong>Feature Columns</strong><div>{summary['feature_columns']}</div></div>
      <div class="card"><strong>Balanced Train Rows</strong><div>{summary['balanced_train_rows']}</div></div>
      <div class="card"><strong>Best Model</strong><div>{summary['best_model']}</div></div>
    </div>
    <section>
      <h2>Model Metrics</h2>
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>Accuracy</th>
            <th>Precision</th>
            <th>Recall</th>
            <th>F1</th>
            <th>ROC-AUC</th>
          </tr>
        </thead>
        <tbody>{metric_rows}</tbody>
      </table>
    </section>
    {image_blocks}
    <section>
      <h3>Artifacts</h3>
      <p>Best model bundle: {Path(MODEL_PATH).name}</p>
      <p>Metrics table: {Path(METRICS_PATH).name}</p>
      <p>High-risk customers: {Path(HIGH_RISK_PATH).name}</p>
      <p>High-risk export: {Path(HIGH_RISK_EXCEL_PATH).name}</p>
      <p>Care-list export: {Path(CARE_RISK_EXCEL_PATH).name}</p>
      <p>Prediction template: {Path(PREDICTION_TEMPLATE_PATH).name}</p>
    </section>
  </main>
</body>
</html>
"""
    DASHBOARD_PATH.write_text(html, encoding="utf-8")
