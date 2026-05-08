import { useEffect, useState } from "react";
import BarChart from "../components/BarChart";
import ChartGallery from "../components/ChartGallery";
import DatasetImportPanel from "../components/DatasetImportPanel";
import HighRiskTable from "../components/HighRiskTable";
import MetricCard from "../components/MetricCard";
import PieChart from "../components/PieChart";
import PredictionForm from "../components/PredictionForm";
import { fetchDashboardDetails, importDataset, predictCustomer, triggerTraining } from "../services/api";

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [training, setTraining] = useState(false);
  const [importing, setImporting] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [importResult, setImportResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadSummary();
  }, []);

  async function loadSummary() {
    try {
      setLoadingSummary(true);
      setError("");
      const data = await fetchDashboardDetails();
      setDashboard(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingSummary(false);
    }
  }

  async function handleTrain() {
    try {
      setTraining(true);
      setError("");
      await triggerTraining();
      await loadSummary();
    } catch (err) {
      setError(err.message);
    } finally {
      setTraining(false);
    }
  }

  async function handlePredict(customer) {
    try {
      setPredicting(true);
      setError("");
      const data = await predictCustomer(customer);
      setPrediction(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setPredicting(false);
    }
  }

  async function handleImport(file) {
    try {
      setImporting(true);
      setError("");
      const data = await importDataset(file);
      setImportResult(data);
      await loadSummary();
    } catch (err) {
      setError(err.message);
    } finally {
      setImporting(false);
    }
  }

  return (
    <main className="dashboard-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Mining System</p>
          <h1>Telco Customer Churn Control Room</h1>
          <p className="hero-copy">
            Dashboard cho BTL: xem mô hình hiện tại, train lại, so sánh các model và dự đoán churn cho khách hàng mới.
          </p>
        </div>
        <button className="primary-button" onClick={handleTrain} disabled={training}>
          {training ? "Training..." : "Retrain model"}
        </button>
      </section>

      {error && <div className="error-banner">{error}</div>}

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Overview</p>
            <h2>Model Summary</h2>
          </div>
        </div>

        {loadingSummary && <p>Loading summary...</p>}

        {dashboard?.summary && (
          <>
            <div className="metric-grid">
              <MetricCard label="Dataset Rows" value={dashboard.summary.datasetRows} accent="#264653" />
              <MetricCard label="Feature Columns" value={dashboard.summary.featureColumns} accent="#2a9d8f" />
              <MetricCard label="Train Rows Before SMOTE" value={dashboard.summary.trainRowsBeforeSmote} accent="#577590" />
              <MetricCard label="Balanced Train Rows" value={dashboard.summary.balancedTrainRows} accent="#e9c46a" />
              <MetricCard label="Best Model" value={dashboard.summary.bestModel} accent="#e76f51" />
              <MetricCard label="F1 Score" value={dashboard.summary.f1?.toFixed?.(4) ?? dashboard.summary.f1} accent="#f4a261" />
              <MetricCard label="ROC-AUC" value={dashboard.summary.rocAuc?.toFixed?.(4) ?? dashboard.summary.rocAuc} accent="#6d597a" />
            </div>

            <div className="performance-grid">
              <div className="summary-block">
                <div className="summary-header">
                  <div>
                    <p className="eyebrow">Performance</p>
                    <h3>Best Model Snapshot</h3>
                  </div>
                  <span className="model-pill">{dashboard.summary.bestModel}</span>
                </div>
                <div className="performance-metrics">
                  <div className="performance-item">
                    <span>Accuracy</span>
                    <strong>{dashboard.summary.accuracy?.toFixed?.(4) ?? dashboard.summary.accuracy}</strong>
                  </div>
                  <div className="performance-item">
                    <span>Precision</span>
                    <strong>{dashboard.summary.precision?.toFixed?.(4) ?? dashboard.summary.precision}</strong>
                  </div>
                  <div className="performance-item">
                    <span>Recall</span>
                    <strong>{dashboard.summary.recall?.toFixed?.(4) ?? dashboard.summary.recall}</strong>
                  </div>
                  <div className="performance-item">
                    <span>F1 Score</span>
                    <strong>{dashboard.summary.f1?.toFixed?.(4) ?? dashboard.summary.f1}</strong>
                  </div>
                  <div className="performance-item performance-item-wide">
                    <span>ROC-AUC</span>
                    <strong>{dashboard.summary.rocAuc?.toFixed?.(4) ?? dashboard.summary.rocAuc}</strong>
                  </div>
                </div>
              </div>

              {dashboard.summary.smoteSummary && (
                <div className="summary-block">
                  <div className="summary-header">
                    <div>
                      <p className="eyebrow">SMOTE</p>
                      <h3>Train Set Before vs After</h3>
                    </div>
                  </div>
                  <div className="smote-grid">
                    <div className="performance-item">
                      <span>Before SMOTE</span>
                      <strong>{dashboard.summary.smoteSummary.before.total}</strong>
                      <p>Churn No: {dashboard.summary.smoteSummary.before.churnNo}</p>
                      <p>Churn Yes: {dashboard.summary.smoteSummary.before.churnYes}</p>
                    </div>
                    <div className="performance-item performance-item-wide">
                      <span>After SMOTE</span>
                      <strong>{dashboard.summary.smoteSummary.after.total}</strong>
                      <p>Churn No: {dashboard.summary.smoteSummary.after.churnNo}</p>
                      <p>Churn Yes: {dashboard.summary.smoteSummary.after.churnYes}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </section>

      <DatasetImportPanel onImport={handleImport} importing={importing} result={importResult} />

      {dashboard?.churnDistribution && (
        <div className="two-column-grid">
          <PieChart
            title="Churn Rate"
            segments={[
              { key: "no", label: "Churn No", value: dashboard.churnDistribution.churnNo, color: "#5fa0e6" },
              { key: "care", label: "Can cham soc", value: dashboard.churnDistribution.care, color: "#f6bd60" },
              { key: "yes", label: "Churn Yes", value: dashboard.churnDistribution.churnYes, color: "#ff6168" }
            ]}
          />
          <BarChart
            title="Model F1 Comparison"
            items={dashboard.modelMetrics || []}
            valueKey="f1"
            labelKey="model"
            color="#457b9d"
            formatter={(value) => value.toFixed(4)}
            maxValue={1}
          />
        </div>
      )}

      {dashboard?.modelMetrics && (
        <div className="two-column-grid">
          <BarChart
            title="Model Recall Comparison"
            items={dashboard.modelMetrics}
            valueKey="recall"
            labelKey="model"
            color="#e76f51"
            formatter={(value) => value.toFixed(4)}
            maxValue={1}
          />
          <BarChart
            title="Model ROC-AUC Comparison"
            items={dashboard.modelMetrics}
            valueKey="rocAuc"
            labelKey="model"
            color="#2a9d8f"
            formatter={(value) => value.toFixed(4)}
            maxValue={1}
          />
        </div>
      )}

      <ChartGallery charts={dashboard?.charts} />
      <div className="two-column-grid">
        <HighRiskTable
          customers={dashboard?.highRiskCustomers}
          eyebrow="Priority"
          title="High-Risk Customers (>= 80%)"
        />
        <HighRiskTable
          customers={dashboard?.careCustomers}
          eyebrow="Care List"
          title="Customers To Watch (50% - <80%)"
        />
      </div>

      <PredictionForm onPredict={handlePredict} prediction={prediction} loading={predicting} />
    </main>
  );
}
