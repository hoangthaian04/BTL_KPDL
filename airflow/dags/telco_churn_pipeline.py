from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_APP = REPO_ROOT / "python" / "app.py"
DATASET_PATH = REPO_ROOT / "Telco_customer_churn.xlsx"
PYTHON_DIR = REPO_ROOT / "python"
INCOMING_DATA_DIR = PYTHON_DIR / "incoming_data"
PROCESSED_DATA_DIR = INCOMING_DATA_DIR / "processed"
ARTIFACTS_DIR = REPO_ROOT / "python" / "artifacts"
CHARTS_DIR = ARTIFACTS_DIR / "charts"
SUMMARY_PATH = ARTIFACTS_DIR / "training_summary.json"
METRICS_PATH = ARTIFACTS_DIR / "metrics.csv"
HIGH_RISK_PATH = ARTIFACTS_DIR / "high_risk_customers.csv"
DASHBOARD_PATH = ARTIFACTS_DIR / "dashboard.html"
MODEL_PATH = ARTIFACTS_DIR / "best_model.pkl"
STATE_DIR = REPO_ROOT / "airflow" / "state"
RUNS_DIR = STATE_DIR / "training_runs"
LATEST_RUN_PATH = STATE_DIR / "latest_training_run.json"
DEFAULT_PYTHON = os.getenv("MINING_PYTHON_EXECUTABLE", "python")


def sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_timestamp(file_path: Path) -> str:
    return datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(timespec="seconds")


@dag(
    dag_id="telco_churn_training_pipeline",
    schedule="0 */6 * * *",
    start_date=datetime(2026, 5, 9),
    catchup=False,
    default_args={
        "owner": "btl-kpdl",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["telco", "churn", "training"],
    description="Retrain the Telco churn model when the dataset changes and validate generated artifacts.",
)
def telco_churn_training_pipeline():
    @task
    def ingest_pending_files() -> dict[str, Any]:
        INCOMING_DATA_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

        command = [
            DEFAULT_PYTHON,
            str(PYTHON_APP),
            "--data",
            str(DATASET_PATH),
            "crawl-data",
        ]
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AirflowFailException(
                "Auto-ingest command failed.\n"
                f"Command: {' '.join(command)}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )
        return json.loads(result.stdout or "{}")

    @task
    def inspect_dataset() -> dict[str, Any]:
        if not DATASET_PATH.exists():
            raise AirflowFailException(f"Dataset not found: {DATASET_PATH}")

        return {
            "path": str(DATASET_PATH),
            "sha256": sha256_file(DATASET_PATH),
            "size_bytes": DATASET_PATH.stat().st_size,
            "modified_at": iso_timestamp(DATASET_PATH),
        }

    @task
    def load_previous_state() -> dict[str, Any]:
        if not LATEST_RUN_PATH.exists():
            return {}
        return json.loads(LATEST_RUN_PATH.read_text(encoding="utf-8"))

    @task.branch
    def decide_retrain(dataset_meta: dict[str, Any], previous_state: dict[str, Any]) -> str:
        from airflow.operators.python import get_current_context

        context = get_current_context()
        dag_run = context.get("dag_run")
        dag_conf = dag_run.conf if dag_run and dag_run.conf else {}
        if dag_conf.get("force_retrain"):
            return "run_training"

        previous_hash = previous_state.get("dataset_sha256")
        if previous_hash != dataset_meta["sha256"]:
            return "run_training"

        return "skip_training"

    @task(task_id="run_training")
    def run_training(dataset_meta: dict[str, Any]) -> dict[str, Any]:
        if not PYTHON_APP.exists():
            raise AirflowFailException(f"Python app not found: {PYTHON_APP}")

        command = [
            DEFAULT_PYTHON,
            str(PYTHON_APP),
            "--data",
            dataset_meta["path"],
            "train",
        ]
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AirflowFailException(
                "Training command failed.\n"
                f"Command: {' '.join(command)}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        return {
            "status": "trained",
            "command": command,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    skip_training = EmptyOperator(task_id="skip_training")

    @task(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def validate_artifacts(dataset_meta: dict[str, Any]) -> dict[str, Any]:
        required_files = [
            SUMMARY_PATH,
            METRICS_PATH,
            HIGH_RISK_PATH,
            DASHBOARD_PATH,
            MODEL_PATH,
        ]
        missing = [str(path) for path in required_files if not path.exists()]
        if missing:
            raise AirflowFailException(f"Missing artifacts: {missing}")

        required_chart_names = {
            "churn_distribution.png",
            "model_comparison_f1.png",
            "confusion_matrix.png",
            "feature_importance.png",
        }
        existing_chart_names = {path.name for path in CHARTS_DIR.glob("*.png")}
        missing_charts = sorted(required_chart_names - existing_chart_names)
        if missing_charts:
            raise AirflowFailException(f"Missing charts: {missing_charts}")

        summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        required_summary_fields = {
            "best_model",
            "metrics",
            "dataset_rows",
            "feature_columns",
            "balanced_train_rows",
            "generated_at",
        }
        missing_fields = sorted(required_summary_fields - summary.keys())
        if missing_fields:
            raise AirflowFailException(f"Summary missing fields: {missing_fields}")

        return {
            "dataset_sha256": dataset_meta["sha256"],
            "dataset_modified_at": dataset_meta["modified_at"],
            "dataset_size_bytes": dataset_meta["size_bytes"],
            "best_model": summary["best_model"],
            "generated_at": summary["generated_at"],
            "artifact_files": {
                "summary": str(SUMMARY_PATH),
                "metrics": str(METRICS_PATH),
                "high_risk": str(HIGH_RISK_PATH),
                "dashboard": str(DASHBOARD_PATH),
                "model": str(MODEL_PATH),
            },
            "charts": sorted(existing_chart_names),
        }

    @task(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def persist_run_manifest(validation: dict[str, Any]) -> str:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        RUNS_DIR.mkdir(parents=True, exist_ok=True)

        manifest = {
            "pipeline": "telco_churn_training_pipeline",
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            **validation,
        }
        run_timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        run_manifest_path = RUNS_DIR / f"{run_timestamp}.json"

        LATEST_RUN_PATH.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        run_manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(run_manifest_path)

    ingest_summary = ingest_pending_files()
    dataset_meta = inspect_dataset()
    previous_state = load_previous_state()
    branch = decide_retrain(dataset_meta, previous_state)
    training_result = run_training(dataset_meta)
    validation = validate_artifacts(dataset_meta)
    manifest = persist_run_manifest(validation)

    ingest_summary >> dataset_meta
    branch >> [training_result, skip_training]
    training_result >> validation
    skip_training >> validation
    manifest


dag = telco_churn_training_pipeline()
