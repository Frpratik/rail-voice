"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Users,
  LayoutDashboard,
  BarChart3,
  User,
  Filter,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface CommandItem {
  id: string;
  category: "Actions" | "Navigation" | "Stations" | "Status Filter";
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  shortcut?: string;
  action: () => void;
}

export function CommandPalette({
  isOpen,
  onClose,
}: {
  isOpen?: boolean;
  onClose?: () => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [selectedIndex, setSelectedIndex] = React.useState(0);
  const router = useRouter();

  const isControlled = typeof isOpen === "boolean";
  const activeOpen = isControlled ? isOpen : open;

  const handleClose = React.useCallback(() => {
    if (isControlled && onClose) {
      onClose();
    } else {
      setOpen(false);
    }
    setQuery("");
    setSelectedIndex(0);
  }, [isControlled, onClose]);

  // Handle global keyboard shortcut Cmd+K / Ctrl+K
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isControlled && onClose && activeOpen) {
          onClose();
        } else if (!isControlled) {
          setOpen((prev) => !prev);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeOpen, isControlled, onClose]);

  const items: CommandItem[] = React.useMemo(
    () => [
      {
        id: "nav-issues",
        category: "Navigation",
        label: "Go to Issues Management",
        icon: LayoutDashboard,
        shortcut: "G I",
        action: () => {
          router.push("/admin/issues");
          handleClose();
        },
      },
      {
        id: "nav-analytics",
        category: "Navigation",
        label: "Go to Analytics & Velocity",
        icon: BarChart3,
        shortcut: "G A",
        action: () => {
          router.push("/admin/analytics");
          handleClose();
        },
      },
      {
        id: "nav-reports",
        category: "Navigation",
        label: "Go to Reports & Audits",
        icon: FileText,
        shortcut: "G R",
        action: () => {
          router.push("/admin/reports");
          handleClose();
        },
      },
      {
        id: "nav-users",
        category: "Navigation",
        label: "Go to User Roles & RBAC",
        icon: Users,
        shortcut: "G U",
        action: () => {
          router.push("/admin/users");
          handleClose();
        },
      },
      {
        id: "nav-profile",
        category: "Navigation",
        label: "Go to Profile Settings",
        icon: User,
        shortcut: "G P",
        action: () => {
          router.push("/profile");
          handleClose();
        },
      },
      {
        id: "action-in-progress",
        category: "Actions",
        label: "Filter: Status -> Work In Progress",
        icon: CheckCircle2,
        shortcut: "S W",
        action: () => {
          router.push("/admin/issues?status=work_in_progress");
          handleClose();
        },
      },
      {
        id: "action-escalated",
        category: "Actions",
        label: "Filter: Status -> SLA Escalated",
        icon: AlertTriangle,
        shortcut: "S E",
        action: () => {
          router.push("/admin/issues?status=forwarded_station_manager");
          handleClose();
        },
      },
      {
        id: "stn-bandra",
        category: "Stations",
        label: "Filter Station: Bandra Terminus (BDTS)",
        icon: Filter,
        action: () => {
          router.push("/admin/issues?station=BDTS");
          handleClose();
        },
      },
      {
        id: "stn-andheri",
        category: "Stations",
        label: "Filter Station: Andheri (ADH)",
        icon: Filter,
        action: () => {
          router.push("/admin/issues?station=ADH");
          handleClose();
        },
      },
      {
        id: "stn-borivali",
        category: "Stations",
        label: "Filter Station: Borivali (BVI)",
        icon: Filter,
        action: () => {
          router.push("/admin/issues?station=BVI");
          handleClose();
        },
      },
      {
        id: "stn-dadar",
        category: "Stations",
        label: "Filter Station: Dadar (DDR)",
        icon: Filter,
        action: () => {
          router.push("/admin/issues?station=DDR");
          handleClose();
        },
      },
      {
        id: "stn-virar",
        category: "Stations",
        label: "Filter Station: Virar (VR)",
        icon: Filter,
        action: () => {
          router.push("/admin/issues?station=VR");
          handleClose();
        },
      },
    ],
    [router, handleClose]
  );

  const filteredItems = React.useMemo(() => {
    if (!query.trim()) return items;
    const q = query.toLowerCase().trim();
    return items.filter(
      (item) =>
        item.label.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q)
    );
  }, [items, query]);

  // Handle arrow key navigation inside modal
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!activeOpen) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % (filteredItems.length || 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev === 0 ? Math.max(0, filteredItems.length - 1) : prev - 1
      );
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filteredItems[selectedIndex]) {
        filteredItems[selectedIndex].action();
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      handleClose();
    }
  };

  if (!activeOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/60 backdrop-blur-md transition-opacity animate-in fade-in duration-150"
      onClick={handleClose}
      onKeyDown={handleKeyDown}
    >
      <div
        className="w-full max-w-xl rounded-2xl border border-border bg-card shadow-2xl overflow-hidden text-foreground animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Input Bar */}
        <div className="flex items-center gap-3 border-b border-border px-4 py-3.5 bg-muted/30">
          <Search className="h-5 w-5 text-muted-foreground shrink-0" />
          <input
            type="text"
            autoFocus
            placeholder="Type a command, filter, or search page (e.g. 'analytics', 'Bandra')..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            className="w-full bg-transparent text-sm font-medium placeholder:text-muted-foreground/60 focus:outline-none"
          />
          <kbd className="hidden sm:inline-flex items-center gap-1 rounded bg-muted px-2 py-0.5 text-[10px] font-mono font-semibold text-muted-foreground border border-border">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filteredItems.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              No matching command found for &quot;{query}&quot;
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <button
                  key={item.id}
                  onClick={() => item.action()}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-colors text-left",
                    isSelected
                      ? "bg-accent/15 text-accent-foreground dark:text-accent border border-accent/20"
                      : "text-foreground/80 hover:bg-muted/50"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        "p-1.5 rounded-lg",
                        isSelected
                          ? "bg-accent text-accent-foreground"
                          : "bg-muted text-muted-foreground"
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <span className="font-semibold">{item.label}</span>
                      <span className="ml-2 text-[10px] text-muted-foreground uppercase font-mono tracking-wider">
                        • {item.category}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {item.shortcut && (
                      <kbd className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono font-semibold text-muted-foreground border border-border">
                        {item.shortcut}
                      </kbd>
                    )}
                    <ArrowRight
                      className={cn(
                        "h-3.5 w-3.5 transition-transform",
                        isSelected
                          ? "opacity-100 translate-x-0"
                          : "opacity-0 -translate-x-1"
                      )}
                    />
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className="flex items-center justify-between border-t border-border px-4 py-2 bg-muted/20 text-[11px] text-muted-foreground font-mono">
          <div className="flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-accent" />
            <span>RailVoice Command Palette</span>
          </div>
          <div className="flex items-center gap-3">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>Esc Close</span>
          </div>
        </div>
      </div>
    </div>
  );
}
