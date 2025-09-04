import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const cardVariants = cva(
  "neo-border neo-shadow bg-card text-card-foreground flex flex-col",
  {
    variants: {
      variant: {
        default: "bg-[var(--neo-bg-primary)] dark:bg-[var(--neo-black)]",
        accent: "bg-[var(--neo-yellow)]",
        secondary: "bg-[var(--neo-pink)]/10 dark:bg-[var(--neo-pink)]/20",
        green: "bg-[var(--neo-green)]/10 dark:bg-[var(--neo-green)]/20",
        blue: "bg-[var(--neo-blue)]/10 dark:bg-[var(--neo-blue)]/20",
      },
      size: {
        default: "gap-6 p-6",
        sm: "gap-4 p-4", 
        lg: "gap-8 p-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Card({ 
  className, 
  variant,
  size,
  ...props 
}: React.ComponentProps<"div"> & VariantProps<typeof cardVariants>) {
  return (
    <div
      data-slot="card"
      className={cn(cardVariants({ variant, size, className }))}
      {...props}
    />
  )
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-header"
      className={cn("flex flex-col gap-1.5 px-6", className)}
      {...props}
    />
  )
}

function CardTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-title"
      className={cn("leading-none font-black uppercase tracking-wider", className)}
      {...props}
    />
  )
}

function CardDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-description"
      className={cn("text-muted-foreground text-sm font-bold", className)}
      {...props}
    />
  )
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-content"
      className={cn("px-6", className)}
      {...props}
    />
  )
}

function CardFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-footer"
      className={cn("flex items-center px-6", className)}
      {...props}
    />
  )
}

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
