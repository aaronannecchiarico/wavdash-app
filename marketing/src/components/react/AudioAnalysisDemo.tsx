"use client"

import { useState } from "react"
import { BarVisualizer } from "@/components/ui/bar-visualizer"
import { StaticWaveform } from "@/components/ui/waveform"

export const AudioAnalysisDemo = () => {
  const [selectedStem, setSelectedStem] = useState<string | null>(null)

  // Static demo analysis results
  const analysisResults = {
    bpm: 128,
    key: "A Minor",
    timeSignature: "4/4",
    loudness: -14.2,
  }

  const stems = [
    { name: "VOCALS", color: "#00eb90", seed: 1 },
    { name: "DRUMS", color: "#ff73a9", seed: 2 },
    { name: "BASS", color: "#3f5ef4", seed: 3 },
    { name: "OTHER", color: "#ffdc00", seed: 4 },
  ]

  // Generate static waveform data (0-1 values)
  const waveformData = Array.from({ length: 80 }, (_, i) => {
    const seed = 42
    const x = Math.sin(seed + i * 0.1) * 10000
    return (x - Math.floor(x)) * 0.8 + 0.1
  })

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
      {/* Left: Interactive Waveform */}
      <div className="border-3 border-black bg-white neo-shadow p-6">
        <h3 className="text-xl font-black mb-4 uppercase tracking-wider">
          Audio Waveform
        </h3>
        <div className="bg-black p-4 mb-4">
          <StaticWaveform
            data={waveformData}
            bars={80}
            barColor="#00eb90"
            height={120}
            barWidth={4}
            barGap={3}
            fadeEdges={false}
          />
        </div>
        <div className="flex gap-4">
          <button className="flex-1 bg-[#00eb90] border-3 border-black px-6 py-3 font-black uppercase tracking-wider neo-shadow hover:neo-hover-lift neo-transition">
            Play Demo
          </button>
          <button className="flex-1 bg-white border-3 border-black px-6 py-3 font-black uppercase tracking-wider neo-shadow hover:neo-hover-lift neo-transition">
            Upload File
          </button>
        </div>
      </div>

      {/* Right: Analysis Results Panel */}
      <div className="border-3 border-black bg-white neo-shadow p-6">
        <h3 className="text-xl font-black mb-4 uppercase tracking-wider">
          Detected Properties
        </h3>
        <div className="space-y-4 mb-6">
          <div className="flex justify-between items-center pb-3 border-b-2 border-black">
            <span className="font-bold uppercase text-sm tracking-wide">
              BPM (Tempo)
            </span>
            <span className="text-2xl font-black" style={{ color: "#00eb90" }}>
              {analysisResults.bpm} BPM
            </span>
          </div>
          <div className="flex justify-between items-center pb-3 border-b-2 border-black">
            <span className="font-bold uppercase text-sm tracking-wide">
              Musical Key
            </span>
            <span className="text-2xl font-black" style={{ color: "#ff73a9" }}>
              {analysisResults.key}
            </span>
          </div>
          <div className="flex justify-between items-center pb-3 border-b-2 border-black">
            <span className="font-bold uppercase text-sm tracking-wide">
              Time Signature
            </span>
            <span className="text-2xl font-black" style={{ color: "#3f5ef4" }}>
              {analysisResults.timeSignature}
            </span>
          </div>
          <div className="flex justify-between items-center pb-3 border-b-2 border-black">
            <span className="font-bold uppercase text-sm tracking-wide">
              Loudness (LUFS)
            </span>
            <span className="text-2xl font-black" style={{ color: "#ffdc00" }}>
              {analysisResults.loudness} LUFS
            </span>
          </div>
        </div>

        {/* Stem Separation Preview */}
        <div className="mt-6">
          <h4 className="text-lg font-black mb-3 uppercase tracking-wide">
            Stem Separation
          </h4>
          <div className="bg-black p-4 mb-4">
            <BarVisualizer
              demo={true}
              barCount={20}
              state="speaking"
              centerAlign={true}
              className="bg-black"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            {stems.map((stem) => (
              <button
                key={stem.name}
                onClick={() =>
                  setSelectedStem(selectedStem === stem.name ? null : stem.name)
                }
                className={`border-3 border-black px-4 py-2 font-black text-sm uppercase tracking-wider neo-shadow neo-transition ${
                  selectedStem === stem.name
                    ? "neo-hover-lift"
                    : "hover:neo-hover-lift"
                }`}
                style={{
                  backgroundColor:
                    selectedStem === stem.name ? stem.color : "#fff",
                  color: selectedStem === stem.name ? "#000" : "#000",
                }}
              >
                {stem.name}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
