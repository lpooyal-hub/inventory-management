import React, { startTransition, useEffect, useState } from "react";
import { ClipboardMinus, Database, FileSpreadsheet, MoonStar, Package2, ReceiptText, Settings2, SunMedium } from "lucide-react";
import Layout from "./components/Layout";
import InventoryPage from "./pages/InventoryPage";
import MonthlyDataPage from "./pages/MonthlyDataPage";
import MovementPage from "./pages/MovementPage";
import MonthlyReportPage from "./pages/MonthlyReportPage";
import ProductsPage from "./pages/ProductsPage";
import ShortageReportPage from "./pages/ShortageReportPage";

const navItems = [
  { path: "/inventory", label: "재고현황", icon: Package2 },
  { path: "/products", label: "제품 관리", icon: Settings2 },
  { path: "/movements", label: "일일 출고 입력", icon: ClipboardMinus },
  { path: "/reports/monthly", label: "월별 통계/업로드", icon: FileSpreadsheet },
  { path: "/monthly-data", label: "월별 데이터 수정", icon: Database },
  { path: "/reports/shortage", label: "부족 재고 리포트", icon: ReceiptText },
];

function getPathname() {
  const path = window.location.pathname;
  return path === "/" ? "/inventory" : path;
}

export default function App() {
  const [pathname, setPathname] = useState(getPathname);
  const [theme, setTheme] = useState("light");

  useEffect(() => {
    const handlePopState = () => setPathname(getPathname());
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  function navigate(path) {
    if (path === pathname) return;
    window.history.pushState({}, "", path);
    startTransition(() => setPathname(path));
  }

  function toggleTheme() {
    setTheme((current) => (current === "light" ? "dark" : "light"));
  }

  let content = <InventoryPage />;
  if (pathname === "/products") content = <ProductsPage />;
  if (pathname === "/movements") content = <MovementPage />;
  if (pathname === "/uploads/monthly") content = <MonthlyReportPage />;
  if (pathname === "/monthly-data") content = <MonthlyDataPage />;
  if (pathname === "/reports/monthly") content = <MonthlyReportPage />;
  if (pathname === "/reports/shortage") content = <ShortageReportPage />;

  return (
    <Layout
      navItems={navItems}
      pathname={pathname}
      onNavigate={navigate}
      theme={theme}
      onToggleTheme={toggleTheme}
      themeIcon={theme === "light" ? <MoonStar size={16} /> : <SunMedium size={16} />}
    >
      {content}
    </Layout>
  );
}
