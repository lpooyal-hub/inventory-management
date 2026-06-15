import React, { startTransition, useState } from "react";
import { AlertCircle, CheckCircle2, FileSpreadsheet, RefreshCw } from "lucide-react";
import { commitInventoryUpload, previewInventoryUpload } from "../api";

export default function UploadPage({ onNavigate }) {
  const [file, setFile] = useState(null);
  const [year, setYear] = useState("2026");
  const [month, setMonth] = useState("6");
  const [preview, setPreview] = useState(null);
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handlePreview() {
    if (!file) {
      setError("업로드할 xlsx 파일을 먼저 선택해주세요.");
      return;
    }
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const data = await previewInventoryUpload({ file, year, month });
      startTransition(() => setPreview(data));
      setReplaceExisting(data.summary.should_confirm_replace);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCommit() {
    if (!preview) return;
    setCommitting(true);
    setError("");
    setMessage("");
    try {
      const data = await commitInventoryUpload({
        ...preview.summary,
        file_name: preview.summary.file_name,
        source: preview.summary.source,
        year: preview.summary.year,
        month: preview.summary.month,
        rows: preview.rows,
        errors: preview.errors,
        replace_existing: replaceExisting,
      });
      setMessage(`batch #${data.batch_id}로 저장했습니다.`);
      onNavigate("/uploads");
    } catch (err) {
      setError(err.message);
    } finally {
      setCommitting(false);
    }
  }

  return (
    <>
      <section className="panel upload-hero">
        <div>
          <h2>월별 입출고 통계 업로드</h2>
          <p>필수 컬럼 검증, 상품 매칭, 중복 확인 후 commit 합니다.</p>
        </div>
        <div className="upload-controls">
          <label className="file-picker">
            <FileSpreadsheet size={18} />
            <span>{file ? file.name : "xlsx 파일 선택"}</span>
            <input
              type="file"
              accept=".xlsx"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
          <input value={year} onChange={(event) => setYear(event.target.value)} placeholder="year" />
          <input value={month} onChange={(event) => setMonth(event.target.value)} placeholder="month" />
          <button className="primary-button" disabled={loading} onClick={handlePreview} type="button">
            {loading ? "미리보기 생성 중..." : "미리보기 생성"}
          </button>
        </div>
      </section>

      {error ? <div className="state-message error">{error}</div> : null}
      {message ? <div className="state-message success">{message}</div> : null}

      {preview ? (
        <>
          <section className="metrics-grid">
            <MetricCard label="총 행 수" value={preview.summary.total_rows} />
            <MetricCard label="매칭 성공" value={preview.summary.matched_rows} />
            <MetricCard label="미매칭" value={preview.summary.unmatched_rows} />
            <MetricCard label="오류" value={preview.summary.error_rows} />
          </section>

          <section className="panel replace-panel">
            <div>
              <h2>저장 정책</h2>
              <p>같은 월 committed batch가 있으면 교체 여부를 명시적으로 선택합니다.</p>
            </div>
            <label className="checkbox-row">
              <input
                checked={replaceExisting}
                onChange={(event) => setReplaceExisting(event.target.checked)}
                type="checkbox"
              />
              <span>기존 committed batch를 rolled_back 처리하고 이번 업로드로 대체</span>
            </label>
            <button className="primary-button" disabled={committing} onClick={handleCommit} type="button">
              {committing ? "저장 중..." : "최종 반영"}
            </button>
          </section>

          <section className="panel table-panel">
            <div className="panel-header">
              <div>
                <h2>업로드 미리보기</h2>
                <p>상품코드, 바코드, 상품명 유사도 순으로 매칭했습니다.</p>
              </div>
            </div>
            <div className="table-scroller">
              <table>
                <thead>
                  <tr>
                    <th>행</th>
                    <th>상품코드</th>
                    <th>외부코드</th>
                    <th>상품명</th>
                    <th>현재고</th>
                    <th>입고</th>
                    <th>출고</th>
                    <th>매칭</th>
                    <th>비고</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.map((row) => (
                    <tr key={row.row_number}>
                      <td>{row.row_number}</td>
                      <td>{row.product_code || "-"}</td>
                      <td>{row.external_code || "-"}</td>
                      <td>{row.product_name}</td>
                      <td className="number">{formatNumber(row.current_stock)}</td>
                      <td className="number">{formatNumber(row.inbound_quantity)}</td>
                      <td className="number">{formatNumber(row.outbound_quantity)}</td>
                      <td>
                        {row.matched ? (
                          <span className="badge matched">
                            <CheckCircle2 size={14} />
                            {row.match_method}
                          </span>
                        ) : (
                          <span className="badge warning">
                            <AlertCircle size={14} />
                            신규
                          </span>
                        )}
                      </td>
                      <td>{row.is_duplicate ? row.duplicate_reason : "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {preview.errors.length ? (
            <section className="panel table-panel">
              <div className="panel-header">
                <div>
                  <h2>검증 오류</h2>
                  <p>필수 컬럼 누락이나 값 이상 행입니다.</p>
                </div>
              </div>
              <div className="error-list">
                {preview.errors.map((item) => (
                  <div className="error-card" key={`${item.row_number}-${item.error_message}`}>
                    <strong>{item.row_number}행</strong>
                    <span>{item.error_message}</span>
                  </div>
                ))}
              </div>
            </section>
          ) : null}
        </>
      ) : (
        <section className="empty-state">
          <RefreshCw size={18} />
          <p>파일을 올리면 미리보기와 매칭 결과가 여기 표시됩니다.</p>
        </section>
      )}
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
