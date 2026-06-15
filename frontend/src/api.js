const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "요청 처리에 실패했습니다.");
  }
  return response.json();
}

export async function fetchInventory(params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "" && value !== false) {
      searchParams.set(key, value);
    }
  });
  const query = searchParams.toString();
  return request(`/api/inventory${query ? `?${query}` : ""}`);
}

export async function fetchMonthlyInventory(year, month) {
  return request(`/api/inventory/monthly?year=${year}&month=${month}`);
}

export async function fetchUploads() {
  return request("/api/uploads");
}

export async function previewInventoryUpload({ file, year, month }) {
  const formData = new FormData();
  formData.append("file", file);
  if (year) formData.append("year", year);
  if (month) formData.append("month", month);
  return request("/api/uploads/inventory-preview", {
    method: "POST",
    body: formData,
  });
}

export async function commitInventoryUpload(payload) {
  return request("/api/uploads/inventory-commit", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
