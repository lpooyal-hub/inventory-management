const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(formatErrorMessage(data));
  }
  return response.json();
}

function formatErrorMessage(data) {
  const detail = data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item?.msg) {
          const location = Array.isArray(item.loc) ? item.loc.slice(1).join(" > ") : "";
          return location ? `${location}: ${item.msg}` : item.msg;
        }
        return JSON.stringify(item);
      })
      .join("\n");
  }

  return "요청 처리에 실패했습니다.";
}

export function fetchProducts() {
  return request("/api/products");
}

export function searchProducts(query) {
  const suffix = query ? `?query=${encodeURIComponent(query)}` : "";
  return request(`/api/products${suffix}`);
}

export function createProduct(payload) {
  return request("/api/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateProduct(productId, payload) {
  return request(`/api/products/${productId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function createStockMovement(payload) {
  return request("/api/stock-movements", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function fetchInventorySummary() {
  return request("/api/inventory/summary");
}

export function fetchMonthlyOutbound(year, month) {
  return request(`/api/reports/monthly-outbound?year=${year}&month=${month}`);
}

export function fetchMonthlyOutboundTrend(year, month, months = 12) {
  return request(`/api/reports/monthly-outbound-trend?year=${year}&month=${month}&months=${months}`);
}

export function fetchShortageReport() {
  return request("/api/reports/shortage");
}

export function previewMonthlyUpload(file, year, month) {
  const formData = new FormData();
  formData.append("file", file);
  return request(`/api/uploads/monthly-preview?year=${year}&month=${month}`, {
    method: "POST",
    body: formData,
  });
}

export function commitMonthlyUpload(payload) {
  return request("/api/uploads/monthly-commit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function fetchMonthlyRecords(year, month, query = "") {
  const suffix = query ? `&query=${encodeURIComponent(query)}` : "";
  return request(`/api/monthly-records?year=${year}&month=${month}${suffix}`);
}

export function resetMonthlyRecords(year, month) {
  return request(`/api/monthly-records?year=${year}&month=${month}`, {
    method: "DELETE",
  });
}

export function updateMonthlyRecord(recordId, payload) {
  return request(`/api/monthly-records/${recordId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
