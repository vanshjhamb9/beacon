"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { CompanyDrawer } from "@/components/company/company-drawer";
import { ErrorState } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { PIPELINE_COLUMNS, PIPELINE_STATUS_MAP, pipelineColumn } from "@/lib/founder";
import { mergeLead } from "@/lib/lead";
import { cn, formatScore } from "@/lib/utils";

export function PipelineWorkspace() {
  const qc = useQueryClient();
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [drawer, setDrawer] = useState<Record<string, unknown> | null>(null);

  const workspace = useQuery({
    queryKey: ["ofc-workspace"],
    queryFn: () => beaconApi.ofcWorkspace(),
    refetchInterval: 60_000,
  });

  const transition = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => beaconApi.ofcTransition(id, status),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["ofc-workspace"] }),
  });

  const items = useMemo(
    () => ((workspace.data?.items as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>,
    [workspace.data],
  );

  const columns = useMemo(() => {
    const map = Object.fromEntries(PIPELINE_COLUMNS.map((col) => [col, [] as Array<Record<string, unknown>>])) as Record<
      string,
      Array<Record<string, unknown>>
    >;
    for (const item of items) {
      const col = pipelineColumn(String(item.status));
      map[col]?.push(item);
    }
    return map;
  }, [items]);

  if (workspace.isError) {
    return <ErrorState title="Pipeline unavailable" description="Could not load deals." />;
  }
  if (workspace.isLoading) return <Skeleton className="h-80 w-full" />;

  return (
    <div className="space-y-5">
      <header>
        <p className="text-sm text-muted-foreground">Drag companies through the path to close</p>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Pipeline</h1>
      </header>

      <div className="-mx-1 flex gap-3 overflow-x-auto px-1 pb-2 scrollbar-thin">
        {PIPELINE_COLUMNS.map((column) => (
          <div
            key={column}
            className="flex min-h-[420px] w-[240px] shrink-0 flex-col rounded-xl border border-border/60 bg-card/40"
            onDragOver={(event) => event.preventDefault()}
            onDrop={() => {
              if (!draggingId) return;
              const status = PIPELINE_STATUS_MAP[column];
              transition.mutate({ id: draggingId, status });
              setDraggingId(null);
            }}
          >
            <div className="flex items-center justify-between border-b border-border/50 px-3 py-3">
              <p className="text-sm font-medium">{column}</p>
              <span className="text-xs text-muted-foreground">{columns[column]?.length || 0}</span>
            </div>
            <div className="flex-1 space-y-2 p-2">
              {(columns[column] || []).map((item) => {
                const id = String(item.id);
                const lead = mergeLead(item);
                return (
                  <button
                    key={id}
                    type="button"
                    draggable
                    onDragStart={() => setDraggingId(id)}
                    onDragEnd={() => setDraggingId(null)}
                    onClick={() => setDrawer(item)}
                    className={cn(
                      "w-full rounded-lg border border-border/60 bg-[#0d1524] px-3 py-3 text-left transition hover:border-primary/30",
                      draggingId === id && "opacity-60",
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-medium">{lead.company}</p>
                      <span className="text-[11px] text-muted-foreground">{formatScore(lead.confidence, 0)}</span>
                    </div>
                    <p className="mt-1 truncate text-xs text-muted-foreground">{lead.decisionMaker}</p>
                    <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{lead.whyNow}</p>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <CompanyDrawer
        open={Boolean(drawer)}
        onClose={() => setDrawer(null)}
        companyId={drawer ? String(drawer.company_id || "") : null}
        companyName={drawer ? String(drawer.company_name || drawer.company || "") : null}
        recordId={drawer ? String(drawer.id || "") : null}
        seed={drawer}
      />
    </div>
  );
}
