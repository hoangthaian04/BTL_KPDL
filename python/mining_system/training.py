from __future__ import annotations

import json
import pickle
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from mining_system.config import (
    ARTIFACTS_DIR,
    CARE_RISK_EXCEL_PATH,
    CARE_RISK_PATH,
    CHARTS_DIR,
    HIGH_RISK_PATH,
    HIGH_RISK_EXCEL_PATH,
    ID_COLUMN,
    METRICS_PATH,
    MODEL_PATH,
    PREDICTION_TEMPLATE_PATH,
    SUMMARY_PATH,
    TARGET_COLUMN,
)
from mining_system.data_io import ensure_directories, load_dataset
from mining_system.preprocessing import add_engineered_features, build_feature_target_sets, build_preprocessor, clean_dataframe
from mining_system.reporting import generate_charts, render_dashboard
from mining_system.prediction import classify_prediction


RISK_EXPORT_COLUMNS = [
    ID_COLUMN,
    "Contract",
    "Internet Service",
    "Payment Method",
    "Actual Churn",
    "Predicted Churn",
    "Churn Probability",
]


def simple_smote(
    features: np.ndarray, labels: np.ndarray, random_state: int = 42, k_neighbors: int = 5
) -> tuple[np.ndarray, np.ndarray]:
    classes, counts = np.unique(labels, return_counts=True)
    if len(classes) != 2:
        return features, labels

    minority_label = classes[np.argmin(counts)]
    majority_count = counts.max()
    minority_indices = np.where(labels == minority_label)[0]
    minority_count = len(minority_indices)
    if minority_count < 2 or minority_count == majority_count:
        return features, labels

    from sklearn.neighbors import NearestNeighbors

    generator = np.random.default_rng(random_state)
    k_value = min(k_neighbors, minority_count - 1)
    minority_samples = features[minority_indices]
    nn = NearestNeighbors(n_neighbors=k_value + 1)
    nn.fit(minority_samples)
    neighbor_ids = nn.kneighbors(minority_samples, return_distance=False)[:, 1:]

    synthetic_samples = []
    for _ in range(majority_count - minority_count):
        base_idx = generator.integers(0, minority_count)
        base_sample = minority_samples[base_idx]
        neighbor_sample = minority_samples[generator.choice(neighbor_ids[base_idx])]
        gap = generator.random()
        synthetic_samples.append(base_sample + gap * (neighbor_sample - base_sample))

    synthetic_array = np.asarray(synthetic_samples)
    synthetic_labels = np.full(len(synthetic_array), minority_label)
    return np.vstack([features, synthetic_array]), np.concatenate([labels, synthetic_labels])


