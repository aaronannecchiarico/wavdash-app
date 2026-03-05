import { Button } from '@/components/ui/button';
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogTitle } from '@/components/ui/dialog';
import { Upload } from '@/types';
import { useForm } from '@inertiajs/react';
import { Loader2, Trash2 } from 'lucide-react';
import { FormEventHandler, MouseEvent } from 'react';

interface DeleteUploadDialogProps {
    upload: Upload;
    isOpen: boolean;
    onOpenChange: (isOpen: boolean) => void;
}

export function DeleteUploadDialog({ upload, isOpen, onOpenChange }: DeleteUploadDialogProps) {
    const { delete: destroy, processing, reset, clearErrors } = useForm();

    const closeDeleteModal = () => {
        clearErrors();
        reset();
        onOpenChange(false);
    };

    const deleteUpload: FormEventHandler = (e) => {
        e.preventDefault();
        e.stopPropagation();
        destroy(route('uploads.destroy', upload.id), {
            preserveScroll: true,
            onSuccess: () => closeDeleteModal(),
        });
    };

    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
            <DialogContent onClick={(e: MouseEvent) => e.stopPropagation()} className="dark:border-slate-700">
                <DialogTitle className="flex items-center">
                    <Trash2 className="mr-2 h-5 w-5 text-red-500 dark:text-red-400" />
                    Are you sure you want to delete this upload?
                </DialogTitle>
                <DialogDescription>Once this upload is deleted, it will be permanently gone. This action cannot be undone.</DialogDescription>
                <form onSubmit={deleteUpload} className="pt-4">
                    <DialogFooter className="gap-2">
                        <DialogClose asChild>
                            <Button type="button" variant="secondary" onClick={closeDeleteModal}>
                                Cancel
                            </Button>
                        </DialogClose>

                        <Button variant="outline" disabled={processing}>
                            {processing ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Deleting...
                                </>
                            ) : (
                                'Delete Upload'
                            )}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
