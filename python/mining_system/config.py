from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
PYTHON_DIR = ROOT_DIR / "python"
DEFAULT_DATA_PATH = ROOT_DIR / "Telco_customer_churn.xlsx"
ARTIFACTS_DIR = PYTHON_DIR / "artifacts"
CHARTS_DIR = ARTIFACTS_DIR / "charts"
MODEL_PATH = ARTIFACTS_DIR / "best_model.pkl"
METRICS_PATH = ARTIFACTS_DIR / "metrics.csv"
SUMMARY_PATH = ARTIFACTS_DIR / "training_summary.json"
HIGH_RISK_PATH = ARTIFACTS_DIR / "high_risk_customers.csv"
CARE_RISK_PATH = ARTIFACTS_DIR / "care_customers.csv"
HIGH_RISK_EXCEL_PATH = ARTIFACTS_DIR / "high_risk_customers.xlsx"
CARE_RISK_EXCEL_PATH = ARTIFACTS_DIR / "care_customers.xlsx"
PREDICTION_TEMPLATE_PATH = ARTIFACTS_DIR / "sample_customer.json"
DASHBOARD_PATH = ARTIFACTS_DIR / "dashboard.html"
INCOMING_DATA_DIR = PYTHON_DIR / "incoming_data"
PROCESSED_DATA_DIR = INCOMING_DATA_DIR / "processed"

TARGET_COLUMN = "Churn Label"
ID_COLUMN = "CustomerID"
DROP_COLUMNS = [
    "Count",
    "Country",
    "State",
    "City",
    "Zip Code",
    "Lat Long",
    "Latitude",
    "Longitude",
    "Churn Value",
    "Churn Score",
    "Churn Reason",
    "CLTV",
]
SERVICE_COLUMNS = [
    "Phone Service",
    "Multiple Lines",
    "Online Security",
    "Online Backup",
    "Device Protection",
    "Tech Support",
    "Streaming TV",
    "Streaming Movies",
]
NUMERIC_COLUMNS = ["Tenure Months", "Monthly Charges", "Total Charges"]
