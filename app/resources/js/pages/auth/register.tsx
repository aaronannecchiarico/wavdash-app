import { Head, Link, useForm } from '@inertiajs/react';
import { LoaderCircle } from 'lucide-react';
import { FormEventHandler } from 'react';

import InputError from '@/components/input-error';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import AuthSplitLayout from '@/layouts/auth/auth-split-layout';

type RegisterForm = {
    name: string;
    email: string;
    password: string;
    password_confirmation: string;
};

export default function Register() {
    const { data, setData, post, processing, errors, reset } = useForm<Required<RegisterForm>>({
        name: '',
        email: '',
        password: '',
        password_confirmation: '',
    });

    const submit: FormEventHandler = (e) => {
        e.preventDefault();
        post(route('register'), {
            onFinish: () => reset('password', 'password_confirmation'),
        });
    };

    return (
        <AuthSplitLayout title="Create your account" description="Start analyzing your tracks in seconds">
            <Head title="Register" />
            <form className="space-y-5" onSubmit={submit}>
                <div className="space-y-1.5">
                    <Label htmlFor="name">Full name</Label>
                    <Input
                        id="name"
                        type="text"
                        required
                        autoFocus
                        tabIndex={1}
                        autoComplete="name"
                        value={data.name}
                        onChange={(e) => setData('name', e.target.value)}
                        disabled={processing}
                        placeholder="Your full name"
                        className={errors.name ? 'border-destructive focus-visible:border-destructive' : ''}
                    />
                    <InputError message={errors.name} />
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="email">Email address</Label>
                    <Input
                        id="email"
                        type="email"
                        required
                        tabIndex={2}
                        autoComplete="email"
                        value={data.email}
                        onChange={(e) => setData('email', e.target.value)}
                        disabled={processing}
                        placeholder="you@example.com"
                        className={errors.email ? 'border-destructive focus-visible:border-destructive' : ''}
                    />
                    <InputError message={errors.email} />
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="password">Password</Label>
                    <Input
                        id="password"
                        type="password"
                        required
                        tabIndex={3}
                        autoComplete="new-password"
                        value={data.password}
                        onChange={(e) => setData('password', e.target.value)}
                        disabled={processing}
                        placeholder="Create a strong password"
                        className={errors.password ? 'border-destructive focus-visible:border-destructive' : ''}
                    />
                    <InputError message={errors.password} />
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="password_confirmation">Confirm password</Label>
                    <Input
                        id="password_confirmation"
                        type="password"
                        required
                        tabIndex={4}
                        autoComplete="new-password"
                        value={data.password_confirmation}
                        onChange={(e) => setData('password_confirmation', e.target.value)}
                        disabled={processing}
                        placeholder="Confirm your password"
                        className={errors.password_confirmation ? 'border-destructive focus-visible:border-destructive' : ''}
                    />
                    <InputError message={errors.password_confirmation} />
                </div>

                <Button
                    type="submit"
                    className="w-full"
                    tabIndex={5}
                    disabled={processing}
                >
                    {processing && <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />}
                    {processing ? 'Creating account...' : 'Create account'}
                </Button>
            </form>

            <p className="text-center text-sm text-muted-foreground">
                Already have an account?{' '}
                <Link
                    href={route('login')}
                    className="text-[--amber] hover:underline font-medium"
                    tabIndex={6}
                >
                    Sign in
                </Link>
            </p>
        </AuthSplitLayout>
    );
}
