from __future__ import annotations

import argparse
import json
from pathlib import Path

from mining_system.config import (
    DASHBOARD_PATH,
    DEFAULT_DATA_PATH,
    HIGH_RISK_PATH,
    METRICS_PATH,
    INCOMING_DATA_DIR,
    PREDICTION_TEMPLATE_PATH,
    PROCESSED_DATA_DIR,
    SUMMARY_PATH,
)
from mining_system.data_io import append_dataset_rows, append_prediction_customer, ensure_directories, import_pending_datasets
from mining_system.prediction import load_prediction_payload, predict_customer
from mining_system.training import train_models


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Telco churn mining system prototype")
    parser.add_argument(
        "--data",
        default=str(DEFAULT_DATA_PATH),
        help="Path to Telco churn dataset (.xlsx or .csv)",
    )

    subparsers = parser.add_subparsers(dest="command")

    train_parser = subparsers.add_parser("train", help="Train models and generate artifacts")
    train_parser.set_defaults(command="train")

    predict_parser = subparsers.add_parser("predict", help="Predict churn for one customer")
    predict_parser.add_argument("--input-json", type=str, help="Path to a customer JSON payload")
    predict_parser.add_argument("--sample-index", type=int, help="Use one row from the dataset as sample input")
    predict_parser.set_defaults(command="predict")

    import_parser = subparsers.add_parser("import-data", help="Append a new CSV/XLSX file into the main dataset")
    import_parser.add_argument("--input-file", required=True, type=str, help="Path to the new dataset file")
    import_parser.set_defaults(command="import-data")

    append_parser = subparsers.add_parser("append-customer", help="Append one predicted customer into the base dataset")
    append_parser.add_argument("--input-json", required=True, type=str, help="Path to a customer JSON payload")
    append_parser.set_defaults(command="append-customer")

    crawl_parser = subparsers.add_parser("crawl-data", help="Auto-import every pending CSV/XLSX file from incoming_data")
    crawl_parser.set_defaults(command="crawl-data")

    report_parser = subparsers.add_parser("report", help="Print artifact paths and best metrics")
    report_parser.set_defaults(command="report")

    return parser


def print_training_summary() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    print("Training completed")
    print(f"Best model: {summary['best_model']}")
    print(f"Dataset rows: {summary['dataset_rows']}")
    print(f"Feature columns: {summary['feature_columns']}")
    print("Top metrics:")
    for metric_name, metric_value in summary["metrics"].items():
        if metric_name != "model":
            if isinstance(metric_value, float):
                print(f"  {metric_name}: {metric_value:.4f}")
            else:
                print(f"  {metric_name}: {metric_value}")
    print(f"Dashboard: {DASHBOARD_PATH}")


def main() -> None:
    ensure_directories(DASHBOARD_PATH.parent)
    parser = build_parser()
    args = parser.parse_args()
    data_path = Path(args.data)
    command = args.command or "train"

    if command == "train":
        train_models(data_path)
        print_training_summary()
        return

    if command == "predict":
        payload = load_prediction_payload(
            input_json=Path(args.input_json) if args.input_json else None,
            sample_index=args.sample_index,
            data_path=data_path,
        )
        print(json.dumps(predict_customer(payload), ensure_ascii=False, indent=2))
        return

    if command == "import-data":
        summary = append_dataset_rows(data_path, Path(args.input_file))
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if command == "append-customer":
        payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
        summary = append_prediction_customer(data_path, payload)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if command == "crawl-data":
        summaries = import_pending_datasets(data_path, INCOMING_DATA_DIR, PROCESSED_DATA_DIR)
        print(json.dumps({"imported_files": summaries, "count": len(summaries)}, ensure_ascii=False, indent=2))
        return

    if command == "report":
        print_training_summary()
        print(f"Metrics file: {METRICS_PATH}")
        print(f"High-risk customers: {HIGH_RISK_PATH}")
        print(f"Prediction template: {PREDICTION_TEMPLATE_PATH}")
        return

    parser.print_help()
