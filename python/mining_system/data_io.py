from __future__ import annotations

from datetime import datetime
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd

from mining_system.config import ID_COLUMN, TARGET_COLUMN


def ensure_directories(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def excel_column_index(cell_ref: str) -> int:
    letters = "".join(char for char in cell_ref if char.isalpha())
    result = 0
    for char in letters:
        result = result * 26 + (ord(char.upper()) - ord("A") + 1)
    return result - 1


def read_xlsx_without_openpyxl(path: Path) -> pd.DataFrame:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as workbook_zip:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in workbook_zip.namelist():
            root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
            for node in root.findall("a:si", ns):
                fragments = [text_node.text or "" for text_node in node.iterfind(".//a:t", ns)]
                shared_strings.append("".join(fragments))

        worksheet = ET.fromstring(workbook_zip.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        max_col = 0
        for row in worksheet.findall(".//a:sheetData/a:row", ns):
            values: dict[int, str] = {}
            for cell in row.findall("a:c", ns):
                index = excel_column_index(cell.get("r", "A1"))
                raw_value = cell.find("a:v", ns)
                value = raw_value.text if raw_value is not None else ""
                if cell.get("t") == "s" and value:
                    value = shared_strings[int(value)]
                values[index] = value
                max_col = max(max_col, index + 1)
            rows.append([values.get(idx, "") for idx in range(max_col)])

    if not rows:
        raise ValueError(f"Workbook {path} does not contain any rows")

    header = rows[0]
    data_rows = [row + [""] * (len(header) - len(row)) for row in rows[1:]]
    return pd.DataFrame(data_rows, columns=header)


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xlsm"}:
        try:
            return pd.read_excel(path)
        except ImportError:
            return read_xlsx_without_openpyxl(path)
    raise ValueError(f"Unsupported file format: {suffix}")


def append_dataset_rows(base_path: Path, incoming_path: Path) -> dict[str, int | str]:
    base_df = load_dataset(base_path)
    incoming_df = load_dataset(incoming_path)

    incoming_df = incoming_df.reindex(columns=base_df.columns)
    combined_df = pd.concat([base_df, incoming_df], ignore_index=True)

    duplicate_rows = 0
    if ID_COLUMN in combined_df.columns:
        before_dedup = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=[ID_COLUMN], keep="first")
        duplicate_rows = before_dedup - len(combined_df)

    if base_path.suffix.lower() in {".xlsx", ".xlsm"}:
        combined_df.to_excel(base_path, index=False)
    else:
        combined_df.to_csv(base_path, index=False)

    imported_rows = len(combined_df) - len(base_df)
    skipped_rows = len(incoming_df) - imported_rows

    return {
        "dataset_path": str(base_path),
        "rows_before": int(len(base_df)),
        "incoming_rows": int(len(incoming_df)),
        "imported_rows": int(imported_rows),
        "skipped_rows": int(skipped_rows),
        "duplicate_rows_removed": int(duplicate_rows),
        "rows_after": int(len(combined_df)),
    }


def append_prediction_customer(base_path: Path, customer_payload: dict[str, object]) -> dict[str, int | str]:
    base_df = load_dataset(base_path)
    customer_row = {column: "" for column in base_df.columns}

    for field_name, field_value in customer_payload.items():
        if field_name in customer_row:
            customer_row[field_name] = field_value

    if ID_COLUMN in customer_row and not customer_row[ID_COLUMN]:
        customer_row[ID_COLUMN] = f"PREDICTED-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if TARGET_COLUMN in customer_row:
        customer_row[TARGET_COLUMN] = ""

    updated_df = pd.concat([base_df, pd.DataFrame([customer_row])], ignore_index=True)
    if base_path.suffix.lower() in {".xlsx", ".xlsm"}:
        updated_df.to_excel(base_path, index=False)
    else:
        updated_df.to_csv(base_path, index=False)

    return {
        "dataset_path": str(base_path),
        "rows_before": int(len(base_df)),
        "rows_after": int(len(updated_df)),
        "appended_customer_id": str(customer_row.get(ID_COLUMN, "")),
    }


def import_pending_datasets(base_path: Path, incoming_dir: Path, processed_dir: Path) -> list[dict[str, int | str]]:
    ensure_directories(incoming_dir, processed_dir)
    summaries: list[dict[str, int | str]] = []
    supported_suffixes = {".csv", ".xlsx", ".xlsm"}

    for pending_path in sorted(incoming_dir.iterdir()):
        if not pending_path.is_file() or pending_path.suffix.lower() not in supported_suffixes:
            continue

        summary = append_dataset_rows(base_path, pending_path)
        archived_name = f"{pending_path.stem}-{datetime.now().strftime('%Y%m%d%H%M%S')}{pending_path.suffix}"
        shutil.move(str(pending_path), str(processed_dir / archived_name))
        summary["source_file"] = pending_path.name
        summaries.append(summary)

    return summaries
