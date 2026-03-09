"use client"

import { useState, useEffect, useRef, useMemo } from "react"
import { motion, useInView } from "motion/react"

// ── Count-up hook ──────────────────────────────────────────────────
function useCountUp(target: number, duration: number, trigger: boolean) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    if (!trigger) return
    let startTime: number | null = null
    const tick = (ts: number) => {
      if (startTime === null) startTime = ts
      const progress = Math.min((ts - startTime) / (duration * 1000), 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(target * eased)
      if (progress < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [trigger, target, duration])
  return value
}

// ── Design tokens ─────────────────────────────────────────────────
const STEMS = [
  { id: "vocals", label: "Vocals", color: "#E8A83E", bg: "rgba(232,168,62,0.08)", border: "rgba(232,168,62,0.22)", seed: 7  },
  { id: "drums",  label: "Drums",  color: "#7BAFD4", bg: "rgba(123,175,212,0.08)", border: "rgba(123,175,212,0.22)", seed: 13 },
  { id: "bass",   label: "Bass",   color: "#A78BFA", bg: "rgba(167,139,250,0.08)", border: "rgba(167,139,250,0.22)", seed: 19 },
  { id: "guitar", label: "Guitar", color: "#8B5CF6", bg: "rgba(139,92,246,0.08)",  border: "rgba(139,92,246,0.22)",  seed: 23 },
  { id: "piano",  label: "Piano",  color: "#FB7185", bg: "rgba(251,113,133,0.08)", border: "rgba(251,113,133,0.22)", seed: 29 },
  { id: "other",  label: "Other",  color: "#F87171", bg: "rgba(248,113,113,0.08)", border: "rgba(248,113,113,0.22)", seed: 31 },
]

const MAC_DOTS = ["#FF5F57", "#FEBC2E", "#28C840"]

// ── Stem waveform strip ────────────────────────────────────────────
interface StemBarProps { color: string; seed: number; isActive: boolean }

function StemBar({ color, seed, isActive }: StemBarProps) {
  const bars = useMemo(() => Array.from({ length: 30 }, (_, i) => {
    const x = Math.sin(seed * 11 + i * 0.38) * 10000
    const h  = Math.max(0.08, (x - Math.floor(x)) * 0.82 + 0.1)
    const h2 = Math.max(0.08, Math.min(1, h + Math.sin(seed + i * 0.7) * 0.35))
    return { h, h2 }
  }), [seed])

  return (
    <div className="flex items-center gap-[1.5px] w-full" style={{ height: "36px" }}>
      {bars.map(({ h, h2 }, i) => (
        <motion.div
          key={i}
          className="flex-1 rounded-[1px]"
          style={{ backgroundColor: color, height: "100%", transformOrigin: "center" }}
          animate={isActive
            ? { scaleY: [h, h2, h], opacity: [0.55, 1, 0.55] }
            : { scaleY: h, opacity: 0.15 }
          }
          transition={isActive
            ? { duration: 0.48 + (i % 7) * 0.08, repeat: Infinity, ease: "easeInOut", delay: i * 0.024 }
            : { duration: 0.38 }
          }
        />
      ))}
    </div>
  )
}

// ── Spectrum bar (memoized stable values) ─────────────────────────
interface SpectrumBarProps { h: number; h2: number; color: string; delay: number }

function SpectrumBar({ h, h2, color, delay }: SpectrumBarProps) {
  return (
    <motion.div
      className="flex-1 rounded-t-[1px]"
      style={{ backgroundColor: color, height: "100%", transformOrigin: "bottom" }}
      animate={{ scaleY: [h, h2, h], opacity: [0.45, 0.9, 0.45] }}
      transition={{ duration: 0.28 + delay * 2.8, repeat: Infinity, ease: "easeInOut", delay: delay * 0.35 }}
    />
  )
}

// ── Main component ─────────────────────────────────────────────────
export const AudioAnalysisDemo = () => {
  const [activeStem, setActiveStem]   = useState("vocals")
  const [isPlaying,  setIsPlaying]    = useState(false)
  const [playhead,   setPlayhead]     = useState(0)

  const ref      = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: "-80px" })

  const bpm  = useCountUp(128,  1.6, isInView)
  const lufs = useCountUp(14.2, 1.4, isInView)

  // Playhead ticker
  useEffect(() => {
    if (!isPlaying) return
    const id = setInterval(() => setPlayhead(p => p >= 99.4 ? 0 : p + 0.35), 35)
    return () => clearInterval(id)
  }, [isPlaying])

  // Stable waveform data
  const waveform = useMemo(() => Array.from({ length: 100 }, (_, i) => {
    const x = Math.sin(42 + i * 0.27) * 10000
    return Math.max(0.07, (x - Math.floor(x)) * 0.86 + 0.08)
  }), [])

  // Stable spectrum data
  const spectrum = useMemo(() => Array.from({ length: 52 }, (_, i) => {
    const f    = i / 52
    const base = Math.exp(-Math.pow((f - 0.12) * 3.5, 2)) * 0.88
               + Math.exp(-Math.pow((f - 0.30) * 4.0, 2)) * 0.60
               + Math.exp(-Math.pow((f - 0.65) * 6.0, 2)) * 0.34
               + Math.exp(-Math.pow((f - 0.85) * 8.0, 2)) * 0.18
    const h    = Math.max(0.04, Math.min(0.94, base + Math.sin(i * 0.9) * 0.07))
    const h2   = Math.max(0.04, Math.min(0.94, h    + Math.sin(i * 1.3 + 1) * 0.16))
    return { h, h2 }
  }), [])

  const activeColor = STEMS.find(s => s.id === activeStem)?.color ?? "#E8A83E"

  const handlePlayToggle = () => {
    const next = !isPlaying
    setIsPlaying(next)
    if (!next) setPlayhead(0)
  }

  const elapsedSec = Math.round((playhead / 100) * 192)

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 44 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.85, ease: [0.22, 1, 0.36, 1] }}
      className="relative overflow-hidden"
      style={{
        borderRadius: "18px",
        background: "linear-gradient(158deg, #141210 0%, #0F0E0D 55%, #0C0B09 100%)",
        border: "1px solid rgba(255,255,255,0.07)",
        boxShadow: [
          "0 48px 120px rgba(0,0,0,0.55)",
          "0 0 0 1px rgba(200,137,42,0.07)",
          "inset 0 1px 0 rgba(255,255,255,0.07)",
        ].join(", "),
      }}
    >
      {/* Ambient amber glow */}
      <div className="absolute pointer-events-none" style={{
        top: 0, left: 0, width: "280px", height: "200px",
        background: "radial-gradient(ellipse at 15% 0%, rgba(200,137,42,0.09) 0%, transparent 70%)",
      }} />
      <div className="absolute pointer-events-none" style={{
        bottom: 0, right: 0, width: "220px", height: "180px",
        background: "radial-gradient(ellipse at 85% 100%, rgba(61,196,166,0.06) 0%, transparent 70%)",
      }} />

      {/* ── Window chrome ── */}
      <div
        className="flex items-center justify-between px-5 pt-4 pb-3"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            {MAC_DOTS.map(c => (
              <div key={c} className="w-2.5 h-2.5 rounded-full" style={{ background: c }} />
            ))}
          </div>
          <span
            className="text-xs font-mono tracking-wide"
            style={{ color: "rgba(255,255,255,0.22)", fontFamily: "var(--font-mono)" }}
          >
            wavdash analyzer — demo_track.mp3
          </span>
        </div>
        <div className="flex items-center gap-2">
          <motion.div
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: "#28C840" }}
            animate={{ opacity: [1, 0.25, 1] }}
            transition={{ duration: 2.2, repeat: Infinity }}
          />
          <span
            className="text-[10px] font-mono tracking-widest uppercase"
            style={{ color: "rgba(255,255,255,0.22)", fontFamily: "var(--font-mono)" }}
          >
            analysis complete
          </span>
        </div>
      </div>

      {/* ── Waveform panel ── */}
      <div className="px-5 pt-4 pb-3">
        {/* Time ruler */}
        <div className="flex justify-between mb-1.5 px-0.5">
          {["0:00", "0:38", "1:16", "1:54", "2:32", "3:12"].map(t => (
            <span
              key={t}
              className="text-[9px] font-mono"
              style={{ color: "rgba(255,255,255,0.16)", fontFamily: "var(--font-mono)" }}
            >
              {t}
            </span>
          ))}
        </div>

        {/* Waveform canvas area */}
        <div
          className="relative rounded-xl overflow-hidden cursor-pointer select-none"
          style={{ height: "92px", background: "rgba(0,0,0,0.28)", border: "1px solid rgba(255,255,255,0.04)" }}
          onClick={handlePlayToggle}
        >
          {/* Vertical grid */}
          {[16.66, 33.33, 50, 66.66, 83.33].map(p => (
            <div
              key={p}
              className="absolute inset-y-0 w-px"
              style={{ left: `${p}%`, background: "rgba(255,255,255,0.03)" }}
            />
          ))}
          {/* Centre line */}
          <div
            className="absolute left-0 right-0"
            style={{ top: "50%", height: "1px", background: "rgba(255,255,255,0.04)" }}
          />

          {/* Bars */}
          <div className="absolute inset-0 flex items-center gap-[1.5px] px-2">
            {waveform.map((h, i) => {
              const barPct  = (i / waveform.length) * 100
              const isPast  = barPct < playhead && isPlaying
              const isNear  = Math.abs(barPct - playhead) < 2.5 && isPlaying
              return (
                <div
                  key={i}
                  suppressHydrationWarning
                  className="flex-1 rounded-[1px]"
                  style={{
                    height: `${Math.round(h * 10000) / 100}%`,
                    background: isPast
                      ? isNear ? "rgba(232,168,62,1)" : "rgba(232,168,62,0.65)"
                      : "rgba(255,255,255,0.13)",
                    boxShadow: isNear ? "0 0 6px rgba(232,168,62,0.5)" : "none",
                    transition: "background 0.06s linear",
                  }}
                />
              )
            })}
          </div>

          {/* Playhead */}
          {isPlaying && (
            <div
              className="absolute inset-y-0 w-[2px] rounded-full"
              style={{
                left: `${playhead}%`,
                background: "rgba(232,168,62,0.95)",
                boxShadow: "0 0 14px rgba(232,168,62,0.75), 0 0 4px rgba(232,168,62,1)",
              }}
            />
          )}

          {/* Click-to-play hint (idle state) */}
          {!isPlaying && (
            <div
              className="absolute inset-0 flex items-center justify-center gap-2 text-[11px] font-mono"
              style={{ color: "rgba(255,255,255,0.2)", fontFamily: "var(--font-mono)" }}
            >
              <svg width="11" height="13" viewBox="0 0 11 13" fill="rgba(232,168,62,0.5)">
                <polygon points="0,0 11,6.5 0,13" />
              </svg>
              click to play demo
            </div>
          )}
        </div>

        {/* Transport + key stat strip */}
        <div className="flex items-center gap-4 mt-3 flex-wrap">
          {/* Play/stop button */}
          <button
            onClick={handlePlayToggle}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-[11px] font-mono font-medium transition-all shrink-0"
            style={{
              background: isPlaying ? "rgba(232,168,62,0.1)" : "rgba(232,168,62,0.92)",
              color: isPlaying ? "#E8A83E" : "#0D0C0B",
              border: "1px solid rgba(232,168,62,0.3)",
              fontFamily: "var(--font-mono)",
            }}
          >
            {isPlaying ? (
              <>
                <svg width="9" height="9" viewBox="0 0 9 9" fill="currentColor">
                  <rect x="0" y="0" width="3.5" height="9" rx="0.5"/>
                  <rect x="5.5" y="0" width="3.5" height="9" rx="0.5"/>
                </svg>
                STOP
              </>
            ) : (
              <>
                <svg width="9" height="10" viewBox="0 0 9 10" fill="currentColor">
                  <polygon points="0,0 9,5 0,10"/>
                </svg>
                PLAY
              </>
            )}
          </button>

          <div className="h-6 w-px shrink-0" style={{ background: "rgba(255,255,255,0.07)" }} />

          {/* Key metrics */}
          <div className="flex items-center gap-5 flex-1 flex-wrap">
            {[
              { label: "BPM",  value: Math.round(bpm).toString(), color: "#E8A83E" },
              { label: "KEY",  value: "A min",                    color: "#7BAFD4" },
              { label: "SIG",  value: "4 / 4",                    color: "rgba(255,255,255,0.55)" },
              { label: "LUFS", value: `−${lufs.toFixed(1)}`,      color: "#A78BFA" },
            ].map(({ label, value, color }) => (
              <div key={label} className="flex flex-col leading-none">
                <span
                  className="text-[9px] font-mono uppercase tracking-widest mb-1"
                  style={{ color: "rgba(255,255,255,0.22)", fontFamily: "var(--font-mono)" }}
                >
                  {label}
                </span>
                <span
                  className="text-lg font-mono font-semibold tabular-nums"
                  style={{ color, fontFamily: "var(--font-mono)", lineHeight: 1 }}
                >
                  {value}
                </span>
              </div>
            ))}
          </div>

          {/* Elapsed / duration */}
          <span
            className="text-[11px] font-mono shrink-0"
            style={{ color: "rgba(255,255,255,0.2)", fontFamily: "var(--font-mono)" }}
          >
            {isPlaying ? `${Math.floor(elapsedSec / 60)}:${String(elapsedSec % 60).padStart(2, "0")}` : "3:12"}
          </span>
        </div>
      </div>

      {/* Full-width rule */}
      <div style={{ height: "1px", background: "rgba(255,255,255,0.05)" }} />

      {/* ── Bottom panels ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5">
        {/* Stems — 3 cols */}
        <div
          className="lg:col-span-3 p-5"
          style={{ borderRight: "1px solid rgba(255,255,255,0.05)" }}
        >
          <div
            className="text-[9px] font-mono tracking-widest uppercase mb-3.5"
            style={{ color: "rgba(255,255,255,0.22)", fontFamily: "var(--font-mono)" }}
          >
            Stem Separation — tap to isolate
          </div>

          <div className="space-y-1.5">
            {STEMS.map(stem => {
              const active = activeStem === stem.id
              return (
                <motion.button
                  key={stem.id}
                  onClick={() => setActiveStem(stem.id)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left"
                  style={{
                    background: active ? stem.bg : "rgba(255,255,255,0.015)",
                    border: `1px solid ${active ? stem.border : "rgba(255,255,255,0.05)"}`,
                  }}
                  whileHover={{ scale: 1.006 }}
                  whileTap ={{ scale: 0.996 }}
                  transition={{ type: "spring", stiffness: 420, damping: 32 }}
                >
                  {/* Dot + label */}
                  <div className="flex items-center gap-2 w-[4.5rem] shrink-0">
                    <motion.div
                      className="w-[7px] h-[7px] rounded-full shrink-0"
                      style={{ background: stem.color }}
                      animate={{ boxShadow: active
                        ? [`0 0 0px ${stem.color}00`, `0 0 8px ${stem.color}`, `0 0 0px ${stem.color}00`]
                        : `0 0 0px ${stem.color}00`
                      }}
                      transition={{ duration: 1.6, repeat: Infinity }}
                    />
                    <span
                      className="text-[11px] font-mono font-medium"
                      style={{
                        color: active ? stem.color : "rgba(255,255,255,0.32)",
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      {stem.label}
                    </span>
                  </div>

                  {/* Animated waveform */}
                  <div className="flex-1 min-w-0">
                    <StemBar color={stem.color} seed={stem.seed} isActive={active} />
                  </div>

                  {/* Badge */}
                  <div className="shrink-0 w-16 text-right">
                    {active && (
                      <span
                        className="text-[9px] font-mono tracking-widest px-1.5 py-[3px] rounded"
                        style={{
                          background: stem.bg,
                          color: stem.color,
                          border: `1px solid ${stem.border}`,
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        ISOLATED
                      </span>
                    )}
                  </div>
                </motion.button>
              )
            })}
          </div>
        </div>

        {/* Spectrum + stats — 2 cols */}
        <div className="lg:col-span-2 p-5">
          <div
            className="text-[9px] font-mono tracking-widest uppercase mb-3.5"
            style={{ color: "rgba(255,255,255,0.22)", fontFamily: "var(--font-mono)" }}
          >
            Frequency Spectrum
          </div>

          {/* Spectrum display */}
          <div
            className="relative rounded-xl overflow-hidden mb-3"
            style={{ height: "78px", background: "rgba(0,0,0,0.22)", border: "1px solid rgba(255,255,255,0.04)" }}
          >
            <div className="absolute inset-x-2 bottom-4 top-2 flex items-end gap-[1.5px]">
              {spectrum.map(({ h, h2 }, i) => (
                <SpectrumBar
                  key={i}
                  h={h}
                  h2={h2}
                  color={activeColor}
                  delay={i / spectrum.length}
                />
              ))}
            </div>
            {/* Freq labels */}
            <div className="absolute bottom-0 inset-x-1 flex justify-between pb-[3px]">
              {["20", "200", "2k", "20k"].map(f => (
                <span
                  key={f}
                  className="text-[8px] font-mono"
                  style={{ color: "rgba(255,255,255,0.14)", fontFamily: "var(--font-mono)" }}
                >
                  {f}
                </span>
              ))}
            </div>
          </div>

          {/* Detail stat grid */}
          <div className="grid grid-cols-2 gap-1.5">
            {[
              { label: "Dyn. Range",   value: "12.4 dB",  color: "#E8A83E" },
              { label: "True Peak",    value: "−0.8 dBTP", color: "#7BAFD4" },
              { label: "Crest Factor", value: "8.2 dB",   color: "#A78BFA" },
              { label: "Spectral Flux",value: "High",     color: "#F87171" },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                className="px-2.5 py-2 rounded-lg"
                style={{ background: "rgba(255,255,255,0.018)", border: "1px solid rgba(255,255,255,0.05)" }}
              >
                <div
                  className="text-[9px] font-mono uppercase tracking-wide mb-0.5"
                  style={{ color: "rgba(255,255,255,0.2)", fontFamily: "var(--font-mono)" }}
                >
                  {label}
                </div>
                <div
                  className="text-xs font-mono font-semibold"
                  style={{ color, fontFamily: "var(--font-mono)" }}
                >
                  {value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Footer status bar ── */}
      <div
        className="flex items-center justify-between px-5 py-2.5"
        style={{ borderTop: "1px solid rgba(255,255,255,0.05)", background: "rgba(0,0,0,0.18)" }}
      >
        <span
          className="text-[9px] font-mono tracking-widest uppercase"
          style={{ color: "rgba(255,255,255,0.16)", fontFamily: "var(--font-mono)" }}
        >
          MP3 · 320 kbps · 44.1 kHz · Stereo
        </span>
        <div className="flex items-center gap-3">
          <span
            className="text-[9px] font-mono tracking-widest uppercase"
            style={{ color: "rgba(255,255,255,0.16)", fontFamily: "var(--font-mono)" }}
          >
            Analyzed in 2.3 s
          </span>
          <div className="flex items-center gap-1.5">
            <div className="w-[5px] h-[5px] rounded-full" style={{ background: "#28C840" }} />
            <span
              className="text-[9px] font-mono tracking-widest uppercase"
              style={{ color: "rgba(255,255,255,0.16)", fontFamily: "var(--font-mono)" }}
            >
              WavDash AI
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
