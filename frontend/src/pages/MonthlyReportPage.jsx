import React, { useEffect, useMemo, useState } from "react";
import {
  commitMonthlyUpload,
  fetchMonthlyOutbound,
  fetchMonthlyOutboundTrend,
  fetchMonthlyRecords,
  previewMonthlyUpload,
  resetMonthlyRecords,
} from "../api";

export default function MonthlyReportPage() {
  const today = new Date();
  const [year, setYear] = useState(String(today.getFullYear()));
  const [month, setMonth] = useState(String(today.getMonth() + 1));
  const [file, setFile] = useState(null);
  const [report, setReport] = useState({ items: [] });
  const [trend, setTrend] = useState({ months: [], items: [] });
  const [records, setRecords] = useState([]);
  const [preview, setPreview] = useState(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  async function load(event) {
    if (event) event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const [monthlyData, trendData, recordData] = await Promise.all([
        fetchMonthlyOutbound(year, month),
        fetchMonthlyOutboundTrend(year, month, 12),
        fetchMonthlyRecords(year, month),
      ]);
      setReport(monthlyData);
      setTrend(trendData);
      setRecords(recordData.items);
    } finally {
      setLoading(false);
    }
  }

  async function handlePreview(event) {
    event.preventDefault();
    if (!file) {
      setError("업로드할 xlsx 파일을 선택해주세요.");
      return;
    }
    setUploading(true);
    setError("");
    setMessage("");
    try {
      const data = await previewMonthlyUpload(file, year, month);
      setPreview(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleCommit() {
    if (!preview) return;
    setUploading(true);
    setError("");
    setMessage("");
    try {
      const result = await commitMonthlyUpload({
        file_name: preview.file_name,
        year: Number(preview.year),
        month: Number(preview.month),
        rows: preview.rows,
      });
      setMessage(`월 데이터 ${result.saved_rows}건 반영, 현재고 조정 ${result.adjusted_rows}건 처리했습니다.`);
      await load();
      setPreview(null);
      setFile(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleReset() {
    const confirmed = window.confirm(`${year}년 ${month}월 업로드 데이터와 월 업로드로 생성된 출고/조정 기록을 리셋할까요?`);
    if (!confirmed) return;
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const result = await resetMonthlyRecords(year, month);
      setPreview(null);
      setMessage(`월 데이터 ${result.deleted_records}건, 생성 movement ${result.deleted_movements}건을 삭제했습니다.`);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function updatePreviewRow(index, patch) {
    setPreview((current) => ({
      ...current,
      rows: current.rows.map((row, rowIndex) => {
        if (rowIndex !== index) return row;
        const nextRow = { ...row, ...patch };
        return {
          ...nextRow,
          current_stock_diff: nextRow.file_current_stock - nextRow.system_current_stock,
        };
      }),
    }));
  }

  function bulkSelect(selected) {
    setPreview((current) => ({
      ...current,
      rows: current.rows.map((row) => ({
        ...row,
        selected: row.matched ? selected : false,
      })),
    }));
  }

  function bulkAdjust(applyStockAdjustment) {
    setPreview((current) => ({
      ...current,
      rows: current.rows.map((row) => ({
        ...row,
        apply_stock_adjustment: row.selected && row.matched ? applyStockAdjustment : false,
      })),
    }));
  }

  const filteredReportItems = useMemo(() => {
    const queryText = query.trim().toLowerCase();
    if (!queryText) return report.items;
    return report.items.filter((item) =>
      [item.name, item.product_code, item.legacy_code].filter(Boolean).join(" ").toLowerCase().includes(queryText)
    );
  }, [query, report.items]);

  const filteredTrendItems = useMemo(() => {
    const queryText = query.trim().toLowerCase();
    if (!queryText) return trend.items;
    return trend.items.filter((item) =>
      [item.name, item.product_code, item.legacy_code].filter(Boolean).join(" ").toLowerCase().includes(queryText)
    );
  }, [query, trend.items]);

  const selectedPreviewCount = preview?.rows.filter((row) => row.selected).length ?? 0;
  const selectedAdjustmentCount = preview?.rows.filter((row) => row.apply_stock_adjustment).length ?? 0;
  const diffPreviewCount = preview?.rows.filter((row) => row.existing_record_diff || row.current_stock_diff !== 0).length ?? 0;
  const monthlyTotal = report.items.reduce((sum, item) => sum + Number(item.outbound_quantity || 0), 0);

  function resetPreviewSelection() {
    setPreview(null);
    setFile(null);
  }

  return (
    <>
      {error ? <div className="state-message error">{error}</div> : null}
      {message ? <div className="state-message success">{message}</div> : null}

      <form className="toolbar-panel monthly-toolbar" onSubmit={load}>
        <input value={year} onChange={(event) => setYear(event.target.value)} placeholder="연도" />
        <input value={month} onChange={(event) => setMonth(event.target.value)} placeholder="월" />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="제품 검색" />
        <button className="primary-button" type="submit" disabled={loading}>{loading ? "조회 중" : "월 통계 조회"}</button>
        <button className="secondary-button" type="button" onClick={handleReset} disabled={loading}>데이터 리셋</button>
      </form>

      <section className="metrics-grid">
        <MetricCard label="저장된 월 데이터" value={records.length} />
        <MetricCard label="이번 달 총 출고" value={monthlyTotal} />
        <MetricCard label="12개월 누적 제품수" value={trend.items.length} />
        <MetricCard label="미리보기 선택 건수" value={selectedPreviewCount} />
        <MetricCard label="현재고 조정 선택" value={selectedAdjustmentCount} />
      </section>

      <form className="panel upload-hero" onSubmit={handlePreview}>
        <div>
          <h2>{year}년 {month}월 업로드 반영</h2>
          <p>월별 통계 페이지에서 해당 월 파일을 바로 비교하고 반영합니다.</p>
        </div>
        <div className="upload-controls">
          <label className="file-picker">
            <span>{file ? file.name : "xlsx 선택"}</span>
            <input type="file" accept=".xlsx" onChange={(event) => setFile(event.target.files?.[0] || null)} />
          </label>
          <button className="primary-button" type="submit" disabled={uploading}>
            {uploading ? "비교 중" : "업로드 비교"}
          </button>
          <button className="secondary-button" type="button" onClick={resetPreviewSelection} disabled={!preview}>
            비교 초기화
          </button>
        </div>
      </form>

      {preview ? (
        <section className="panel table-panel">
          <div className="panel-header">
            <div>
              <h2>업로드 비교 결과</h2>
              <p>매칭 {preview.matched_rows}건 / 미매칭 {preview.unmatched_rows}건 / 차이 감지 {diffPreviewCount}건</p>
            </div>
            <div className="button-row">
              <button className="secondary-button" type="button" onClick={() => bulkSelect(true)}>전체 선택</button>
              <button className="secondary-button" type="button" onClick={() => bulkSelect(false)}>전체 해제</button>
              <button className="secondary-button" type="button" onClick={() => bulkAdjust(true)}>현재고 조정 전체 선택</button>
              <button className="secondary-button" type="button" onClick={() => bulkAdjust(false)}>현재고 조정 전체 해제</button>
              <button className="primary-button" type="button" onClick={handleCommit} disabled={uploading}>
                {uploading ? "반영 중" : "최종 반영"}
              </button>
            </div>
          </div>
          <div className="table-scroller">
            <table>
              <thead>
                <tr>
                  <th>반영</th>
                  <th>제품</th>
                  <th>매칭</th>
                  <th>기존 월데이터</th>
                  <th>시스템 현재고</th>
                  <th>업로드 현재고</th>
                  <th>차이</th>
                  <th>현재고 조정</th>
                  <th>출고</th>
                  <th>비고</th>
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, index) => (
                  <tr key={`${row.row_number}-${row.product_code || row.name}`}>
                    <td>
                      <input
                        type="checkbox"
                        checked={row.selected}
                        onChange={(event) => updatePreviewRow(index, { selected: event.target.checked })}
                      />
                    </td>
                    <td>
                      <div className="cell-title">
                        <strong>{row.name}</strong>
                        <span>{row.product_code || "-"} / {row.legacy_code || "-"}</span>
                      </div>
                    </td>
                    <td><span className={`badge ${row.matched ? "matched" : "danger"}`}>{row.matched ? "매칭" : "미매칭"}</span></td>
                    <td><span className={`badge ${row.existing_record_id ? (row.existing_record_diff ? "warning" : "matched") : "neutral"}`}>{row.existing_record_id ? (row.existing_record_diff ? "변경있음" : "기존있음") : "신규"}</span></td>
                    <td className="number">{formatNumber(row.system_current_stock)}</td>
                    <td>
                      <input
                        className="table-input number"
                        value={row.file_current_stock}
                        onChange={(event) => updatePreviewRow(index, { file_current_stock: Number(event.target.value || 0) })}
                      />
                    </td>
                    <td className={`number ${row.current_stock_diff !== 0 ? "danger" : ""}`}>{formatNumber(row.current_stock_diff)}</td>
                    <td>
                      <input
                        type="checkbox"
                        checked={row.apply_stock_adjustment}
                        onChange={(event) => updatePreviewRow(index, { apply_stock_adjustment: event.target.checked })}
                      />
                    </td>
                    <td>
                      <input
                        className="table-input number"
                        value={row.outbound_quantity}
                        onChange={(event) => updatePreviewRow(index, { outbound_quantity: Number(event.target.value || 0) })}
                      />
                    </td>
                    <td>
                      <input
                        className="table-input"
                        value={row.note || ""}
                        onChange={(event) => updatePreviewRow(index, { note: event.target.value })}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      <section className="panel table-panel">
        <div className="panel-header">
          <div>
            <h2>제품별 월 출고량</h2>
            <p>{year}년 {month}월 OUT 합계를 표시합니다.</p>
          </div>
        </div>
        {loading ? <div className="state-message">월 통계를 불러오는 중입니다.</div> : null}
        <div className="table-scroller">
          <table>
            <thead>
              <tr>
                <th>제품명</th>
                <th>제품코드</th>
                <th>월 출고량</th>
              </tr>
            </thead>
            <tbody>
              {filteredReportItems.map((item) => (
                <tr key={item.product_id}>
                  <td>{item.name}</td>
                  <td>
                    {item.product_code || "-"}
                    {item.legacy_code ? ` / ${item.legacy_code}` : ""}
                  </td>
                  <td className="number">{Number(item.outbound_quantity).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel table-panel">
        <div className="panel-header">
          <div>
            <h2>최근 12개월 출고 추이</h2>
            <p>선택한 월을 기준으로 최근 12개월 제품별 출고량을 봅니다.</p>
          </div>
        </div>
        <div className="table-scroller">
          <table>
            <thead>
              <tr>
                <th>제품명</th>
                {trend.months.map((item) => (
                  <th key={item.label}>{item.label}</th>
                ))}
                <th>12개월 합계</th>
                <th>월 평균</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrendItems.map((item) => (
                <tr key={item.product_id}>
                  <td>
                    <div className="cell-title">
                      <strong>{item.name}</strong>
                      <span>
                        {item.product_code || "-"}
                        {item.legacy_code ? ` / ${item.legacy_code}` : ""}
                      </span>
                    </div>
                  </td>
                  {item.monthly_quantities.map((quantity, index) => (
                    <td key={`${item.product_id}-${trend.months[index]?.label || index}`} className="number">
                      {formatNumber(quantity)}
                    </td>
                  ))}
                  <td className="number">{formatNumber(item.total_outbound_quantity)}</td>
                  <td className="number">{formatDecimal(item.average_outbound_quantity)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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
