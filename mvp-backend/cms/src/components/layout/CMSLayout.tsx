import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  Users,
  FolderOpen,
  Download,
} from "lucide-react";
import { toast } from "../shared/Toast";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/articles", label: "Articles", icon: FileText },
  { to: "/community", label: "Community", icon: Users },
  { to: "/categories", label: "Categories", icon: FolderOpen },
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
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-[240px] shrink-0 bg-[#1C1C1E] flex flex-col text-white">
        <div className="px-5 py-6">
          <h1 className="text-lg font-bold tracking-wide text-[#C9A84C]">
            MVP CMS
          </h1>
        </div>

        <nav className="flex-1 flex flex-col gap-1 px-3">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-[#C9A84C]/15 text-[#C9A84C]"
                    : "text-gray-400 hover:bg-[#2B2B2E] hover:text-white"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 pb-5">
          <button
            onClick={handleExportParquet}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-400 transition-colors hover:bg-[#2B2B2E] hover:text-white"
          >
            <Download size={18} />
            Export Parquet
          </button>
        </div>
      </aside>

      {/* Content area */}
      <main className="flex-1 overflow-y-auto bg-gray-50 min-h-screen">
        <Outlet />
      </main>

    </div>
  );
}
