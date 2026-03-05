import { Head, Link, useForm } from '@inertiajs/react';
import { LoaderCircle } from 'lucide-react';
import { FormEventHandler } from 'react';

import { BrutalistCheckbox } from '@/components/brutalist-checkbox';
import { BrutalistInput } from '@/components/brutalist-input';
import { BrutalistLabel } from '@/components/brutalist-label';
import InputError from '@/components/input-error';
import { Button } from '@/components/ui/button';
import BrutalistAuthLayout from '@/layouts/brutalist-auth-layout';

type LoginForm = {
    email: string;
    password: string;
    remember: boolean;
};

interface LoginProps {
    status?: string;
    canResetPassword: boolean;
}

export default function Login({ status, canResetPassword }: LoginProps) {
    const { data, setData, post, processing, errors, reset } = useForm<Required<LoginForm>>({
        email: '',
        password: '',
        remember: false,
    });

    const submit: FormEventHandler = (e) => {
        e.preventDefault();
        post(route('login'), {
            onFinish: () => reset('password'),
        });
    };

    return (
        <BrutalistAuthLayout title="LOGIN TO THE FORGE" description="ENTER YOUR CREDENTIALS TO ACCESS THE BEATS">
            <Head title="Log in" />

            <form className="space-y-6" onSubmit={submit}>
                <div className="space-y-4">
                    <div>
                        <BrutalistLabel htmlFor="email">EMAIL ADDRESS</BrutalistLabel>
                        <BrutalistInput
                            id="email"
                            type="email"
                            required
                            autoFocus
                            tabIndex={1}
                            autoComplete="email"
                            value={data.email}
                            onChange={(e) => setData('email', e.target.value)}
                            placeholder="EMAIL@EXAMPLE.COM"
                            hasError={!!errors.email}
                        />
                        <InputError message={errors.email} />
                    </div>

                    <div>
                        <div className="mb-2 flex items-center justify-between">
                            <BrutalistLabel htmlFor="password">PASSWORD</BrutalistLabel>
                            {canResetPassword && (
                                <Link
                                    href={route('password.request')}
                                    className="font-heading text-xs font-black tracking-wide text-foreground/70 uppercase transition-colors hover:text-foreground"
                                    tabIndex={5}
                                >
                                    FORGOT PASSWORD?
                                </Link>
                            )}
                        </div>
                        <BrutalistInput
                            id="password"
                            type="password"
                            required
                            tabIndex={2}
                            autoComplete="current-password"
                            value={data.password}
                            onChange={(e) => setData('password', e.target.value)}
                            placeholder="PASSWORD"
                            hasError={!!errors.password}
                        />
                        <InputError message={errors.password} />
                    </div>

                    <div className="pt-2">
                        <BrutalistCheckbox
                            id="remember"
                            name="remember"
                            checked={data.remember}
                            onClick={() => setData('remember', !data.remember)}
                            tabIndex={3}
                            label="REMEMBER ME"
                        />
                    </div>

                    <Button
                        type="submit"
                        className="h-12 w-full bg-chart-1 font-heading font-black tracking-widest text-main-foreground uppercase hover:bg-chart-2"
                        tabIndex={4}
                        disabled={processing}
                    >
                        {processing && <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />}
                        {processing ? 'LOGGING IN...' : 'LOGIN TO FORGE'}
                    </Button>
                </div>

                <div className="border-t-2 border-border pt-6 text-center">
                    <span className="text-sm font-base font-bold tracking-wide text-foreground/70 uppercase">DON'T HAVE AN ACCOUNT? </span>
                    <Link
                        href={route('register')}
                        className="font-heading text-sm font-black tracking-wide text-chart-1 uppercase transition-colors hover:text-chart-2"
                        tabIndex={6}
                    >
                        SIGN UP
                    </Link>
                </div>
            </form>

            {status && (
                <div className="border-2 border-chart-1 bg-chart-1/20 p-3 text-center">
                    <span className="text-sm font-base font-bold text-foreground uppercase">{status}</span>
                </div>
            )}
        </BrutalistAuthLayout>
    );
}
