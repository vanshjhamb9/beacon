"use client";

import { Suspense } from "react";

import { SearchWorkspace } from "@/features/search/search-workspace";
import { Skeleton } from "@/components/ui/skeleton";

export default function SearchPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <SearchWorkspace />
    </Suspense>
  );
}
