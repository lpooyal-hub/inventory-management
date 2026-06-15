import React, { startTransition, useDeferredValue, useEffect, useState } from "react";
import { Search } from "lucide-react";
import { fetchInventory } from "../api";

const monthOptions = [
  { label: "전체 최신", value: "" },
  { label: "2026-06", value: "2026-06" },
  { label: "2026-05", value: "2026-05" },
];

export default function InventoryPage() {
  const [inventory, setInventory] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedMonth, setSelectedMonth] = useState("");
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const deferredSearch = useDeferredValue(search);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = {
          search: deferredSearch,
          low_stock_only: lowStockOnly,
        };
        if (selectedMonth) {
          const [year, month] = selectedMonth.split("-");
          params.year = year;
          params.month = month;
        }
        const data = await fetchInventory(params);
        if (active) {
          startTransition(() => setInventory(data.items));
        }
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
  }, [deferredSearch, lowStockOnly, selectedMonth]);

  const metrics = {
    total: inventory.length,
    lowStock: inventory.filter((item) => item.is_low_stock).length,
    inbound: inventory.reduce((sum, item) => sum + item.inbound_quantity, 0),
    outbound: inventory.reduce((sum, item) => sum + item.outbound_quantity, 0),
  };

  return (
    <>
      <section className="metrics-grid">
        <MetricCard label="전체 제품 수" value={metrics.total} />
        <MetricCard label="재고 부족 품목" value={metrics.lowStock} />
        <MetricCard label="총 입고 수량" value={metrics.inbound} />
        <MetricCard label="총 출고 수량" value={metrics.outbound} />
      </section>

      <section className="toolbar-panel">
        <label className="search-field">
          <Search size={16} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="상품명, 상품코드, 바코드 검색"
          />
        </label>
        <select value={selectedMonth} onChange={(event) => setSelectedMonth(event.target.value)}>
          {monthOptions.map((option) => (
            <option key={option.label} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <button
          className={`filter-button ${lowStockOnly ? "active" : ""}`}
          onClick={() => setLowStockOnly((value) => !value)}
          type="button"
        >
          재고 부족만
        </button>
      </section>

      <section className="panel table-panel">
        <div className="panel-header">
          <div>
            <h2>재고 테이블</h2>
            <p>가장 최근 committed batch 기준입니다.</p>
          </div>
        </div>
        {loading ? <StateMessage text="재고 데이터를 불러오는 중입니다." /> : null}
        {error ? <StateMessage text={error} variant="error" /> : null}
        {!loading && !error ? (
          <div className="table-scroller">
            <table>
              <thead>
                <tr>
                  <th>상품코드</th>
                  <th>외부코드</th>
                  <th>상품명</th>
                  <th>현재고</th>
                  <th>금월 마감</th>
                  <th>전월 마감</th>
                  <th>입고</th>
                  <th>출고</th>
                  <th>증감</th>
                  <th>월</th>
                </tr>
              </thead>
              <tbody>
                {inventory.map((item) => (
                  <tr key={`${item.product_id}-${item.snapshot_year}-${item.snapshot_month}`}>
                    <td>{item.product_code || "-"}</td>
                    <td>{item.external_code || "-"}</td>
                    <td>{item.name}</td>
                    <td className={item.is_low_stock ? "number danger" : "number"}>
                      {formatNumber(item.current_stock)}
                    </td>
                    <td className="number">{formatNumber(item.closing_stock_current_month)}</td>
                    <td className="number">{formatNumber(item.closing_stock_previous_month)}</td>
                    <td className="number">{formatNumber(item.inbound_quantity)}</td>
                    <td className="number">{formatNumber(item.outbound_quantity)}</td>
                    <td className={`number ${item.net_change < 0 ? "danger" : "positive"}`}>
                      {formatNumber(item.net_change)}
                    </td>
                    <td>{item.snapshot_year}-{String(item.snapshot_month).padStart(2, "0")}</td>
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

function StateMessage({ text, variant = "neutral" }) {
  return <div className={`state-message ${variant}`}>{text}</div>;
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString();
}
