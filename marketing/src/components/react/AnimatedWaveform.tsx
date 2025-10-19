import { Play, Pause, SkipBack, SkipForward, Volume2, Repeat, Shuffle } from 'lucide-react';
import { useState } from 'react';

export function AnimatedWaveform() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(33); // 0-100

  // Generate 60 bars for better visual density
  const bars = Array.from({ length: 60 }, (_, i) => ({
    id: i,
    height: Math.random() * 70 + 15, // 15% to 85% height
    delay: Math.random() * 2.5,
  }));

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="border-3 border-black bg-white neo-shadow-lg overflow-hidden">
      {/* Track Info Header */}
      <div className="border-b-3 border-black bg-[#ffdc00] p-6 md:p-8">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="uppercase tracking-wider mb-2">
              Demo Track
            </h3>
            <p className="uppercase tracking-wider opacity-70">
              WavDash • AI Audio Processing
            </p>
          </div>
          <div className="flex gap-3">
            <button className="border-3 border-black bg-white w-12 h-12 flex items-center justify-center neo-shadow-sm neo-transition neo-hover-lift">
              <Shuffle size={20} />
            </button>
            <button className="border-3 border-black bg-white w-12 h-12 flex items-center justify-center neo-shadow-sm neo-transition neo-hover-lift">
              <Repeat size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Waveform Visualization */}
      <div className="bg-black p-8 md:p-12 relative">
        {/* Waveform Container */}
        <div className="relative h-48 md:h-64 mb-8">
          {/* Playhead indicator */}
          <div
            className="absolute top-0 bottom-0 w-1 bg-[#ff73a9] z-10 transition-all duration-300"
            style={{ left: `${progress}%` }}
          >
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-full mb-2">
              <div className="border-3 border-[#ff73a9] bg-[#ff73a9] w-4 h-4 rotate-45"></div>
            </div>
          </div>

          {/* Waveform bars */}
          <div className="flex items-end justify-center gap-1 h-full">
            {bars.map((bar, index) => {
              const barProgress = (index / bars.length) * 100;
              const isPassed = barProgress < progress;

              return (
                <div
                  key={bar.id}
                  className={`flex-1 max-w-2 transition-colors duration-300 cursor-pointer hover:opacity-80 ${
                    isPlaying ? 'pulse-bar' : ''
                  }`}
                  style={{
                    height: `${bar.height}%`,
                    animationDelay: `${bar.delay}s`,
                    backgroundColor: isPassed ? '#ff73a9' : '#00eb90',
                  }}
                  onClick={() => setProgress(barProgress)}
                />
              );
            })}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="border-3 border-white bg-white/10 h-3 relative overflow-hidden cursor-pointer group">
            <div
              className="h-full bg-[#00eb90] transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
            {/* Hover indicator */}
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="h-full bg-white/20" />
            </div>
          </div>
          <div className="flex justify-between mt-3 text-white">
            <span className="uppercase tracking-wider">{formatTime(103)}</span>
            <span className="uppercase tracking-wider">{formatTime(225)}</span>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="border-t-3 border-black bg-[#3f5ef4] p-6 md:p-8">
        <div className="flex items-center justify-between gap-6">
          {/* Volume Control */}
          <div className="hidden md:flex items-center gap-4 flex-1">
            <button className="border-3 border-black bg-white w-12 h-12 flex items-center justify-center neo-shadow-sm neo-transition neo-hover-lift">
              <Volume2 size={20} />
            </button>
            <div className="border-3 border-black bg-white w-32 h-3">
              <div className="w-3/4 h-full bg-[#00eb90]"></div>
            </div>
          </div>

          {/* Main Controls */}
          <div className="flex items-center justify-center gap-4">
            <button className="border-3 border-black bg-white w-14 h-14 flex items-center justify-center neo-shadow neo-transition neo-hover-lift">
              <SkipBack size={24} />
            </button>

            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="border-3 border-black bg-[#00eb90] w-16 h-16 flex items-center justify-center neo-shadow neo-transition neo-hover-lift"
            >
              {isPlaying ? (
                <Pause size={28} fill="currentColor" />
              ) : (
                <Play size={28} fill="currentColor" className="ml-1" />
              )}
            </button>

            <button className="border-3 border-black bg-white w-14 h-14 flex items-center justify-center neo-shadow neo-transition neo-hover-lift">
              <SkipForward size={24} />
            </button>
          </div>

          {/* Spacer for alignment */}
          <div className="hidden md:block flex-1"></div>
        </div>
      </div>
    </div>
  );
}
