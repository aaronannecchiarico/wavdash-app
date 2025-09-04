import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const inputVariants = cva(
  "neo-border neo-shadow-hover bg-[var(--neo-bg-primary)] font-mono text-base px-4 py-3 w-full min-w-0 outline-none disabled:opacity-50 file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium",
  {
    variants: {
      variant: {
        default: "border-[var(--neo-black)] dark:border-[var(--neo-white)] placeholder:text-[var(--neo-text-primary)]/50",
        accent: "border-[var(--neo-green)] bg-[var(--neo-green)]/5 placeholder:text-[var(--neo-black)]/50",
        error: "border-red-500 bg-red-50 dark:bg-red-900/20 placeholder:text-red-500/50",
      },
      size: {
        default: "h-12 px-4 py-3 text-base",
        sm: "h-10 px-3 py-2 text-sm",
        lg: "h-16 px-6 py-4 text-lg",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Input({ 
  className, 
  type, 
  variant,
  size,
  ...props 
}: React.ComponentProps<"input"> & VariantProps<typeof inputVariants>) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        inputVariants({ variant, size }),
        "focus:shadow-none focus:translate-x-1 focus:translate-y-1 focus:border-[var(--neo-accent-1)]",
        "selection:bg-[var(--neo-accent-1)] selection:text-[var(--neo-black)]",
        className
      )}
      {...props}
    />
  )
}

export { Input }
