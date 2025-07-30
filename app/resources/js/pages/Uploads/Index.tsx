import { Head, usePage } from '@inertiajs/react';
import { Button } from '@/components/ui/button';
import { Link } from '@inertiajs/react';
import { Music, PlusIcon } from 'lucide-react';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { MusicCard, type Upload } from '@/components/music-library-card';
import { toast } from "sonner";
import { useEffect } from 'react';

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

export default function Index({ uploads }: Props) {
  const { flash } = usePage().props as any;

  useEffect(() => {
    if (flash?.success) {
      toast.success(flash.success);
    }

    if (flash?.error) {
      toast.error(flash.error);
    }
  }, [flash]);

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

