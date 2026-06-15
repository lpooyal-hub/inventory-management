import React, { useEffect, useState } from "react";
import { fetchUploads } from "../api";

export default function UploadHistoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await fetchUploads();
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

  return (
    <section className="panel table-panel">
      <div className="panel-header">
        <div>
          <h2>업로드 배치 목록</h2>
          <p>preview, committed, rolled_back 상태를 모두 확인할 수 있습니다.</p>
        </div>
      </div>

      {loading ? <div className="state-message">업로드 이력을 불러오는 중입니다.</div> : null}
      {error ? <div className="state-message error">{error}</div> : null}

      {!loading && !error ? (
        <div className="table-scroller">
          <table>
            <thead>
              <tr>
                <th>배치 ID</th>
                <th>파일명</th>
                <th>반영월</th>
                <th>상태</th>
                <th>총 행</th>
                <th>매칭</th>
                <th>미매칭</th>
                <th>오류</th>
                <th>업로드 시각</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.file_name}</td>
                  <td>{item.year}-{String(item.month).padStart(2, "0")}</td>
                  <td>
                    <span className={`badge ${statusClassName(item.status)}`}>{item.status}</span>
                  </td>
                  <td className="number">{item.total_rows}</td>
                  <td className="number">{item.matched_rows}</td>
                  <td className="number">{item.unmatched_rows}</td>
                  <td className="number">{item.error_rows}</td>
                  <td>{new Date(item.uploaded_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function statusClassName(status) {
  if (status === "committed") return "matched";
  if (status === "rolled_back") return "warning";
  if (status === "failed") return "danger";
  return "neutral";
}
