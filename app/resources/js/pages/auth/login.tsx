import { Head, Link, useForm } from '@inertiajs/react';
import { LoaderCircle } from 'lucide-react';
import { FormEventHandler } from 'react';

import InputError from '@/components/input-error';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import AuthSplitLayout from '@/layouts/auth/auth-split-layout';

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
        <AuthSplitLayout title="Sign in to WavDash" description="Enter your credentials to access your account">
            <Head title="Log in" />

            <form className="space-y-5" onSubmit={submit}>
                <div className="space-y-1.5">
                    <Label htmlFor="email">Email address</Label>
                    <Input
                        id="email"
                        type="email"
                        required
                        autoFocus
                        tabIndex={1}
                        autoComplete="email"
                        value={data.email}
                        onChange={(e) => setData('email', e.target.value)}
                        placeholder="you@example.com"
                        className={errors.email ? 'border-destructive focus-visible:border-destructive' : ''}
                    />
                    <InputError message={errors.email} />
                </div>

                <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                        <Label htmlFor="password">Password</Label>
                        {canResetPassword && (
                            <Link
                                href={route('password.request')}
                                className="text-xs text-[--amber] hover:underline"
                                tabIndex={5}
                            >
                                Forgot password?
                            </Link>
                        )}
                    </div>
                    <Input
                        id="password"
                        type="password"
                        required
                        tabIndex={2}
                        autoComplete="current-password"
                        value={data.password}
                        onChange={(e) => setData('password', e.target.value)}
                        placeholder="Your password"
                        className={errors.password ? 'border-destructive focus-visible:border-destructive' : ''}
                    />
                    <InputError message={errors.password} />
                </div>

                <div className="flex items-center gap-2 pt-1">
                    <Checkbox
                        id="remember"
                        checked={data.remember}
                        onCheckedChange={(checked) => setData('remember', !!checked)}
                        tabIndex={3}
                    />
                    <Label htmlFor="remember" className="cursor-pointer font-normal text-muted-foreground">
                        Remember me
                    </Label>
                </div>

                <Button
                    type="submit"
                    className="w-full"
                    tabIndex={4}
                    disabled={processing}
                >
                    {processing && <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />}
                    {processing ? 'Signing in...' : 'Sign in'}
                </Button>
            </form>

            {status && (
                <div className="rounded-[--radius-md] bg-green-50 border border-green-200 p-3 text-center dark:bg-green-900/20 dark:border-green-800">
                    <span className="text-sm text-green-700 dark:text-green-400">{status}</span>
                </div>
            )}

            <p className="text-center text-sm text-muted-foreground">
                Don't have an account?{' '}
                <Link
                    href={route('register')}
                    className="text-[--amber] hover:underline font-medium"
                    tabIndex={6}
                >
                    Sign up
                </Link>
            </p>
        </AuthSplitLayout>
    );
}
