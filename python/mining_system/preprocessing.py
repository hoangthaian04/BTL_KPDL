from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

from mining_system.config import (
    DROP_COLUMNS,
    ID_COLUMN,
    NUMERIC_COLUMNS,
    SERVICE_COLUMNS,
    TARGET_COLUMN,
)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [column.strip() for column in cleaned.columns]

    for column in cleaned.columns:
        if cleaned[column].dtype == object:
            cleaned[column] = cleaned[column].astype(str).str.strip()
            cleaned[column] = cleaned[column].replace({"": np.nan, "nan": np.nan, "None": np.nan})

    for column in NUMERIC_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned = cleaned.drop(columns=[column for column in DROP_COLUMNS if column in cleaned.columns])
    
    if TARGET_COLUMN in cleaned.columns:
        cleaned = cleaned.dropna(subset=[TARGET_COLUMN])
        
    return cleaned.drop_duplicates()


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()

    if {"Total Charges", "Tenure Months", "Monthly Charges"}.issubset(enriched.columns):
        tenure = enriched["Tenure Months"].replace(0, np.nan)
        enriched["Avg Charges Per Month"] = (enriched["Total Charges"] / tenure).replace(
            [np.inf, -np.inf], np.nan
        )
        enriched["Avg Charges Per Month"] = enriched["Avg Charges Per Month"].fillna(
            enriched["Monthly Charges"]
        )

    available_services = [column for column in SERVICE_COLUMNS if column in enriched.columns]
    if available_services and "Monthly Charges" in enriched.columns:
        enriched["Total Services"] = (enriched[available_services] == "Yes").sum(axis=1)
        enriched["Charge Per Service"] = enriched["Monthly Charges"] / (
            enriched["Total Services"].replace(0, 1)
        )

    if "Contract" in enriched.columns:
        enriched["Is Long Term Contract"] = np.where(
            enriched["Contract"] == "Month-to-month", "No", "Yes"
        )

    if "Tenure Months" in enriched.columns:
        enriched["Is New Customer"] = np.where(enriched["Tenure Months"] < 6, "Yes", "No")

    return enriched


def build_feature_target_sets(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    working = add_engineered_features(clean_dataframe(df))
    target = working[TARGET_COLUMN].map({"No": 0, "Yes": 1})
    if target.isna().any():
        raise ValueError("Target column contains values other than Yes/No")

    features = working.drop(columns=[column for column in [TARGET_COLUMN, ID_COLUMN] if column in working.columns])
    return features, target.astype(int)


def build_preprocessor(features: pd.DataFrame) -> ColumnTransformer:
    numeric_features = features.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = [column for column in features.columns if column not in numeric_features]

    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", MinMaxScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", encoder),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )
