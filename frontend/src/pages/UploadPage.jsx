import React, { useState } from "react";
import { commitMonthlyUpload, previewMonthlyUpload } from "../api";

export default function UploadPage() {
  const today = new Date();
  const [year, setYear] = useState(String(today.getFullYear()));
  const [month, setMonth] = useState(String(today.getMonth() + 1));
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handlePreview(event) {
    event.preventDefault();
    if (!file) {
      setError("업로드할 xlsx 파일을 선택해주세요.");
      return;
    }
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const data = await previewMonthlyUpload(file, year, month);
      setPreview(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCommit() {
    if (!preview) return;
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const result = await commitMonthlyUpload({
        file_name: preview.file_name,
        year: Number(preview.year),
        month: Number(preview.month),
        rows: preview.rows,
      });
      setMessage(`저장 ${result.saved_rows}건, 현재고 조정 ${result.adjusted_rows}건 반영했습니다.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function updateRow(index, patch) {
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

  return (
    <>
      {error ? <div className="state-message error">{error}</div> : null}
      {message ? <div className="state-message success">{message}</div> : null}

      <form className="panel upload-hero" onSubmit={handlePreview}>
        <div>
          <h2>월별 업로드 비교</h2>
          <p>엑셀 값을 바로 덮어쓰지 않고 시스템 값과 비교한 뒤 반영합니다.</p>
        </div>
        <div className="upload-controls">
          <label className="file-picker">
            <span>{file ? file.name : "xlsx 선택"}</span>
            <input type="file" accept=".xlsx" onChange={(event) => setFile(event.target.files?.[0] || null)} />
          </label>
          <input value={year} onChange={(event) => setYear(event.target.value)} placeholder="연도" />
          <input value={month} onChange={(event) => setMonth(event.target.value)} placeholder="월" />
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "확인 중" : "비교하기"}
          </button>
        </div>
      </form>

      {preview ? (
        <section className="panel table-panel">
          <div className="panel-header">
            <div>
              <h2>업로드 비교 결과</h2>
              <p>매칭 성공 {preview.matched_rows}건 / 실패 {preview.unmatched_rows}건</p>
            </div>
            <button className="primary-button" type="button" onClick={handleCommit} disabled={loading}>
              최종 반영
            </button>
          </div>
          <div className="table-scroller">
            <table>
              <thead>
                <tr>
                  <th>반영</th>
                  <th>제품</th>
                  <th>매칭</th>
                  <th>시스템 현재고</th>
                  <th>업로드 현재고</th>
                  <th>차이</th>
                  <th>현재고 조정</th>
                  <th>입고</th>
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
                        onChange={(event) => updateRow(index, { selected: event.target.checked })}
                      />
                    </td>
                    <td>
                      <div className="cell-title">
                        <strong>{row.name}</strong>
                        <span>
                          {row.product_code || "-"} / {row.legacy_code || "-"}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${row.matched ? "matched" : "danger"}`}>
                        {row.matched ? "매칭" : "미매칭"}
                      </span>
                    </td>
                    <td className="number">{row.system_current_stock.toLocaleString()}</td>
                    <td>
                      <input
                        className="table-input number"
                        value={row.file_current_stock}
                        onChange={(event) => updateRow(index, { file_current_stock: Number(event.target.value || 0) })}
                      />
                    </td>
                    <td className={`number ${row.current_stock_diff !== 0 ? "danger" : ""}`}>
                      {row.current_stock_diff.toLocaleString()}
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        checked={row.apply_stock_adjustment}
                        onChange={(event) => updateRow(index, { apply_stock_adjustment: event.target.checked })}
                      />
                    </td>
                    <td>
                      <input
                        className="table-input number"
                        value={row.inbound_quantity}
                        onChange={(event) => updateRow(index, { inbound_quantity: Number(event.target.value || 0) })}
                      />
                    </td>
                    <td>
                      <input
                        className="table-input number"
                        value={row.outbound_quantity}
                        onChange={(event) => updateRow(index, { outbound_quantity: Number(event.target.value || 0) })}
                      />
                    </td>
                    <td>
                      <input
                        className="table-input"
                        value={row.note || ""}
                        onChange={(event) => updateRow(index, { note: event.target.value })}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </>
  );
}
