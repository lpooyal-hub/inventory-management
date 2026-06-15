import React from "react";

export default function Layout({
  navItems,
  pathname,
  onNavigate,
  theme,
  onToggleTheme,
  themeIcon,
  children,
}) {
  const titleMap = {
    "/inventory": "재고현황",
    "/products": "제품 관리",
    "/movements": "일일 출고 입력",
    "/uploads/monthly": "월별 통계/업로드",
    "/monthly-data": "월별 데이터 수정",
    "/reports/monthly": "월별 통계/업로드",
    "/reports/shortage": "부족 재고 리포트",
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => onNavigate("/inventory")} type="button">
          <span className="brand-mark">IM</span>
          <span className="brand-copy">
            <strong>Inventory MVP</strong>
            <small>daily outbound first</small>
          </span>
        </button>

        <nav className="nav-list" aria-label="Primary">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;
            return (
              <button
                key={item.path}
                className={`nav-link ${isActive ? "active" : ""}`}
                onClick={() => onNavigate(item.path)}
                type="button"
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-note">
          <p>부족 상태가 보이면 바로 생산주문 후보입니다.</p>
          <strong>빨간불 = 우선 확인</strong>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Simple Inventory Operations</p>
            <h1>{titleMap[pathname] || "재고현황"}</h1>
          </div>
          <button className="theme-toggle" onClick={onToggleTheme} type="button">
            {themeIcon}
            <span>{theme === "light" ? "다크모드" : "라이트모드"}</span>
          </button>
        </header>

        {children}
      </main>
    </div>
  );
}
