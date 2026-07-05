import { cn } from "@/lib/utils"
import { Input as InputPrimitive } from "@base-ui/react/input"

function Input({ className, ...props }: InputPrimitive.Props) {
  return (
    <InputPrimitive
      data-slot="input"
      className={cn(
        "flex h-9 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm shadow-xs transition-colors",
        "placeholder:text-muted-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  )
}

export { Input }
