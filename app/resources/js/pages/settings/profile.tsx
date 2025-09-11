import { type BreadcrumbItem, type SharedData } from '@/types';
import { Transition } from '@headlessui/react';
import { Head, Link, useForm, usePage } from '@inertiajs/react';
import { CheckCircle, Save } from 'lucide-react';
import { FormEventHandler } from 'react';

import { BrutalistInput } from '@/components/brutalist-input';
import { BrutalistLabel } from '@/components/brutalist-label';
import DeleteUser from '@/components/delete-user';
import InputError from '@/components/input-error';
import { Button } from '@/components/ui/neo/button';
import AppLayout from '@/layouts/app-layout';
import BrutalistSettingsLayout from '@/layouts/brutalist-settings-layout';

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

            <BrutalistSettingsLayout>
                <div className="space-y-8">
                    {/* Header */}
                    <div className="border-b-2 border-border pb-6">
                        <h2 className="mb-2 font-heading text-xl font-black tracking-widest text-foreground uppercase">PROFILE INFORMATION</h2>
                        <p className="text-sm font-base font-bold tracking-wide text-foreground/70 uppercase">UPDATE YOUR NAME AND EMAIL ADDRESS</p>
                    </div>

                    <form onSubmit={submit} className="space-y-6">
                        <div>
                            <BrutalistLabel htmlFor="name">FULL NAME</BrutalistLabel>
                            <BrutalistInput
                                id="name"
                                value={data.name}
                                onChange={(e) => setData('name', e.target.value)}
                                required
                                autoComplete="name"
                                placeholder="YOUR FULL NAME"
                                hasError={!!errors.name}
                            />
                            <InputError message={errors.name} />
                        </div>

                        <div>
                            <BrutalistLabel htmlFor="email">EMAIL ADDRESS</BrutalistLabel>
                            <BrutalistInput
                                id="email"
                                type="email"
                                value={data.email}
                                onChange={(e) => setData('email', e.target.value)}
                                required
                                autoComplete="username"
                                placeholder="EMAIL@EXAMPLE.COM"
                                hasError={!!errors.email}
                            />
                            <InputError message={errors.email} />
                        </div>

                        {mustVerifyEmail && auth.user.email_verified_at === null && (
                            <div className="border-2 border-red-500 bg-red-50 p-4">
                                <p className="mb-2 text-sm font-base font-bold tracking-wide text-red-800 uppercase">EMAIL NOT VERIFIED</p>
                                <p className="mb-3 text-sm font-base font-bold text-red-700">
                                    Your email address is unverified.{' '}
                                    <Link
                                        href={route('verification.send')}
                                        method="post"
                                        as="button"
                                        className="font-heading font-black tracking-wide text-red-800 uppercase underline hover:text-red-900"
                                    >
                                        CLICK TO RESEND VERIFICATION EMAIL
                                    </Link>
                                </p>

                                {status === 'verification-link-sent' && (
                                    <div className="border-2 border-green-500 bg-green-50 p-3">
                                        <span className="text-sm font-base font-bold text-green-800 uppercase">
                                            VERIFICATION EMAIL SENT TO YOUR ADDRESS
                                        </span>
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="flex items-center gap-4 pt-4">
                            <Button
                                disabled={processing}
                                className="bg-chart-1 px-6 font-heading font-black tracking-widest text-main-foreground uppercase hover:bg-chart-2"
                            >
                                <Save className="mr-2 h-4 w-4" />
                                {processing ? 'SAVING...' : 'SAVE CHANGES'}
                            </Button>

                            <Transition
                                show={recentlySuccessful}
                                enter="transition ease-in-out"
                                enterFrom="opacity-0"
                                leave="transition ease-in-out"
                                leaveTo="opacity-0"
                            >
                                <div className="flex items-center gap-2 border-2 border-green-500 bg-green-50 px-3 py-2">
                                    <CheckCircle className="h-4 w-4 text-green-700" />
                                    <span className="font-heading text-sm font-black tracking-wide text-green-800 uppercase">SAVED</span>
                                </div>
                            </Transition>
                        </div>
                    </form>

                    {/* Danger Zone */}
                    <div className="border-t-2 border-border pt-8">
                        <div className="border-2 border-red-500 bg-red-50 p-6 dark:bg-red-900/20">
                            <h3 className="mb-2 font-heading text-lg font-black tracking-widest text-red-800 uppercase dark:text-red-200">
                                DANGER ZONE
                            </h3>
                            <p className="mb-4 text-sm font-base font-bold tracking-wide text-red-700 uppercase dark:text-red-300">
                                DELETE YOUR ACCOUNT PERMANENTLY
                            </p>
                            <DeleteUser />
                        </div>
                    </div>
                </div>
            </BrutalistSettingsLayout>
        </AppLayout>
    );
}
