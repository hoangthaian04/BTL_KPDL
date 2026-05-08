const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export async function fetchDashboardDetails() {
  const response = await fetch(`${BASE_URL}/dashboard/details`);
  if (!response.ok) {
    throw new Error("Cannot load dashboard details");
  }
  return response.json();
}

export async function triggerTraining() {
  const response = await fetch(`${BASE_URL}/models/train`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Training request failed");
  }
  return response.json();
}

export async function predictCustomer(customer) {
  const response = await fetch(`${BASE_URL}/predictions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ customer }),
  });
  if (!response.ok) {
    throw new Error("Prediction request failed");
  }
  return response.json();
}

export async function importDataset(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/datasets/import`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error("Dataset import failed");
  }
  return response.json();
}
