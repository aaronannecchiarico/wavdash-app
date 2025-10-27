import { useEffect, useState } from "react"
import { Toaster as Sonner, ToasterProps } from "sonner"

const BrutalistToaster = ({ ...props }: ToasterProps) => {
  const [theme, setTheme] = useState<"light" | "dark" | "system">("system")

  // Detect the theme from the document
  useEffect(() => {
    const isDark = document.documentElement.classList.contains("dark")
    setTheme(isDark ? "dark" : "light")

    // Set up an observer to watch for theme changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === "class") {
          const isDark = document.documentElement.classList.contains("dark")
          setTheme(isDark ? "dark" : "light")
        }
      })
    })

    observer.observe(document.documentElement, { attributes: true })

    return () => observer.disconnect()
  }, [])

  return (
    <Sonner
      theme={theme}
      className="toaster group"
      position="top-right"
      expand={true}
      richColors={false}
      closeButton={false}
      style={
        {
          "--normal-bg": "var(--chart-1)",
          "--normal-border": "var(--border)",
          "--normal-text": "var(--main-foreground)",
          "--success-bg": "var(--chart-1)",
          "--success-border": "var(--border)",
          "--success-text": "var(--main-foreground)",
          "--info-bg": "var(--chart-4)",
          "--info-border": "var(--border)",
          "--info-text": "var(--main-foreground)",
          "--warning-bg": "var(--chart-3)",
          "--warning-border": "var(--border)",
          "--warning-text": "var(--main-foreground)",
          "--error-bg": "#ef4444",
          "--error-border": "var(--border)",
          "--error-text": "var(--main-foreground)",
          "--border-radius": "0px",
          "--width": "420px",
          "--height": "auto",
          "--font-family": "var(--font-heading)",
        } as React.CSSProperties
      }
      toastOptions={{
        style: {
          border: "2px solid var(--border)",
          boxShadow: "var(--shadow)",
          fontSize: "14px",
          fontWeight: "700",
          textTransform: "uppercase" as const,
          letterSpacing: "0.05em",
          fontFamily: "var(--font-heading)",
          padding: "16px",
          borderRadius: "0px",
        },
        className: "brutalist-toast",
      }}
      {...props}
    />
  )
}

export { BrutalistToaster }