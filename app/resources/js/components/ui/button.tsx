import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-bold uppercase tracking-wider neo-border neo-shadow neo-transition disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus:shadow-none focus:translate-x-0.5 focus:translate-y-0.5",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--neo-green)] text-[var(--neo-black)] hover:bg-[var(--neo-green)]/90 hover:neo-shadow-hover hover:translate-x-0.5 hover:translate-y-0.5",
        secondary:
          "bg-[var(--neo-pink)] text-[var(--neo-white)] hover:bg-[var(--neo-pink)]/90 hover:neo-shadow-hover hover:translate-x-0.5 hover:translate-y-0.5",
        accent:
          "bg-[var(--neo-yellow)] text-[var(--neo-black)] hover:bg-[var(--neo-yellow)]/90 hover:neo-shadow-hover hover:translate-x-0.5 hover:translate-y-0.5",
        blue:
          "bg-[var(--neo-blue)] text-[var(--neo-white)] hover:bg-[var(--neo-blue)]/90 hover:neo-shadow-hover hover:translate-x-0.5 hover:translate-y-0.5",
        outline:
          "bg-transparent border-current hover:bg-current hover:text-[var(--neo-bg-primary)] hover:neo-shadow-hover hover:translate-x-0.5 hover:translate-y-0.5",
        ghost:
          "border-transparent shadow-none hover:bg-current/10 hover:shadow-none",
        destructive:
          "bg-red-500 text-white hover:bg-red-600 hover:neo-shadow-hover hover:translate-x-0.5 hover:translate-y-0.5",
        link: 
          "text-current underline-offset-4 hover:underline border-transparent shadow-none",
      },
      size: {
        default: "h-12 px-6 py-3 has-[>svg]:px-4",
        sm: "h-10 px-4 py-2 text-xs has-[>svg]:px-3",
        lg: "h-16 px-8 py-4 text-base has-[>svg]:px-6",
        icon: "h-12 w-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
