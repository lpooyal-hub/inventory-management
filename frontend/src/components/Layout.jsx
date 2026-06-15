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
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => onNavigate("/inventory")} type="button">
          <span className="brand-mark">IM</span>
          <span className="brand-copy">
            <strong>Inventory Flow</strong>
            <small>small business stock desk</small>
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
          <p>월별 업로드는 바로 반영되지 않습니다.</p>
          <strong>미리보기 확인 후 commit</strong>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Web Inventory System</p>
            <h1>
              {pathname === "/inventory/upload"
                ? "월별 입출고 업로드"
                : pathname === "/uploads"
                  ? "업로드 이력"
                  : "종합 재고현황"}
            </h1>
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
