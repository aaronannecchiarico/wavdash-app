import { Head, useForm } from '@inertiajs/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Form, FormMessage } from '@/components/ui/form';
import { useState, ChangeEvent } from 'react';
import { UploadCloud } from 'lucide-react';

interface UploadForm {
  title: string;
  description: string;
  audio_file: File | null;
}

export default function Create() {
  const { data, setData, post, errors, processing } = useForm<UploadForm>({
    title: '',
    description: '',
    audio_file: null,
  });

  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>('');
  const [fileSize, setFileSize] = useState<string>('');

  // Format file size to human-readable format
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setData('audio_file', file);
      setFileName(file.name);
      setFileSize(formatFileSize(file.size));

      // Create a preview URL for audio file
      const url = URL.createObjectURL(file);
      setFilePreview(url);

      // If title is empty, use filename (without extension) as default title
      if (!data.title) {
        const nameWithoutExtension = file.name.replace(/\.[^/.]+$/, '');
        setData('title', nameWithoutExtension);
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post(route('uploads.store'), {
      forceFormData: true,
    });
  };

  return (
    <>
      <Head title="Upload Audio" />

      <div className="py-12">
        <div className="max-w-7xl mx-auto sm:px-6 lg:px-8">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold text-gray-900">Upload Audio</h1>
          </div>

          <Card>
            <form onSubmit={handleSubmit}>
              <CardHeader>
                <CardTitle>Audio Details</CardTitle>
                <CardDescription>
                  Upload an audio file to use in beats and contests
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="title">Title</Label>
                  <Input
                    id="title"
                    type="text"
                    value={data.title}
                    onChange={(e) => setData('title', e.target.value)}
                  />
                  {errors.title && <FormMessage>{errors.title}</FormMessage>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description (optional)</Label>
                  <Textarea
                    id="description"
                    value={data.description}
                    onChange={(e) => setData('description', e.target.value)}
                    rows={3}
                  />
                  {errors.description && <FormMessage>{errors.description}</FormMessage>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="audio_file">Audio File</Label>
                  <div className="flex items-center justify-center w-full">
                    <label
                      htmlFor="audio_file"
                      className="flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100"
                    >
                      <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <UploadCloud className="w-10 h-10 mb-3 text-gray-400" />
                        {fileName ? (
                          <div className="text-center">
                            <p className="mb-2 text-sm font-semibold text-gray-900">{fileName}</p>
                            <p className="text-xs text-gray-500">{fileSize}</p>
                          </div>
                        ) : (
                          <div className="text-center">
                            <p className="mb-2 text-sm text-gray-500">
                              <span className="font-semibold">Click to upload</span> or drag and drop
                            </p>
                            <p className="text-xs text-gray-500">MP3, WAV, AIFF or FLAC (max. 50MB)</p>
                          </div>
                        )}
                      </div>
                      <input
                        id="audio_file"
                        type="file"
                        className="hidden"
                        accept="audio/mpeg,audio/wav,audio/aiff,audio/flac,audio/ogg"
                        onChange={handleFileChange}
                      />
                    </label>
                  </div>
                  {errors.audio_file && <FormMessage>{errors.audio_file}</FormMessage>}
                </div>

                {filePreview && (
                  <div className="mt-4">
                    <audio controls className="w-full">
                      <source src={filePreview} />
                      Your browser does not support the audio element.
                    </audio>
                  </div>
                )}
              </CardContent>

              <CardFooter className="flex justify-between">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => window.history.back()}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={processing || !data.audio_file}>
                  {processing ? 'Uploading...' : 'Upload'}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      </div>
    </>
  );
}
