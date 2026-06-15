import React, { useEffect, useMemo, useState } from "react";
import { createStockMovement, fetchInventorySummary, fetchProducts } from "../api";

export default function MovementPage() {
  const [products, setProducts] = useState([]);
  const [inventoryItems, setInventoryItems] = useState([]);
  const [query, setQuery] = useState("");
  const [movement, setMovement] = useState({
    movement_date: new Date().toISOString().slice(0, 10),
    product_id: "",
    movement_type: "OUT",
    quantity: "",
    memo: "",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadProducts() {
    const [productData, inventoryData] = await Promise.all([fetchProducts(), fetchInventorySummary()]);
    setProducts(productData);
    setInventoryItems(inventoryData.items);
  }

  useEffect(() => {
    loadProducts().catch((err) => setError(err.message));
  }, []);

  const filteredProducts = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return products;
    return products.filter((product) =>
      [product.name, product.product_code, product.legacy_code, product.barcode]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }, [products, query]);

  const currentInventory = useMemo(() => {
    const productId = Number(movement.product_id || 0);
    return inventoryItems.find((item) => item.product_id === productId) || null;
  }, [inventoryItems, movement.product_id]);

  async function submitMovement(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await createStockMovement({
        ...movement,
        product_id: Number(movement.product_id),
        quantity: Number(movement.quantity),
      });
      setMessage(
        movement.movement_type === "ADJUST"
          ? `현재고를 ${Number(movement.quantity).toLocaleString()}개로 맞췄습니다.`
          : "입출고 기록을 저장했습니다."
      );
      setMovement((current) => ({ ...current, quantity: "", memo: "" }));
      await loadProducts();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      {error ? <div className="state-message error">{error}</div> : null}
      {message ? <div className="state-message success">{message}</div> : null}

      <section className="dual-grid">
        <form className="panel form-panel" onSubmit={submitMovement}>
          <div className="panel-header">
            <div>
              <h2>일일 입출고 입력</h2>
              <p>보유 재고에서 매일 나간 수량을 차감하는 기본 입력 화면입니다.</p>
            </div>
          </div>
          <label>
            <span>날짜</span>
            <input
              type="date"
              value={movement.movement_date}
              onChange={(event) => setMovement({ ...movement, movement_date: event.target.value })}
            />
          </label>
          <label>
            <span>제품 검색</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="제품명, 신코드, 구코드 검색"
            />
          </label>
          <label>
            <span>제품</span>
            <select
              value={movement.product_id}
              onChange={(event) => setMovement({ ...movement, product_id: event.target.value })}
            >
              <option value="">제품 선택</option>
              {filteredProducts.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                  {product.product_code ? ` [신:${product.product_code}]` : ""}
                  {product.legacy_code ? ` [구:${product.legacy_code}]` : ""}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>구분</span>
            <select
              value={movement.movement_type}
              onChange={(event) => setMovement({ ...movement, movement_type: event.target.value })}
            >
              <option value="IN">입고</option>
              <option value="OUT">출고</option>
              <option value="ADJUST">현재고 맞춤</option>
            </select>
          </label>
          {movement.movement_type === "ADJUST" ? (
            <div className="state-message">
              현재 계산 재고: <strong>{Number(currentInventory?.current_stock || 0).toLocaleString()}</strong>
            </div>
          ) : null}
          <label>
            <span>{movement.movement_type === "ADJUST" ? "맞출 현재고" : "수량"}</span>
            <input
              type="number"
              value={movement.quantity}
              onChange={(event) => setMovement({ ...movement, quantity: event.target.value })}
              placeholder={movement.movement_type === "ADJUST" ? "예: 0 또는 18" : "예: 24"}
            />
          </label>
          <label>
            <span>메모</span>
            <input
              value={movement.memo}
              onChange={(event) => setMovement({ ...movement, memo: event.target.value })}
              placeholder="비고"
            />
          </label>
          <button className="primary-button" type="submit">저장</button>
        </form>

        <section className="panel form-panel">
          <div className="panel-header">
            <div>
              <h2>현재고 맞춤 안내</h2>
              <p>초기 재고를 맞추거나 실사값으로 보정할 때는 구분을 <strong>현재고 맞춤</strong>으로 선택하면 됩니다.</p>
            </div>
          </div>
          <div className="empty-state">
            입력한 숫자가 최종 현재고가 되도록 내부에서 차이값을 계산해 조정 이력을 남깁니다. 예를 들어 현재 계산 재고가 12이고 여기에 5를 입력하면, 내부적으로 `-7 ADJUST`가 기록되어 결과 현재고가 5가 됩니다.
          </div>
        </section>
      </section>
    </>
  );
}
