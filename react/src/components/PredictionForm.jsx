import { useState } from "react";

const defaultCustomer = {
  Gender: "Female",
  "Senior Citizen": "No",
  Partner: "No",
  Dependents: "No",
  "Tenure Months": 6,
  "Phone Service": "Yes",
  "Multiple Lines": "No",
  "Internet Service": "Fiber optic",
  "Online Security": "No",
  "Online Backup": "No",
  "Device Protection": "No",
  "Tech Support": "No",
  "Streaming TV": "No",
  "Streaming Movies": "No",
  Contract: "Month-to-month",
  "Paperless Billing": "Yes",
  "Payment Method": "Electronic check",
  "Monthly Charges": 75,
  "Total Charges": 450
};

export default function PredictionForm({ onPredict, prediction, loading }) {
  const [customer, setCustomer] = useState(defaultCustomer);

  function updateField(field, value) {
    setCustomer((current) => ({ ...current, [field]: value }));
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Prediction</p>
          <h2>Predict One Customer</h2>
        </div>
        <button className="primary-button" onClick={() => onPredict(customer)} disabled={loading}>
          {loading ? "Predicting..." : "Predict churn"}
        </button>
      </div>

      <div className="form-grid">
        {Object.entries(customer).map(([field, value]) => (
          <label key={field} className="field">
            <span>{field}</span>
            <input value={value} onChange={(event) => updateField(field, event.target.value)} />
          </label>
        ))}
      </div>

      {prediction && (
        <div className="prediction-result">
          <p>Model: {prediction.model}</p>
          <p>Prediction label: {prediction.prediction}</p>
          <p>Churn probability: {(prediction.churnProbability * 100).toFixed(2)}%</p>
          <p>Predicted at: {prediction.predictedAt}</p>
          <p>Dataset update: customer da duoc them vao dataset goc voi nhan churn de trong.</p>
        </div>
      )}
    </section>
  );
}
