"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Command, Menu, RefreshCw, Search, Zap } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

type TopbarProps = {
  onMenuClick?: () => void;
};

export function Topbar({ onMenuClick }: TopbarProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");

  const readiness = useQuery({
    queryKey: ["execution-dashboard-card"],
    queryFn: () => beaconApi.executionDashboardCard(),
    refetchInterval: 30_000,
  });

  const discoveryMutation = useMutation({
    mutationFn: () => beaconApi.leadDiscovery(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fsw-leads"] });
      queryClient.invalidateQueries({ queryKey: ["operations-center-live"] });
    },
  });

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        router.push("/leads");
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [router]);

  const isRunning = discoveryMutation.isPending;

  return (
    <header className="sticky top-0 z-20 border-b border-border/70 bg-[#0b1220]/88 backdrop-blur-xl">
      <div className="flex items-center gap-3 px-4 py-3 sm:px-6">
        <Button variant="ghost" size="icon" className="lg:hidden" onClick={onMenuClick} aria-label="Open menu">
          <Menu className="h-4 w-4" />
        </Button>

        <form
          className="relative min-w-0 flex-1 max-w-md"
          onSubmit={(event) => {
            event.preventDefault();
            const next = query.trim();
            router.push(next ? `/leads?q=${encodeURIComponent(next)}` : "/leads");
          }}
        >
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search leads..."
            className="h-10 bg-card/50 pl-10 pr-16"
            aria-label="Search leads"
          />
          <div className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 items-center gap-1 text-[11px] text-muted-foreground sm:flex">
            <Command className="h-3 w-3" />
            <span>K</span>
          </div>
        </form>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => discoveryMutation.mutate()}
            disabled={isRunning}
            className={cn(
              "hidden sm:inline-flex",
              isRunning && "animate-pulse"
            )}
          >
            {isRunning ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Discovering...
              </>
            ) : (
              <>
                <Zap className="mr-2 h-4 w-4" />
                Run Discovery
              </>
            )}
          </Button>

          <div className="flex items-center gap-2 rounded-lg bg-card/50 px-3 py-1.5">
            <Activity className="h-4 w-4 text-green-500" />
            <span className="text-xs text-muted-foreground">Live</span>
          </div>
        </div>
      </div>
    </header>
  );
}
