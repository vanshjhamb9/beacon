import { Suspense } from "react";
import { LeadsWorkspace } from "@/features/leads/leads-workspace";

export default function LeadsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-muted-foreground">Loading leads...</div>}>
      <LeadsWorkspace />
    </Suspense>
  );
}
