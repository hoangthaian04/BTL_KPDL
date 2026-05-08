import { useState } from "react";

export default function DatasetImportPanel({ onImport, importing, result }) {
  const [selectedFile, setSelectedFile] = useState(null);

  async function handleSubmit() {
    if (!selectedFile || importing) {
      return;
    }
    await onImport(selectedFile);
    setSelectedFile(null);
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Data Ingestion</p>
          <h2>Import New Dataset File</h2>
        </div>
        <button className="primary-button" onClick={handleSubmit} disabled={!selectedFile || importing}>
          {importing ? "Importing..." : "Import file"}
        </button>
      </div>

      <div className="upload-card">
        <label className="field">
          <span>Accepted formats: CSV, XLSX, XLSM</span>
          <input
            type="file"
            accept=".csv,.xlsx,.xlsm"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <p className="upload-note">
          File mới sẽ được nối vào dataset gốc. Nếu trùng `CustomerID`, hệ thống sẽ giữ bản ghi cũ và bỏ bản ghi trùng.
        </p>
      </div>

      {result && (
        <div className="prediction-result">
          <p>Source file: {result.sourceFile}</p>
          <p>Rows before: {result.rowsBefore}</p>
          <p>Incoming rows: {result.incomingRows}</p>
          <p>Imported rows: {result.importedRows}</p>
          <p>Skipped rows: {result.skippedRows}</p>
          <p>Rows after: {result.rowsAfter}</p>
        </div>
      )}
    </section>
  );
}
