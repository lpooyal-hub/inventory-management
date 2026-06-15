import React, { useEffect, useMemo, useState } from "react";
import { createProduct, fetchProducts, updateProduct } from "../api";

const EMPTY_FORM = {
  product_code: "",
  legacy_code: "",
  name: "",
  barcode: "",
  memo: "",
};

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [createForm, setCreateForm] = useState(EMPTY_FORM);
  const [editForm, setEditForm] = useState(EMPTY_FORM);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadProducts() {
    const data = await fetchProducts();
    setProducts(data);
    if (!selectedId && data.length > 0) {
      setSelectedId(data[0].id);
      setEditForm(toForm(data[0]));
    }
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

  useEffect(() => {
    const selectedProduct = products.find((product) => product.id === selectedId);
    if (selectedProduct) {
      setEditForm(toForm(selectedProduct));
    }
  }, [selectedId, products]);

  async function submitCreate(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await createProduct(createForm);
      setCreateForm(EMPTY_FORM);
      setMessage("제품을 등록했습니다.");
      await loadProducts();
    } catch (err) {
      setError(err.message);
    }
  }

  async function submitUpdate(event) {
    event.preventDefault();
    if (!selectedId) return;
    setError("");
    setMessage("");
    try {
      const updated = await updateProduct(selectedId, editForm);
      setProducts((current) => current.map((product) => (product.id === selectedId ? updated : product)));
      setMessage("제품 정보를 수정했습니다.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      {error ? <div className="state-message error">{error}</div> : null}
      {message ? <div className="state-message success">{message}</div> : null}

      <section className="dual-grid wide-right">
        <div className="panel form-panel">
          <div className="panel-header">
            <div>
              <h2>제품 검색</h2>
              <p>신코드, 구코드, 제품명, 바코드로 찾을 수 있습니다.</p>
            </div>
          </div>
          <div className="search-field">
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="제품 검색" />
          </div>
          <div className="list-panel">
            {filteredProducts.map((product) => (
              <button
                key={product.id}
                type="button"
                className={`list-row ${selectedId === product.id ? "active" : ""}`}
                onClick={() => setSelectedId(product.id)}
              >
                <strong>{product.name}</strong>
                <span>
                  {product.product_code || "-"} / {product.legacy_code || "-"}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="stack-grid">
          <form className="panel form-panel" onSubmit={submitUpdate}>
            <div className="panel-header">
              <div>
                <h2>제품 수정</h2>
                <p>현재 선택한 제품의 코드와 이름, 메모를 수정합니다.</p>
              </div>
            </div>
            <label>
              <span>신코드</span>
              <input value={editForm.product_code} onChange={(event) => setEditForm({ ...editForm, product_code: event.target.value })} />
            </label>
            <label>
              <span>구코드</span>
              <input value={editForm.legacy_code} onChange={(event) => setEditForm({ ...editForm, legacy_code: event.target.value })} />
            </label>
            <label>
              <span>제품명</span>
              <input value={editForm.name} onChange={(event) => setEditForm({ ...editForm, name: event.target.value })} />
            </label>
            <label>
              <span>바코드</span>
              <input value={editForm.barcode} onChange={(event) => setEditForm({ ...editForm, barcode: event.target.value })} />
            </label>
            <label>
              <span>메모</span>
              <textarea value={editForm.memo} onChange={(event) => setEditForm({ ...editForm, memo: event.target.value })} />
            </label>
            <button className="primary-button" type="submit" disabled={!selectedId}>수정 저장</button>
          </form>

          <form className="panel form-panel" onSubmit={submitCreate}>
            <div className="panel-header">
              <div>
                <h2>제품 추가</h2>
                <p>구코드가 겹쳐도 일단 등록하고 이후 수정할 수 있습니다.</p>
              </div>
            </div>
            <label>
              <span>신코드</span>
              <input value={createForm.product_code} onChange={(event) => setCreateForm({ ...createForm, product_code: event.target.value })} />
            </label>
            <label>
              <span>구코드</span>
              <input value={createForm.legacy_code} onChange={(event) => setCreateForm({ ...createForm, legacy_code: event.target.value })} />
            </label>
            <label>
              <span>제품명</span>
              <input value={createForm.name} onChange={(event) => setCreateForm({ ...createForm, name: event.target.value })} required />
            </label>
            <label>
              <span>바코드</span>
              <input value={createForm.barcode} onChange={(event) => setCreateForm({ ...createForm, barcode: event.target.value })} />
            </label>
            <label>
              <span>메모</span>
              <textarea value={createForm.memo} onChange={(event) => setCreateForm({ ...createForm, memo: event.target.value })} />
            </label>
            <button className="primary-button" type="submit">제품 등록</button>
          </form>
        </div>
      </section>
    </>
  );
}

function toForm(product) {
  return {
    product_code: product.product_code || "",
    legacy_code: product.legacy_code || "",
    name: product.name || "",
    barcode: product.barcode || "",
    memo: product.memo || "",
  };
}
