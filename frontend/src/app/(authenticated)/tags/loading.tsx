import { TableSkeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <div className="p-6">
      <div className="mb-6 h-8 w-32 animate-pulse rounded bg-zinc-800/50" />
      <TableSkeleton rows={4} />
    </div>
  )
}
