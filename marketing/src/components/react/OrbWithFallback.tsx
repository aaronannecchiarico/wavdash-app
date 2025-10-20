"use client"

import { useEffect, useState } from "react"
import { Orb, type AgentState } from "@/components/ui/orb"

export interface OrbWithFallbackProps {
  colors?: [string, string]
  agentState?: AgentState
  volumeMode?: "auto" | "manual"
  className?: string
}

/**
 * Orb component with mobile fallback
 * Shows static gradient on mobile devices to avoid performance issues
 */
export const OrbWithFallback = ({
  colors = ["#00eb90", "#ff73a9"],
  agentState = "thinking",
  volumeMode = "auto",
  className,
}: OrbWithFallbackProps) => {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    // Detect mobile devices
    const checkMobile = () => {
      const mobile = window.matchMedia("(max-width: 768px)").matches
      setIsMobile(mobile)
    }

    checkMobile()
    window.addEventListener("resize", checkMobile)

    return () => window.removeEventListener("resize", checkMobile)
  }, [])

  if (isMobile) {
    // Static gradient fallback for mobile
    return (
      <div
        className={className ?? "relative h-full w-full"}
        style={{
          background: `radial-gradient(circle at center, ${colors[0]} 0%, ${colors[1]} 70%, transparent 100%)`,
          opacity: 0.3,
        }}
        aria-label="Audio visualization (static)"
      />
    )
  }

  // Full 3D Orb for desktop
  return (
    <Orb
      colors={colors}
      agentState={agentState}
      volumeMode={volumeMode}
      className={className}
    />
  )
}
