import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  Users,
  FolderOpen,
  Download,
  Mailbox,
} from "lucide-react";
import { toast } from "../shared/Toast";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/articles", label: "Articles", icon: FileText },
  { to: "/community", label: "Community", icon: Users },
  { to: "/categories", label: "Categories", icon: FolderOpen },
  { to: "/email-sync", label: "Email Sync", icon: Mailbox },
];

export default function CMSLayout() {
  const handleExportParquet = async () => {
    try {
      const res = await fetch("/cms/export-parquet", { method: "POST" });
      if (!res.ok) throw new Error("Export failed");
      toast.success("Parquet exported successfully");
    } catch (err) {
      console.error("Parquet export failed:", err);
      toast.error("Parquet export failed");
    }
  };

  return (
    <div className="flex min-h-screen bg-canvas">
      {/* Sidebar — 240px, canvas bg, hairline right edge */}
      <aside className="w-[240px] shrink-0 bg-canvas border-r border-hairline flex flex-col">
        <div className="px-500 py-700">
          <h1 className="font-display text-title-lg text-ink-primary">
            MVP CMS
          </h1>
        </div>

        <nav className="flex-1 flex flex-col gap-100 px-400">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-400 rounded-md px-400 py-300 text-body-md font-medium transition-colors duration-fast ${
                  isActive
                    ? "bg-accent-tint text-accent"
                    : "text-ink-muted hover:bg-sober hover:text-ink-primary"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-400 pb-500">
          <button
            onClick={handleExportParquet}
            className="flex w-full items-center gap-400 rounded-md px-400 py-300 text-body-md font-medium text-ink-muted transition-colors duration-fast hover:bg-sober hover:text-ink-primary"
          >
            <Download size={18} />
            Export Parquet
          </button>
        </div>
      </aside>

      {/* Content area — elevated bg, dense page gutter */}
      <main className="flex-1 overflow-y-auto bg-elevated min-h-screen">
        <Outlet />
      </main>
    </div>
  );
}
