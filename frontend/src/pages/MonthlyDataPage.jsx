import React, { useEffect, useState } from "react";
import { fetchMonthlyRecords, updateMonthlyRecord } from "../api";

export default function MonthlyDataPage() {
  const today = new Date();
  const [year, setYear] = useState(String(today.getFullYear()));
  const [month, setMonth] = useState(String(today.getMonth() + 1));
  const [query, setQuery] = useState("");
  const [records, setRecords] = useState([]);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [form, setForm] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const data = await fetchMonthlyRecords(year, month, query);
    setRecords(data.items);
    if (data.items.length > 0) {
      setSelectedRecord(data.items[0]);
      setForm(toForm(data.items[0]));
    } else {
      setSelectedRecord(null);
      setForm(null);
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  async function submitSearch(event) {
    event.preventDefault();
    setError("");
    await load().catch((err) => setError(err.message));
  }

  async function submitUpdate(event) {
    event.preventDefault();
    if (!selectedRecord || !form) return;
    setError("");
    setMessage("");
    try {
      const updated = await updateMonthlyRecord(selectedRecord.id, form);
      setRecords((current) => current.map((record) => (record.id === updated.id ? updated : record)));
      setSelectedRecord(updated);
      setForm(toForm(updated));
      setMessage("월별 데이터를 수정했습니다.");
    } catch (err) {
      setError(err.message);
    }
  }

  function chooseRecord(record) {
    setSelectedRecord(record);
    setForm(toForm(record));
  }

  return (
    <>
      {error ? <div className="state-message error">{error}</div> : null}
      {message ? <div className="state-message success">{message}</div> : null}

      <form className="toolbar-panel wide-toolbar" onSubmit={submitSearch}>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="제품 검색" />
        <input value={year} onChange={(event) => setYear(event.target.value)} placeholder="연도" />
        <input value={month} onChange={(event) => setMonth(event.target.value)} placeholder="월" />
        <button className="primary-button" type="submit">조회</button>
      </form>

      <section className="dual-grid wide-right">
        <div className="panel form-panel">
          <div className="panel-header">
            <div>
              <h2>월별 데이터 목록</h2>
              <p>{year}년 {month}월 기준 업로드 반영 후 세부 값을 보정하는 화면입니다.</p>
            </div>
          </div>
          <div className="list-panel">
            {records.map((record) => (
              <button
                key={record.id}
                type="button"
                className={`list-row ${selectedRecord?.id === record.id ? "active" : ""}`}
                onClick={() => chooseRecord(record)}
              >
                <strong>{record.name}</strong>
                <span>
                  현재고 {record.file_current_stock.toLocaleString()} / 출고 {record.outbound_quantity.toLocaleString()}
                </span>
              </button>
            ))}
          </div>
        </div>

        {form ? (
          <form className="panel form-panel" onSubmit={submitUpdate}>
            <div className="panel-header">
              <div>
                <h2>월별 데이터 수정</h2>
                <p>월별 통계 페이지에서 반영한 뒤, 필요한 숫자만 여기서 세부 수정합니다.</p>
              </div>
            </div>
            <div className="triple-grid">
              <label><span>현재고</span><input type="number" value={form.file_current_stock} onChange={(event) => setForm({ ...form, file_current_stock: Number(event.target.value || 0) })} /></label>
              <label><span>금월 마감재고</span><input type="number" value={form.closing_stock_current_month} onChange={(event) => setForm({ ...form, closing_stock_current_month: Number(event.target.value || 0) })} /></label>
              <label><span>전월 마감재고</span><input type="number" value={form.closing_stock_previous_month} onChange={(event) => setForm({ ...form, closing_stock_previous_month: Number(event.target.value || 0) })} /></label>
              <label><span>마감재고 증감</span><input type="number" value={form.stock_change} onChange={(event) => setForm({ ...form, stock_change: Number(event.target.value || 0) })} /></label>
              <label><span>입고</span><input type="number" value={form.inbound_quantity} onChange={(event) => setForm({ ...form, inbound_quantity: Number(event.target.value || 0) })} /></label>
              <label><span>창고 내 입고</span><input type="number" value={form.warehouse_inbound_quantity} onChange={(event) => setForm({ ...form, warehouse_inbound_quantity: Number(event.target.value || 0) })} /></label>
              <label><span>반품 입고</span><input type="number" value={form.return_inbound_quantity} onChange={(event) => setForm({ ...form, return_inbound_quantity: Number(event.target.value || 0) })} /></label>
              <label><span>출고</span><input type="number" value={form.outbound_quantity} onChange={(event) => setForm({ ...form, outbound_quantity: Number(event.target.value || 0) })} /></label>
              <label><span>반출</span><input type="number" value={form.carryout_quantity} onChange={(event) => setForm({ ...form, carryout_quantity: Number(event.target.value || 0) })} /></label>
              <label><span>회송</span><input type="number" value={form.return_outbound_quantity} onChange={(event) => setForm({ ...form, return_outbound_quantity: Number(event.target.value || 0) })} /></label>
              <label><span>조정 입고</span><input type="number" value={form.adjustment_inbound_quantity} onChange={(event) => setForm({ ...form, adjustment_inbound_quantity: Number(event.target.value || 0) })} /></label>
              <label><span>조정 반출</span><input type="number" value={form.adjustment_outbound_quantity} onChange={(event) => setForm({ ...form, adjustment_outbound_quantity: Number(event.target.value || 0) })} /></label>
              <label><span>증감</span><input type="number" value={form.net_change} onChange={(event) => setForm({ ...form, net_change: Number(event.target.value || 0) })} /></label>
            </div>
            <label>
              <span>비고</span>
              <textarea value={form.note || ""} onChange={(event) => setForm({ ...form, note: event.target.value })} />
            </label>
            <button className="primary-button" type="submit">수정 저장</button>
          </form>
        ) : (
          <section className="empty-state">선택할 월별 데이터가 없습니다.</section>
        )}
      </section>
    </>
  );
}

function toForm(record) {
  return {
    file_current_stock: record.file_current_stock,
    closing_stock_current_month: record.closing_stock_current_month,
    closing_stock_previous_month: record.closing_stock_previous_month,
    stock_change: record.stock_change,
    inbound_quantity: record.inbound_quantity,
    warehouse_inbound_quantity: record.warehouse_inbound_quantity,
    return_inbound_quantity: record.return_inbound_quantity,
    outbound_quantity: record.outbound_quantity,
    carryout_quantity: record.carryout_quantity,
    return_outbound_quantity: record.return_outbound_quantity,
    adjustment_inbound_quantity: record.adjustment_inbound_quantity,
    adjustment_outbound_quantity: record.adjustment_outbound_quantity,
    net_change: record.net_change,
    note: record.note || "",
  };
}
