interface BrutalistStatusBadgeProps {
    status: 'Upcoming' | 'Active' | 'Finished';
}

export const BrutalistStatusBadge = ({ status }: BrutalistStatusBadgeProps) => {
    const getStatusClasses = (status: string) => {
        switch (status) {
            case 'Active':
                return 'neo-border bg-neo-green text-neo-black';
            case 'Finished':
                return 'neo-border bg-neo-pink text-neo-white';
            case 'Upcoming':
                return 'neo-border bg-neo-yellow text-neo-black';
            default:
                return 'neo-border bg-neo-blue text-neo-white';
        }
    };

    return (
        <div className={`${getStatusClasses(status)} inline-block px-3 py-1`}>
            <span className="text-xs font-black tracking-wide uppercase">{status}</span>
        </div>
    );
};
