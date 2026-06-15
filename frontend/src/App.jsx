import React, { startTransition, useEffect, useState } from "react";
import { Archive, FileUp, Layers3, MoonStar, SunMedium } from "lucide-react";
import Layout from "./components/Layout";
import InventoryPage from "./pages/InventoryPage";
import UploadPage from "./pages/UploadPage";
import UploadHistoryPage from "./pages/UploadHistoryPage";

const navItems = [
  { path: "/inventory", label: "재고현황", icon: Layers3 },
  { path: "/inventory/upload", label: "엑셀 업로드", icon: FileUp },
  { path: "/uploads", label: "업로드 이력", icon: Archive },
];

function getPathname() {
  const path = window.location.pathname;
  if (path === "/") return "/inventory";
  return path;
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
  if (pathname === "/inventory/upload") {
    content = <UploadPage onNavigate={navigate} />;
  } else if (pathname === "/uploads") {
    content = <UploadHistoryPage />;
  }

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
