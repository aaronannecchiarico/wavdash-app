import { type BreadcrumbItem, type SharedData } from '@/types';
import { Transition } from '@headlessui/react';
import { Head, Link, useForm, usePage } from '@inertiajs/react';
import { CheckCircle, Save } from 'lucide-react';
import { FormEventHandler } from 'react';

import DeleteUser from '@/components/delete-user';
import InputError from '@/components/input-error';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import AppLayout from '@/layouts/app-layout';
import SettingsLayout from '@/layouts/settings/layout';

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Profile settings',
        href: '/settings/profile',
    },
];

type ProfileForm = {
    name: string;
    email: string;
};

export default function Profile({ mustVerifyEmail, status }: { mustVerifyEmail: boolean; status?: string }) {
    const { auth } = usePage<SharedData>().props;

    const { data, setData, patch, errors, processing, recentlySuccessful } = useForm<Required<ProfileForm>>({
        name: auth.user.name,
        email: auth.user.email,
    });

    const submit: FormEventHandler = (e) => {
        e.preventDefault();

        patch(route('profile.update'), {
            preserveScroll: true,
        });
    };

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Profile settings" />

            <SettingsLayout>
                <div className="space-y-8">
                    {/* Header */}
                    <div className="border-b border-[--border] pb-6">
                        <h2 className="font-sans text-lg font-semibold text-foreground mb-1">Profile information</h2>
                        <p className="text-sm text-muted-foreground">Update your name and email address</p>
                    </div>

                    <form onSubmit={submit} className="space-y-5 max-w-md">
                        <div className="space-y-1.5">
                            <Label htmlFor="name">Full name</Label>
                            <Input
                                id="name"
                                value={data.name}
                                onChange={(e) => setData('name', e.target.value)}
                                required
                                autoComplete="name"
                                placeholder="Your full name"
                                className={errors.name ? 'border-destructive' : ''}
                            />
                            <InputError message={errors.name} />
                        </div>

                        <div className="space-y-1.5">
                            <Label htmlFor="email">Email address</Label>
                            <Input
                                id="email"
                                type="email"
                                value={data.email}
                                onChange={(e) => setData('email', e.target.value)}
                                required
                                autoComplete="username"
                                placeholder="you@example.com"
                                className={errors.email ? 'border-destructive' : ''}
                            />
                            <InputError message={errors.email} />
                        </div>

                        {mustVerifyEmail && auth.user.email_verified_at === null && (
                            <div className="rounded-[--radius-md] border border-amber-200 bg-amber-50 p-4 dark:bg-amber-900/20 dark:border-amber-800">
                                <p className="mb-2 text-sm font-medium text-amber-800 dark:text-amber-300">Email not verified</p>
                                <p className="mb-3 text-sm text-amber-700 dark:text-amber-400">
                                    Your email address is unverified.{' '}
                                    <Link
                                        href={route('verification.send')}
                                        method="post"
                                        as="button"
                                        className="font-medium text-[--amber] underline hover:text-foreground"
                                    >
                                        Click to resend verification email
                                    </Link>
                                </p>

                                {status === 'verification-link-sent' && (
                                    <div className="rounded-[--radius-sm] bg-green-50 border border-green-200 p-3 dark:bg-green-900/20 dark:border-green-800">
                                        <span className="text-sm text-green-700 dark:text-green-400">
                                            Verification email sent to your address.
                                        </span>
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="flex items-center gap-4 pt-2">
                            <Button disabled={processing}>
                                <Save className="mr-2 h-4 w-4" />
                                {processing ? 'Saving...' : 'Save changes'}
                            </Button>

                            <Transition
                                show={recentlySuccessful}
                                enter="transition ease-in-out"
                                enterFrom="opacity-0"
                                leave="transition ease-in-out"
                                leaveTo="opacity-0"
                            >
                                <div className="flex items-center gap-2">
                                    <CheckCircle className="h-4 w-4 text-green-600" />
                                    <span className="text-sm text-green-700 dark:text-green-400">Saved</span>
                                </div>
                            </Transition>
                        </div>
                    </form>

                    {/* Danger Zone */}
                    <div className="border-t border-[--border] pt-8">
                        <div className="rounded-[--radius-lg] border border-destructive/20 bg-destructive/5 p-6">
                            <h3 className="font-sans text-base font-semibold text-destructive mb-1">
                                Delete account
                            </h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Permanently delete your account and all associated data.
                            </p>
                            <DeleteUser />
                        </div>
                    </div>
                </div>
            </SettingsLayout>
        </AppLayout>
    );
}