def create_prediction_template(raw_df: pd.DataFrame) -> None:
    cleaned = add_engineered_features(clean_dataframe(raw_df))
    feature_frame = cleaned.drop(columns=[column for column in [TARGET_COLUMN, ID_COLUMN] if column in cleaned.columns])
    template: dict[str, Any] = {}

    for column in feature_frame.columns:
        if pd.api.types.is_numeric_dtype(feature_frame[column]):
            template[column] = round(float(feature_frame[column].median()), 2)
        else:
            modes = feature_frame[column].mode(dropna=True)
            template[column] = modes.iloc[0] if not modes.empty else ""

    PREDICTION_TEMPLATE_PATH.write_text(
        json.dumps(template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def export_risk_lists(dataframe: pd.DataFrame, csv_path, excel_path) -> None:
    export_frame = dataframe.reindex(columns=RISK_EXPORT_COLUMNS)
    export_frame.to_csv(csv_path, index=False)
    export_frame.to_excel(excel_path, index=False)


def train_models(data_path) -> dict[str, Any]:
    ensure_directories(ARTIFACTS_DIR, CHARTS_DIR)
    raw_df = load_dataset(data_path)
    features, target = build_feature_target_sets(raw_df)

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        stratify=target,
        random_state=42,
    )

    preprocessor = build_preprocessor(features)
    X_train_processed = np.asarray(preprocessor.fit_transform(X_train), dtype=float)
    X_test_processed = np.asarray(preprocessor.transform(X_test), dtype=float)
    train_class_counts_before = y_train.value_counts().to_dict()
    X_train_balanced, y_train_balanced = simple_smote(X_train_processed, y_train.to_numpy(dtype=int))
    train_class_counts_after = pd.Series(y_train_balanced).value_counts().to_dict()
    feature_names = preprocessor.get_feature_names_out().tolist()

    candidate_models = {
        "Logistic Regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=42
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=8, min_samples_leaf=10, class_weight="balanced", random_state=42
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=4,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=1,
        ),
    }

    evaluation_rows: list[dict[str, Any]] = []
    trained_models: dict[str, Any] = {}
    test_probabilities: dict[str, np.ndarray] = {}
    test_predictions: dict[str, np.ndarray] = {}

    for model_name, model in candidate_models.items():
        model.fit(X_train_balanced, y_train_balanced)
        probabilities = model.predict_proba(X_test_processed)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        metrics = {
            "model": model_name,
            "accuracy": accuracy_score(y_test, predictions),
            "precision": precision_score(y_test, predictions, zero_division=0),
            "recall": recall_score(y_test, predictions, zero_division=0),
            "f1": f1_score(y_test, predictions, zero_division=0),
            "roc_auc": roc_auc_score(y_test, probabilities),
        }
        evaluation_rows.append(metrics)
        trained_models[model_name] = model
        test_probabilities[model_name] = probabilities
        test_predictions[model_name] = predictions

    metrics_df = pd.DataFrame(evaluation_rows).sort_values(
        by=["f1", "recall", "roc_auc"], ascending=False
    )
    metrics_df.to_csv(METRICS_PATH, index=False)

    best_model_name = metrics_df.iloc[0]["model"]
    best_model = trained_models[best_model_name]
    best_predictions = test_predictions[best_model_name]
    best_probabilities = test_probabilities[best_model_name]

    bundle = {
        "model_name": best_model_name,
        "model": best_model,
        "preprocessor": preprocessor,
        "feature_names": feature_names,
        "training_columns": features.columns.tolist(),
        "train_timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    with MODEL_PATH.open("wb") as model_file:
        pickle.dump(bundle, model_file)

    scored_customers = X_test.copy()
    if ID_COLUMN in raw_df.columns:
        scored_customers[ID_COLUMN] = raw_df.loc[X_test.index, ID_COLUMN]
    scored_customers["Actual Churn"] = y_test.values
    scored_customers["Predicted Churn"] = best_predictions
    scored_customers["Churn Probability"] = best_probabilities
    scored_customers = scored_customers.sort_values("Churn Probability", ascending=False).head(50)

    high_risk_customers = scored_customers[scored_customers["Churn Probability"] >= 0.8].copy()
    care_customers = scored_customers[
        (scored_customers["Churn Probability"] > 0.5) & (scored_customers["Churn Probability"] < 0.8)
    ].copy()

    export_risk_lists(high_risk_customers, HIGH_RISK_PATH, HIGH_RISK_EXCEL_PATH)
    export_risk_lists(care_customers, CARE_RISK_PATH, CARE_RISK_EXCEL_PATH)

    full_probabilities = best_model.predict_proba(np.asarray(preprocessor.transform(features), dtype=float))[:, 1]

    summary = {
        "dataset_rows": int(len(raw_df)),
        "dataset_columns": int(len(raw_df.columns)),
        "feature_rows": int(len(features)),
        "feature_columns": int(len(features.columns)),
        "train_rows_before_smote": int(X_train_processed.shape[0]),
        "balanced_train_rows": int(X_train_balanced.shape[0]),
        "smote_summary": {
            "before": {
                "churn_no": int(train_class_counts_before.get(0, 0)),
                "churn_yes": int(train_class_counts_before.get(1, 0)),
                "total": int(X_train_processed.shape[0]),
            },
            "after": {
                "churn_no": int(train_class_counts_after.get(0, 0)),
                "churn_yes": int(train_class_counts_after.get(1, 0)),
                "total": int(X_train_balanced.shape[0]),
            },
        },
        "target_distribution": {
            "No": int((raw_df[TARGET_COLUMN] == "No").sum()),
            "Yes": int((raw_df[TARGET_COLUMN] == "Yes").sum()),
        },
        "prediction_label_distribution": build_prediction_label_distribution(full_probabilities),
        "best_model": best_model_name,
        "metrics": metrics_df.iloc[0].to_dict(),
        "export_files": {
            "care_csv": str(CARE_RISK_PATH),
            "care_excel": str(CARE_RISK_EXCEL_PATH),
            "high_risk_csv": str(HIGH_RISK_PATH),
            "high_risk_excel": str(HIGH_RISK_EXCEL_PATH),
        },
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    create_prediction_template(raw_df)
    chart_paths = generate_charts(raw_df, metrics_df, best_model_name, best_model, feature_names, y_test, best_predictions)
    render_dashboard(summary, metrics_df, chart_paths)
    return summary
def build_prediction_label_distribution(probabilities: np.ndarray) -> dict[str, int]:
    labels = [classify_prediction(float(probability)) for probability in probabilities]
    return {
        "Churn No": int(sum(label == "Churn No" for label in labels)),
        "Can cham soc": int(sum(label == "Can cham soc" for label in labels)),
        "Churn Yes": int(sum(label == "Churn Yes" for label in labels)),
    }
