import { StatsCardSkeleton, TableSkeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <div className="p-6">
      <div className="mb-6 h-8 w-48 animate-pulse rounded bg-zinc-800/50" />
      <StatsCardSkeleton />
      <div className="mt-6 h-8 w-32 animate-pulse rounded bg-zinc-800/50" />
      <div className="mt-4"><TableSkeleton rows={5} /></div>
    </div>
  )
}
