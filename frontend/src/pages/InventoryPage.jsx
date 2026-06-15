import React, { useEffect, useState } from "react";
import { fetchInventorySummary } from "../api";

export default function InventoryPage() {
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        setLoading(true);
        const data = await fetchInventorySummary();
        if (active) setItems(data.items);
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  const shortageCount = items.filter((item) => item.shortage_status !== "정상").length;
  const criticalCount = items.filter((item) => item.shortage_status === "심각 부족").length;
  const filteredItems = items.filter((item) =>
    [item.name, item.product_code, item.legacy_code, item.barcode]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(query.trim().toLowerCase())
  );

  return (
    <>
      <section className="metrics-grid">
        <MetricCard label="전체 제품" value={items.length} />
        <MetricCard label="부족 제품" value={shortageCount} />
        <MetricCard label="심각 부족" value={criticalCount} />
        <MetricCard label="생산주문 필요" value={items.filter((item) => item.production_order_required).length} />
      </section>

      <section className="panel table-panel">
        <div className="panel-header">
          <div>
            <h2>재고현황</h2>
            <p>현재고에서 이번달 남은 예상 출고량을 반영해 선제적으로 부족 품목을 판단합니다.</p>
          </div>
        </div>
        <div className="search-field">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="제품명, 신코드, 구코드, 바코드 검색"
          />
        </div>
        {loading ? <div className="state-message">재고 요약을 불러오는 중입니다.</div> : null}
        {error ? <div className="state-message error">{error}</div> : null}
        {!loading && !error ? (
          <div className="table-scroller">
            <table>
              <thead>
                <tr>
                  <th>제품명</th>
                  <th>현재고</th>
                  <th>이번 달 출고량</th>
                  <th>최근 3개월 월 평균 출고량</th>
                  <th>이번달 남은 출고 예상량</th>
                  <th>예상 출고 반영 후 재고</th>
                  <th>부족 상태</th>
                  <th>생산주문 필요</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={item.product_id}>
                    <td>
                      <div className="cell-title">
                        <strong>{item.name}</strong>
                        <span>
                          {item.product_code ? `신:${item.product_code}` : "신:-"}
                          {" / "}
                          {item.legacy_code ? `구:${item.legacy_code}` : "구:-"}
                        </span>
                      </div>
                    </td>
                    <td className="number">{formatNumber(item.current_stock)}</td>
                    <td className="number">{formatNumber(item.current_month_outbound)}</td>
                    <td className="number">{formatDecimal(item.average_monthly_outbound_last_3_months)}</td>
                    <td className="number">{formatDecimal(item.remaining_expected_outbound_this_month)}</td>
                    <td className={`number ${item.projected_stock_after_expected_outbound < 0 ? "danger" : "positive"}`}>
                      {formatDecimal(item.projected_stock_after_expected_outbound)}
                    </td>
                    <td>
                      <span className={`status-dot ${statusClassName(item.shortage_status)}`}>
                        {item.shortage_status}
                      </span>
                    </td>
                    <td>{item.production_order_required ? "필요" : "정상"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </>
  );
}

function MetricCard({ label, value }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{formatNumber(value)}</strong>
    </article>
  );
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString();
}

function formatDecimal(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function statusClassName(status) {
  if (status === "심각 부족") return "critical";
  if (status === "부족") return "warning";
  return "normal";
}
