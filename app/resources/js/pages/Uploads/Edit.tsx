import { Head, useForm } from '@inertiajs/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Form, FormMessage } from '@/components/ui/form';
import { useState } from 'react';

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
}

interface Props {
  upload: Upload;
}

export default function Edit({ upload }: Props) {
  const { data, setData, put, errors, processing } = useForm({
    title: upload.title,
    description: upload.description || '',
  });

  // Format file size to human-readable format
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    put(route('uploads.update', upload.id));
  };

  return (
    <>
      <Head title="Edit Upload" />

      <div className="py-12">
        <div className="max-w-7xl mx-auto sm:px-6 lg:px-8">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold text-gray-900">Edit Upload</h1>
          </div>

          <Card>
            <form onSubmit={handleSubmit}>
              <CardHeader>
                <CardTitle>Edit Audio Details</CardTitle>
                <CardDescription>
                  Update the details of your uploaded audio file
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
                  <Label>Current File</Label>
                  <div className="p-4 bg-gray-50 rounded-md">
                    <div className="flex items-center">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{upload.filename}</p>
                        <p className="text-sm text-gray-500">{upload.mime_type} • {formatFileSize(upload.size)}</p>
                      </div>

                      {upload.status === 'ready' && upload.stream_url && (
                        <div className="ml-4">
                          <audio controls className="h-8">
                            <source src={upload.stream_url} type={upload.mime_type} />
                          </audio>
                        </div>
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    To replace the file, please delete this upload and create a new one.
                  </p>
                </div>
              </CardContent>

              <CardFooter className="flex justify-between">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => window.history.back()}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={processing}>
                  {processing ? 'Saving...' : 'Save Changes'}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      </div>
    </>
  );
}
