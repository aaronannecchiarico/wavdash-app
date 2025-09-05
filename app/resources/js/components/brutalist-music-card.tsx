import { Badge } from '@/components/ui/neo/badge';
import { Card, CardContent } from '@/components/ui/neo/card';
import { type Upload } from '@/types';
import { formatDistance } from 'date-fns';
import { router } from '@inertiajs/react';
import { Music, Scissors, BarChart3, Clock, Gauge } from 'lucide-react';

interface BrutalistMusicCardProps {
  upload: Upload;
}

export function BrutalistMusicCard({ upload }: BrutalistMusicCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-chart-1'; // neo-green
      case 'processing':
        return 'bg-chart-3'; // neo-yellow  
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-chart-4'; // neo-blue
    }
  };

  return (
    <Card 
      className="cursor-pointer transition-all hover:translate-x-2 hover:translate-y-2"
      onClick={() => router.visit(`/uploads/${upload.id}?from=dashboard`)}
    >
      {/* Status Header */}
      <div className={`${getStatusColor(upload.status)} p-3 border-b-2 border-border flex justify-between items-center`}>
        <div className="flex items-center space-x-2">
          <Music className="w-4 h-4 text-main-foreground" />
          <span className="font-heading font-black text-xs uppercase tracking-widest text-main-foreground">
            {upload.filename.split('.').pop()?.toUpperCase()}
          </span>
        </div>
        <div className="font-heading font-black text-xs uppercase tracking-widest text-main-foreground">
          {upload.status.toUpperCase()}
        </div>
      </div>

      {/* Waveform Visualization */}
      <div className="p-4 bg-border">
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

      <CardContent className="p-4 space-y-3">
        <div>
          <h3 className="font-heading font-black text-lg uppercase tracking-wide text-foreground mb-1">
            {upload.title}
          </h3>
          <p className="font-base text-sm opacity-70">
            {upload.description && upload.description}
          </p>
        </div>

        {/* Feature Badges */}
        <div className="flex flex-wrap gap-1">
          {upload.has_analysis && (
            <Badge className="text-xs font-black uppercase">
              <BarChart3 className="mr-1 h-3 w-3" />
              ANALYZED
            </Badge>
          )}
          {upload.has_stems && (
            <Badge className="text-xs font-black uppercase">
              <Scissors className="mr-1 h-3 w-3" />
              STEMS
            </Badge>
          )}
          {upload.has_tempos && (
            <Badge className="text-xs font-black uppercase">
              <Gauge className="mr-1 h-3 w-3" />
              TEMPO FX
            </Badge>
          )}
        </div>

        {/* Footer with timestamp */}
        <div className="border-t-2 border-border bg-border p-3 -mb-4 -mx-4 flex justify-between items-center">
          <div className="text-xs font-base text-foreground uppercase">
            {formatDistance(new Date(upload.created_at), new Date(), { addSuffix: true }).toUpperCase()}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="size-3" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}