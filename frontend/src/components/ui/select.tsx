import { cn } from "@/lib/utils"
import { ChevronDown } from "lucide-react"

function Select({ className, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="relative">
      <select
        data-slot="select"
        className={cn(
          "flex h-9 w-full appearance-none rounded-lg border border-input bg-background px-3 py-2 pr-8 text-sm shadow-xs",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
    </div>
  )
}

export { Select }
