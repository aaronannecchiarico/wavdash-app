import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import * as React from "react"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap text-sm font-medium ring-offset-background transition-all duration-200 gap-2 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground rounded-[--radius-md] shadow-sm-studio hover:scale-[1.01] hover:shadow-md-studio active:scale-[0.99]",
        secondary:
          "bg-card text-foreground border border-[--border-strong] rounded-[--radius-md] shadow-sm-studio hover:scale-[1.01] hover:shadow-md-studio active:scale-[0.99]",
        ghost:
          "rounded-[--radius-md] hover:bg-muted hover:text-foreground",
        destructive:
          "bg-destructive text-destructive-foreground rounded-[--radius-md] shadow-sm-studio hover:scale-[1.01]",
        outline:
          "border border-[--border-strong] bg-transparent text-foreground rounded-[--radius-md] hover:bg-muted",
        link:
          "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm:      "h-8 px-3 text-xs",
        lg:      "h-11 px-8",
        xl:      "h-14 px-10 text-base",
        icon:    "size-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
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
