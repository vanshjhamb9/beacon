import { Suspense } from "react";

import { TodayLeadsWorkspace } from "@/features/today-leads/today-leads-workspace";
import { Skeleton } from "@/components/ui/skeleton";

export default function TodayLeadsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-64 w-full" />}>
      <TodayLeadsWorkspace />
    </Suspense>
  );
}
