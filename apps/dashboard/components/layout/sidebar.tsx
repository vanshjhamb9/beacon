"use client";

import {
  BarChart3,
  Building2,
  FolderKanban,
  Handshake,
  Home,
  PhoneCall,
  Radar,
  Send,
  Settings,
  Sparkles,
  Target,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/leads", label: "Leads", icon: Target },
  { href: "/lead-engine", label: "Lead Engine", icon: Radar },
  { href: "/pipeline", label: "Qualified Leads", icon: FolderKanban },
  { href: "/partner-leads", label: "COMAI B2B Partners", icon: Handshake },
  { href: "/cold-call", label: "Cold Call Today", icon: PhoneCall },
  { href: "/universe", label: "Company Universe", icon: Building2 },
  { href: "/outreach", label: "Outreach", icon: Send },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

type SidebarProps = {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
};

export function Sidebar({ mobileOpen = false, onMobileClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      <div
        className={cn(
          "fixed inset-0 z-40 bg-black/50 backdrop-blur-[1px] transition lg:hidden",
          mobileOpen ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={onMobileClose}
        aria-hidden={!mobileOpen}
      />

      <aside
        className={cn(
          "group/sidebar fixed inset-y-0 left-0 z-50 flex h-full w-[72px] flex-col border-r border-border/70 bg-[#0a111c]/95 transition-[width,transform] duration-200 ease-out hover:w-[220px]",
          mobileOpen ? "translate-x-0 w-[220px]" : "-translate-x-full lg:translate-x-0",
        )}
      >
        <div className="flex items-center gap-3 px-4 py-5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-status-ready/15 text-status-ready shadow-soft">
            <Sparkles className="h-4 w-4" />
          </div>
          <div className="min-w-0 overflow-hidden opacity-0 transition-opacity duration-150 group-hover/sidebar:opacity-100 max-lg:opacity-100">
            <p className="truncate font-display text-sm font-semibold tracking-tight">Beacon</p>
            <p className="truncate text-[11px] text-muted-foreground">Founder OS</p>
          </div>
          <button
            type="button"
            className="ml-auto rounded-lg p-1.5 text-muted-foreground hover:bg-muted/50 lg:hidden"
            onClick={onMobileClose}
            aria-label="Close menu"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-2 pb-4" aria-label="Primary">
          {NAV.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onMobileClose}
                title={item.label}
                className={cn(
                  "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                  active
                    ? "bg-primary/10 text-foreground"
                    : "text-muted-foreground hover:bg-muted/40 hover:text-foreground",
                )}
              >
                <Icon className={cn("h-4 w-4 shrink-0", active ? "text-primary" : "")} />
                <span className="truncate font-medium opacity-0 transition-opacity duration-150 group-hover/sidebar:opacity-100 max-lg:opacity-100">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-border/70 px-3 py-4">
          <div className="flex items-center gap-3 rounded-xl bg-muted/30 px-2 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-status-info/20 text-xs font-semibold text-status-info">
              V
            </div>
            <div className="min-w-0 overflow-hidden opacity-0 transition-opacity duration-150 group-hover/sidebar:opacity-100 max-lg:opacity-100">
              <p className="truncate text-sm font-medium">Vansh</p>
              <p className="truncate text-xs text-muted-foreground">Founder</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
