import { Badge } from '@/components/ui/neo/badge';
import { Button } from '@/components/ui/neo/button';
import { Card, CardContent } from '@/components/ui/neo/card';
import { NeoProgressBar } from '@/components/ui/neo/progress-bar';
import { type Upload } from '@/types';
import { formatDistance } from 'date-fns';
import { router, Link } from '@inertiajs/react';
import { 
  Music, 
  Scissors, 
  BarChart3, 
  Clock, 
  Gauge,
  HardDrive,
  FileAudio,
  User,
  Tag,
  Play,
  Settings,
  Download
} from 'lucide-react';
import { 
  formatFileSize, 
  formatDuration, 
  formatBitrate, 
  getAudioFormat, 
  getProcessingProgress 
} from '@/lib/format-utils';

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

  const processingInfo = getProcessingProgress(upload);

  const handleCardClick = (e: React.MouseEvent) => {
    // Prevent navigation when clicking on buttons
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    router.visit(`/uploads/${upload.id}?from=dashboard`);
  };

  return (
    <Card 
      className="cursor-pointer transition-all hover:translate-x-2 hover:translate-y-2"
      onClick={handleCardClick}
    >
      {/* Enhanced Status Header */}
      <div className={`${getStatusColor(upload.status)} p-3 border-b-2 border-border flex justify-between items-center`}>
        <div className="flex items-center space-x-3">
          <FileAudio className="w-5 h-5 text-main-foreground" />
          <span className="font-heading font-black text-sm uppercase tracking-widest text-main-foreground">
            {getAudioFormat(upload.mime_type)}
          </span>
          {processingInfo && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-main-foreground rounded-full animate-pulse" />
              <span className="font-heading font-black text-xs uppercase text-main-foreground">
                PROCESSING {processingInfo.type.toUpperCase()}
              </span>
            </div>
          )}
        </div>
        <div className="font-heading font-black text-sm uppercase tracking-widest text-main-foreground">
          {upload.status.toUpperCase()}
        </div>
      </div>

      <CardContent className="p-0">
        {/* Track Information Section */}
        <div className="p-4 border-b-2 border-border">
          <div className="space-y-2">
            <h3 className="font-heading font-black text-xl uppercase tracking-wide text-foreground">
              {upload.title}
            </h3>
            <div className="flex items-center space-x-4 text-sm">
              {upload.artist && (
                <div className="flex items-center space-x-1">
                  <User className="w-4 h-4" />
                  <span className="font-base font-bold uppercase">{upload.artist}</span>
                </div>
              )}
              {upload.genre && (
                <div className="flex items-center space-x-1">
                  <Tag className="w-4 h-4" />
                  <span className="font-base font-bold uppercase">{upload.genre}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Technical Specs Grid */}
        <div className="p-4 border-b-2 border-border bg-secondary-background/20">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4 text-chart-1" />
                <span className="text-xs font-heading font-black uppercase">Duration</span>
              </div>
              <span className="font-mono font-bold text-lg">
                {formatDuration(upload.duration || 0)}
              </span>
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <HardDrive className="w-4 h-4 text-chart-2" />
                <span className="text-xs font-heading font-black uppercase">Size</span>
              </div>
              <span className="font-mono font-bold text-lg">
                {formatFileSize(upload.size)}
              </span>
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <Gauge className="w-4 h-4 text-chart-4" />
                <span className="text-xs font-heading font-black uppercase">Bitrate</span>
              </div>
              <span className="font-mono font-bold text-lg">
                {upload.bitrate ? formatBitrate(upload.bitrate) : 'Unknown'}
              </span>
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <FileAudio className="w-4 h-4 text-chart-3" />
                <span className="text-xs font-heading font-black uppercase">Format</span>
              </div>
              <span className="font-mono font-bold text-lg">
                {getAudioFormat(upload.mime_type)}
              </span>
            </div>
          </div>
        </div>

        {/* Processing Status */}
        {processingInfo && (
          <div className="p-4 border-b-2 border-border">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-heading font-black text-sm uppercase">
                  {processingInfo.type} IN PROGRESS
                </span>
                <span className="font-mono font-bold text-sm">
                  {processingInfo.progress}%
                </span>
              </div>
              <NeoProgressBar 
                value={processingInfo.progress} 
                max={100}
                color="bg-chart-1"
              />
            </div>
          </div>
        )}

        {/* Features Available */}
        <div className="p-4 border-b-2 border-border">
          <div className="flex flex-wrap gap-2">
            {upload.has_analysis ? (
              <Badge className="bg-chart-1 text-main-foreground font-black uppercase text-xs">
                <BarChart3 className="mr-1 h-3 w-3" />
                ANALYZED
              </Badge>
            ) : (
              <Badge variant="outline" className="font-black uppercase text-xs opacity-50">
                <BarChart3 className="mr-1 h-3 w-3" />
                ANALYSIS
              </Badge>
            )}
            
            {upload.has_stems ? (
              <Badge className="bg-chart-2 text-main-foreground font-black uppercase text-xs">
                <Scissors className="mr-1 h-3 w-3" />
                STEMS READY
              </Badge>
            ) : (
              <Badge variant="outline" className="font-black uppercase text-xs opacity-50">
                <Scissors className="mr-1 h-3 w-3" />
                STEMS
              </Badge>
            )}
            
            {upload.has_tempos ? (
              <Badge className="bg-chart-4 text-main-foreground font-black uppercase text-xs">
                <Gauge className="mr-1 h-3 w-3" />
                TEMPO FX
              </Badge>
            ) : (
              <Badge variant="outline" className="font-black uppercase text-xs opacity-50">
                <Gauge className="mr-1 h-3 w-3" />
                TEMPO FX
              </Badge>
            )}
          </div>
        </div>

        {/* Quick Actions Footer */}
        <div className="p-4 bg-border flex justify-between items-center">
          <div className="text-xs font-base text-foreground uppercase">
            {formatDistance(new Date(upload.created_at), new Date(), { addSuffix: true }).toUpperCase()}
          </div>
          
          <div className="flex items-center space-x-2">
            {upload.stream_url && (
              <Button 
                size="sm" 
                variant="outline" 
                className="font-black uppercase text-xs"
                onClick={(e) => {
                  e.stopPropagation();
                  // Handle play action
                }}
              >
                <Play className="w-3 h-3 mr-1" />
                PLAY
              </Button>
            )}
            
            <Button 
              size="sm" 
              variant="outline" 
              className="font-black uppercase text-xs"
              asChild
            >
              <Link href={`/uploads/${upload.id}?from=dashboard`}>
                <Settings className="w-3 h-3 mr-1" />
                MANAGE
              </Link>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}