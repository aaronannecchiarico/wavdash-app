import { Head } from '@inertiajs/react';
import { Button } from '@/components/ui/button';
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Link } from '@inertiajs/react';
import { Music, Play, Download, Clock, User, Calendar, Volume2, PlusIcon } from 'lucide-react';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';

interface Upload {
  id: number;
  title: string;
  description: string | null;
  filename: string;
  mime_type: string;
  size: number;
  status: string;
  stream_url: string | null;
  created_at: string;
  updated_at: string;
  user: {
    id: number;
    name: string;
  };
  artist?: string;
  duration?: number;
  genre?: string;
  bitrate?: number;
}

interface Props {
  uploads: {
    data: Upload[];
    links: any;
  };
}

// Helper function to format file size
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

// Helper function to format duration
const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, "0")}`
}

// Helper function to format date
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

// Helper function to get audio format from mime type
const getAudioFormat = (mimeType: string): string => {
  const formats: { [key: string]: string } = {
    "audio/mpeg": "MP3",
    "audio/wav": "WAV",
    "audio/flac": "FLAC",
    "audio/aac": "AAC",
    "audio/ogg": "OGG",
    "audio/m4a": "M4A",
    "audio/wma": "WMA",
  }
  return formats[mimeType] || "AUDIO"
}

// Helper function to get status color
const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case "completed":
    case "success":
    case "ready":
      return "bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300 dark:hover:bg-green-900/40"
    case "processing":
    case "pending":
      return "bg-yellow-100 text-yellow-800 hover:bg-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-300 dark:hover:bg-yellow-900/40"
    case "failed":
    case "error":
      return "bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-300 dark:hover:bg-red-900/40"
    default:
      return "bg-gray-100 text-gray-800 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
  }
}

// Individual music upload card component
const MusicCard = ({
  upload,
  isLast,
  lastElementRef,
}: {
  upload: Upload
  isLast: boolean
  lastElementRef?: (node: HTMLDivElement | null) => void
}) => {
  return (
    <Card
      ref={isLast ? lastElementRef : null}
      className="group hover:shadow-lg transition-all duration-200 hover:-translate-y-1 cursor-pointer"
      onClick={() => window.location.href = route('uploads.show', upload.id)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="text-xs dark:text-gray-300 dark:border-gray-600">
              {getAudioFormat(upload.mime_type)}
            </Badge>
            <Badge className={getStatusColor(upload.status)}>
              {upload.status.charAt(0).toUpperCase() + upload.status.slice(1)}
            </Badge>
          </div>
          <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {upload.stream_url && (
              <Button variant="ghost" size="sm" onClick={(e) => {
                e.stopPropagation();
                // Play audio functionality could be added here
              }}>
                <Play className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={(e) => {
              e.stopPropagation();
              window.location.href = route('uploads.edit', upload.id);
            }}>
              <Download className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Music Visualization */}
        <div className="aspect-square bg-gradient-to-br from-white to-blue-100 dark:from-slate-800 dark:to-blue-950 rounded-lg flex items-center justify-center overflow-hidden">
          <div className="flex flex-col items-center justify-center">
            <Music className="w-12 h-12 mb-2 text-blue-500 dark:text-blue-400" />
            <div className="flex items-center space-x-1">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className={`w-1 rounded-full bg-blue-400/70 dark:bg-blue-500/70 animate-pulse`}
                  style={{
                    height: `${15 + Math.floor(Math.random() * 20)}px`,
                    animationDelay: `${i * 0.1}s`
                  }}
                ></div>
              ))}
            </div>
          </div>
        </div>

        {/* Music Info */}
        <div className="space-y-2">
          <h3 className="font-semibold text-lg leading-tight line-clamp-1 dark:text-white">{upload.title}</h3>
          {upload.artist && <p className="text-sm text-gray-600 dark:text-gray-300 font-medium line-clamp-1">by {upload.artist}</p>}
          {upload.description && <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{upload.description}</p>}
        </div>

        {/* Technical Details */}
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-500 dark:text-gray-400">
          {upload.duration && (
            <div className="flex items-center space-x-1">
              <Clock className="w-3 h-3 text-gray-400 dark:text-gray-500" />
              <span>{formatDuration(upload.duration)}</span>
            </div>
          )}
          <div className="flex items-center space-x-1">
            <Volume2 className="w-3 h-3 text-gray-400 dark:text-gray-500" />
            <span>{formatFileSize(upload.size)}</span>
          </div>
          {upload.bitrate && (
            <div className="flex items-center space-x-1">
              <span className="text-xs text-gray-400 dark:text-gray-500">♪</span>
              <span>{upload.bitrate} kbps</span>
            </div>
          )}
          {upload.genre && (
            <div className="flex items-center space-x-1">
              <span className="text-xs text-gray-400 dark:text-gray-500">#</span>
              <span className="truncate">{upload.genre}</span>
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="pt-0">
        <div className="flex items-center justify-between w-full text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center space-x-1">
            <User className="w-3 h-3 text-gray-400 dark:text-gray-500" />
            <span className="truncate">{upload.user.name}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Calendar className="w-3 h-3 text-gray-400 dark:text-gray-500" />
            <span>{formatDate(upload.created_at)}</span>
          </div>
        </div>
      </CardFooter>
    </Card>
  )
}

export default function Index({ uploads }: Props) {
  // Estimate total duration for display purposes (since we don't have actual duration in the data)
  const estimatedTotalDuration = uploads.data.reduce((acc, upload) =>
    acc + (upload.duration || Math.floor(upload.size / 10000)), 0);
  const totalSize = uploads.data.reduce((acc, upload) => acc + upload.size, 0);

  const breadcrumbs: BreadcrumbItem[] = [
    {
      title: 'Music Library',
      href: route('uploads.index'),
      description: `${uploads.data.length} ${uploads.data.length === 1 ? "track" : "tracks"} • ${formatDuration(estimatedTotalDuration)} total • ${formatFileSize(totalSize)}`
    },
  ];

  return (
    <AppLayout breadcrumbs={breadcrumbs}>
      <Head title="Music Library" />
        <Link href={route('uploads.create')}>
            <Button
                className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600 shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105 z-50 p-0"
                size="lg"
            >
                <PlusIcon className="w-6 h-6" />
            </Button>
        </Link>
      <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4 overflow-x-auto">
        {uploads.data.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-white to-blue-100 dark:from-slate-800/50 dark:to-blue-900/30 rounded-full flex items-center justify-center mb-4">
              <Music className="w-8 h-8 text-blue-500 dark:text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No music files found</h3>
            <p className="text-gray-500 dark:text-gray-400 max-w-sm">
              {"You haven't uploaded any audio files yet. Upload some tracks to get started."}
            </p>
            <div className="mt-6">
              <Link href={route('uploads.create')}>
                <Button className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600">
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Upload Your First Beat
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {uploads.data.map((upload, index) => (
                <MusicCard
                  key={upload.id}
                  upload={upload}
                  isLast={index === uploads.data.length - 1}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}

