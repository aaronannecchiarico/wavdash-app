import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import Echo from 'laravel-echo';
import Pusher from 'pusher-js';

declare global {
    interface Window {
        Pusher: typeof Pusher;
    }
}

window.Pusher = Pusher;

interface EchoContextType {
    echo: Echo<any> | null;
}

const EchoContext = createContext<EchoContextType>({ echo: null });

export const useEcho = () => useContext(EchoContext);

export const EchoProvider = ({ children }: { children: ReactNode }) => {
    const [echo, setEcho] = useState<Echo<any> | null>(null);

    useEffect(() => {
        const echoInstance = new Echo({
            broadcaster: 'reverb',
            key: import.meta.env.VITE_REVERB_APP_KEY,
            wsHost: import.meta.env.VITE_REVERB_HOST,
            wsPort: import.meta.env.VITE_REVERB_PORT,
            wssPort: import.meta.env.VITE_REVERB_PORT,
            forceTLS: (import.meta.env.VITE_REVERB_SCHEME ?? 'https') === 'https',
            enabledTransports: ['ws', 'wss'],
        });

        setEcho(echoInstance);

        return () => {
            echoInstance.disconnect();
        };
    }, []);

    return <EchoContext.Provider value={{ echo }}>{children}</EchoContext.Provider>;
};
