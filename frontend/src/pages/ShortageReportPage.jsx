import React, { useEffect, useState } from "react";
import { fetchShortageReport } from "../api";

export default function ShortageReportPage() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchShortageReport()
      .then((data) => setItems(data.items))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <section className="panel table-panel">
      <div className="panel-header">
        <div>
          <h2>부족 재고 리포트</h2>
          <p>빨간불이 들어온 제품은 생산주문 필요 제품으로 봅니다.</p>
        </div>
      </div>
      {error ? <div className="state-message error">{error}</div> : null}
      <div className="table-scroller">
        <table>
          <thead>
            <tr>
              <th>제품명</th>
              <th>현재고</th>
              <th>이번 달 출고량</th>
              <th>최근 3개월 월 평균</th>
              <th>이번달 남은 출고 예상량</th>
              <th>예상 출고 반영 후 재고</th>
              <th>부족 상태</th>
              <th>생산주문 필요</th>
            </tr>
          </thead>
          <tbody>
              {items.map((item) => (
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
                <td className="number">{Number(item.current_stock).toLocaleString()}</td>
                <td className="number">{Number(item.current_month_outbound).toLocaleString()}</td>
                <td className="number">
                  {Number(item.average_monthly_outbound_last_3_months).toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </td>
                <td className="number">
                  {Number(item.remaining_expected_outbound_this_month).toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </td>
                <td className="number danger">
                  {Number(item.projected_stock_after_expected_outbound).toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </td>
                <td>
                  <span className={`status-dot ${item.shortage_status === "심각 부족" ? "critical" : "warning"}`}>
                    {item.shortage_status}
                  </span>
                </td>
                <td>{item.production_order_required ? "필요" : "정상"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
