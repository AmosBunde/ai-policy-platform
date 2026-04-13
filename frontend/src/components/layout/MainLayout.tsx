import { useEffect } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

export function MainLayout() {
  const navigate = useNavigate();

  // Cmd+K (Mac) / Ctrl+K (Windows) — global search shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        navigate("/search");
        // Focus the search input after navigation
        setTimeout(() => {
          const input = document.querySelector<HTMLInputElement>(
            'input[aria-label="Search"]',
          );
          input?.focus();
        }, 100);
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [navigate]);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-navy-900">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
