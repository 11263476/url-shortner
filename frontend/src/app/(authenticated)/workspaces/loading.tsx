import { TableSkeleton, CardSkeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <div className="p-6">
      <div className="mb-6 h-8 w-48 animate-pulse rounded bg-zinc-800/50" />
      <CardSkeleton count={2} />
      <div className="mt-6"><TableSkeleton rows={3} /></div>
    </div>
  )
}
