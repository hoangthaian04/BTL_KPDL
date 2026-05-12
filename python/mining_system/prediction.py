from __future__ import annotations

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mining_system.config import MODEL_PATH
from mining_system.data_io import load_dataset
from mining_system.preprocessing import add_engineered_features, clean_dataframe


def load_trained_bundle() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model artifact not found. Run the train command first.")
    with MODEL_PATH.open("rb") as model_file:
        return pickle.load(model_file)


def predict_customer(customer_payload: dict[str, Any]) -> dict[str, Any]:
    bundle = load_trained_bundle()
    payload_frame = pd.DataFrame([customer_payload])
    
    payload_frame = clean_dataframe(payload_frame)
    payload_frame = add_engineered_features(payload_frame)

    for column in bundle["training_columns"]:
        if column not in payload_frame.columns:
            payload_frame[column] = np.nan
    payload_frame = payload_frame[bundle["training_columns"]]

    processed = np.asarray(bundle["preprocessor"].transform(payload_frame), dtype=float)
    probability = float(bundle["model"].predict_proba(processed)[:, 1][0])
    return {
        "model": bundle["model_name"],
        "prediction": classify_prediction(probability),
        "churn_probability": round(probability, 4),
        "predicted_at": datetime.now().isoformat(timespec="seconds"),
    }


def load_prediction_payload(
    input_json: Path | None, sample_index: int | None, data_path: Path
) -> dict[str, Any]:
    if input_json is not None:
        return json.loads(input_json.read_text(encoding="utf-8"))

    if sample_index is not None:
        df = add_engineered_features(clean_dataframe(load_dataset(data_path)))
        feature_frame = df.drop(columns=[column for column in ["Churn Label", "CustomerID"] if column in df.columns])
        if sample_index < 0 or sample_index >= len(feature_frame):
            raise IndexError(f"sample-index must be between 0 and {len(feature_frame) - 1}")
        return feature_frame.iloc[sample_index].to_dict()

    raise ValueError("Provide either --input-json or --sample-index")


def classify_prediction(probability: float) -> str:
    if probability > 0.5 and probability < 0.8:
        return "Can cham soc"
    if probability >= 0.8:
        return "Churn Yes"
    return "Churn No"
