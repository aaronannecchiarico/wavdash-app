import { Head, useForm, Link } from '@inertiajs/react';
import { LoaderCircle } from 'lucide-react';
import { FormEventHandler } from 'react';

import InputError from '@/components/input-error';
import { Button } from '@/components/ui/neo/button';
import { BrutalistInput } from '@/components/brutalist-input';
import { BrutalistLabel } from '@/components/brutalist-label';
import { BrutalistCheckbox } from '@/components/brutalist-checkbox';
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
                        <div className="flex items-center justify-between mb-2">
                            <BrutalistLabel htmlFor="password">PASSWORD</BrutalistLabel>
                            {canResetPassword && (
                                <Link 
                                    href={route('password.request')} 
                                    className="font-heading font-black text-xs uppercase tracking-wide text-foreground/70 hover:text-foreground transition-colors"
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
                        className="w-full bg-chart-1 text-main-foreground hover:bg-chart-2 font-heading font-black uppercase tracking-widest h-12" 
                        tabIndex={4} 
                        disabled={processing}
                    >
                        {processing && <LoaderCircle className="h-4 w-4 animate-spin mr-2" />}
                        {processing ? 'LOGGING IN...' : 'LOGIN TO FORGE'}
                    </Button>
                </div>

                <div className="text-center border-t-2 border-border pt-6">
                    <span className="font-base font-bold text-foreground/70 text-sm uppercase tracking-wide">
                        DON'T HAVE AN ACCOUNT?{' '}
                    </span>
                    <Link 
                        href={route('register')} 
                        className="font-heading font-black text-sm uppercase tracking-wide text-chart-1 hover:text-chart-2 transition-colors"
                        tabIndex={6}
                    >
                        SIGN UP
                    </Link>
                </div>
            </form>

            {status && (
                <div className="border-2 border-chart-1 bg-chart-1/20 p-3 text-center">
                    <span className="font-base font-bold text-foreground text-sm uppercase">{status}</span>
                </div>
            )}
        </BrutalistAuthLayout>
    );
}
