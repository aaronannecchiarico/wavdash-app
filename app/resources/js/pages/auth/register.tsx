import { Head, Link, useForm } from '@inertiajs/react';
import { LoaderCircle } from 'lucide-react';
import { FormEventHandler } from 'react';

import { BrutalistInput } from '@/components/brutalist-input';
import { BrutalistLabel } from '@/components/brutalist-label';
import InputError from '@/components/input-error';
import { Button } from '@/components/ui/button';
import BrutalistAuthLayout from '@/layouts/brutalist-auth-layout';

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
        <BrutalistAuthLayout title="JOIN THE FORGE" description="CREATE YOUR ACCOUNT TO START DESTROYING BEATS">
            <Head title="Register" />
            <form className="space-y-6" onSubmit={submit}>
                <div className="space-y-4">
                    <div>
                        <BrutalistLabel htmlFor="name">FULL NAME</BrutalistLabel>
                        <BrutalistInput
                            id="name"
                            type="text"
                            required
                            autoFocus
                            tabIndex={1}
                            autoComplete="name"
                            value={data.name}
                            onChange={(e) => setData('name', e.target.value)}
                            disabled={processing}
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
                            required
                            tabIndex={2}
                            autoComplete="email"
                            value={data.email}
                            onChange={(e) => setData('email', e.target.value)}
                            disabled={processing}
                            placeholder="EMAIL@EXAMPLE.COM"
                            hasError={!!errors.email}
                        />
                        <InputError message={errors.email} />
                    </div>

                    <div>
                        <BrutalistLabel htmlFor="password">PASSWORD</BrutalistLabel>
                        <BrutalistInput
                            id="password"
                            type="password"
                            required
                            tabIndex={3}
                            autoComplete="new-password"
                            value={data.password}
                            onChange={(e) => setData('password', e.target.value)}
                            disabled={processing}
                            placeholder="CREATE A STRONG PASSWORD"
                            hasError={!!errors.password}
                        />
                        <InputError message={errors.password} />
                    </div>

                    <div>
                        <BrutalistLabel htmlFor="password_confirmation">CONFIRM PASSWORD</BrutalistLabel>
                        <BrutalistInput
                            id="password_confirmation"
                            type="password"
                            required
                            tabIndex={4}
                            autoComplete="new-password"
                            value={data.password_confirmation}
                            onChange={(e) => setData('password_confirmation', e.target.value)}
                            disabled={processing}
                            placeholder="CONFIRM YOUR PASSWORD"
                            hasError={!!errors.password_confirmation}
                        />
                        <InputError message={errors.password_confirmation} />
                    </div>

                    <Button
                        type="submit"
                        className="mt-6 h-12 w-full bg-chart-2 font-heading font-black tracking-widest text-main-foreground uppercase hover:bg-chart-1"
                        tabIndex={5}
                        disabled={processing}
                    >
                        {processing && <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />}
                        {processing ? 'CREATING ACCOUNT...' : 'CREATE FORGE ACCOUNT'}
                    </Button>
                </div>

                <div className="border-t-2 border-border pt-6 text-center">
                    <span className="text-sm font-base font-bold tracking-wide text-foreground/70 uppercase">ALREADY HAVE AN ACCOUNT? </span>
                    <Link
                        href={route('login')}
                        className="font-heading text-sm font-black tracking-wide text-chart-1 uppercase transition-colors hover:text-chart-2"
                        tabIndex={6}
                    >
                        LOG IN
                    </Link>
                </div>
            </form>
        </BrutalistAuthLayout>
    );
}
