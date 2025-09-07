import { type Upload } from '@/types';
import { router } from '@inertiajs/react';
import { 
  formatFileSize, 
  formatDuration, 
  formatDate,
  getAudioFormat, 
} from '@/lib/formatters';
import { BrutalistDropdownMenu } from '@/components/brutalist-dropdown-menu';

interface BrutalistMusicCardProps {
  upload: Upload;
  isLast?: boolean;
  lastElementRef?: (node: HTMLDivElement | null) => void;
}

export function BrutalistMusicCard({ upload, isLast, lastElementRef }: BrutalistMusicCardProps) {
  const statusColors = {
    ready: 'bg-chart-1', // neo-green
    processing: 'bg-chart-3', // neo-yellow
    failed: 'bg-red-500',
    pending: 'bg-chart-4' // neo-blue
  }

  return (
    <div
      ref={isLast ? lastElementRef : null}
      className="border-2 border-border shadow-shadow bg-background hover:shadow-none hover:translate-x-boxShadowX hover:translate-y-boxShadowY transition-all cursor-pointer"
      onClick={() => router.visit(route('uploads.show', upload.id))}
    >
      {/* Status Header */}
      <div className={`${statusColors[upload.status as keyof typeof statusColors]} p-3 border-b-2 border-border flex justify-between items-center`}>
        <div className="flex items-center space-x-2">
          <span className="font-heading font-black text-xs uppercase tracking-widest text-main-foreground">
            {getAudioFormat(upload.mime_type)}
          </span>
        </div>
        <div className="font-heading font-black text-xs uppercase tracking-widest text-main-foreground">
          {upload.status.toUpperCase()}
        </div>
      </div>

      {/* Waveform Visualization */}
      <div className="p-4 bg-main-foreground">
        <div className="flex items-center justify-center space-x-1 h-16">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="w-1 bg-chart-1 animate-pulse"
              style={{
                height: `${20 + Math.random() * 40}px`,
                animationDelay: `${i * 0.1}s`,
                animationDuration: '2s'
              }}
            />
          ))}
        </div>
      </div>

      {/* Track Info */}
      <div className="p-4 space-y-3">
        <div>
          <h3 className="font-heading font-black text-lg uppercase tracking-wide text-foreground mb-1">
            {upload.title}
          </h3>
          {upload.artist && (
            <p className="font-base font-bold text-sm text-foreground/70">
              BY {upload.artist.toUpperCase()}
            </p>
          )}
        </div>

        {/* Technical Specs */}
        <div className="grid grid-cols-2 gap-2">
          <div className="border-2 border-border bg-chart-3/20 p-2">
            <div className="text-xs font-heading font-black uppercase text-foreground">
              DURATION
            </div>
            <div className="font-mono font-bold text-foreground">
              {formatDuration(upload.duration || 0)}
            </div>
          </div>
          <div className="border-2 border-border bg-chart-2/20 p-2">
            <div className="text-xs font-heading font-black uppercase text-foreground">
              SIZE
            </div>
            <div className="font-mono font-bold text-foreground">
              {formatFileSize(upload.size)}
            </div>
          </div>
        </div>

        {/* Feature Badges */}
        <div className="flex flex-wrap gap-1">
          {upload.has_analysis && (
            <div className="border-2 border-border bg-chart-1 px-2 py-1">
              <span className="text-xs font-heading font-black text-main-foreground">ANALYZED</span>
            </div>
          )}
          {upload.has_stems && (
            <div className="border-2 border-border bg-chart-2 px-2 py-1">
              <span className="text-xs font-heading font-black text-main-foreground">STEMS</span>
            </div>
          )}
          {upload.has_tempos && (
            <div className="border-2 border-border bg-chart-4 px-2 py-1">
              <span className="text-xs font-heading font-black text-main-foreground">TEMPO FX</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="border-t-2 border-border bg-border p-3 flex justify-between items-center">
        <div className="text-xs font-mono text-foreground">
          {formatDate(upload.created_at).toUpperCase()}
        </div>
        <BrutalistDropdownMenu upload={upload} />
      </div>
    </div>
  )
}