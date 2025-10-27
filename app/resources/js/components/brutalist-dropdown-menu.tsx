import { type Upload } from '@/types';
import { Link } from '@inertiajs/react';
import { BarChart3, Download, Gauge, MoreVertical, Pencil, Scissors, Trash2 } from 'lucide-react';
import { useState } from 'react';

interface BrutalistDropdownMenuProps {
    upload: Upload;
}

export function BrutalistDropdownMenu({ upload }: BrutalistDropdownMenuProps) {
    const [isOpen, setIsOpen] = useState(false);

    const menuItems = [
        {
            label: 'AUDIO ANALYSIS',
            icon: BarChart3,
            href: `/uploads/${upload.id}/analysis`,
            status: upload.has_analysis ? 'DONE' : upload.is_analysis_in_progress ? 'PROCESSING' : null,
            color: 'bg-chart-1', // neo-green
        },
        {
            label: 'STEM SEPARATION',
            icon: Scissors,
            href: `/uploads/${upload.id}/stems`,
            status: upload.has_stems ? 'DONE' : upload.is_stem_separation_in_progress ? 'PROCESSING' : null,
            color: 'bg-chart-2', // neo-pink
        },
        {
            label: 'TEMPO EFFECTS',
            icon: Gauge,
            href: `/uploads/${upload.id}/tempo`,
            status: upload.has_tempos ? 'DONE' : upload.is_tempo_processing_in_progress ? 'PROCESSING' : null,
            color: 'bg-chart-4', // neo-blue
        },
        {
            label: 'EDIT',
            icon: Pencil,
            href: `/uploads/${upload.id}/edit`,
            color: 'bg-chart-3', // neo-yellow
        },
        {
            label: 'VIEW DETAILS',
            icon: Download,
            href: `/uploads/${upload.id}`,
            color: 'bg-main',
        },
    ];

    return (
        <div className="relative">
            <button
                className="border-2 border-border bg-main px-3 py-2 font-heading text-xs font-black text-main-foreground uppercase shadow-shadow transition-colors hover:translate-x-1 hover:translate-y-1 hover:bg-main-foreground hover:text-main hover:shadow-none"
                onClick={(e) => {
                    e.stopPropagation();
                    setIsOpen(!isOpen);
                }}
            >
                <MoreVertical className="h-4 w-4" />
            </button>

            {isOpen && (
                <>
                    {/* Backdrop */}
                    <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />

                    {/* Menu */}
                    <div className="absolute top-full right-0 z-20 mt-2 w-64 border-2 border-border bg-background shadow-shadow">
                        <div className="border-b-2 border-border bg-border p-2">
                            <h3 className="font-heading text-xs font-black tracking-widest text-foreground uppercase">TRACK ACTIONS</h3>
                        </div>

                        <div className="space-y-1 p-2">
                            {menuItems.map((item) => (
                                <Link
                                    key={item.label}
                                    href={item.href}
                                    className="group block w-full border-2 border-border p-3 transition-all hover:-translate-x-1 hover:-translate-y-1 hover:shadow-shadow"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setIsOpen(false);
                                    }}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center space-x-3">
                                            <div className={`border-2 border-border p-2 ${item.color}`}>
                                                <item.icon className="h-4 w-4 text-main-foreground" />
                                            </div>
                                            <span className="font-heading text-xs font-black tracking-wide text-foreground uppercase">
                                                {item.label}
                                            </span>
                                        </div>

                                        {item.status && (
                                            <div
                                                className={`border-2 border-border px-2 py-1 ${
                                                    item.status === 'DONE' ? 'bg-chart-1' : item.status === 'PROCESSING' ? 'bg-chart-3' : 'bg-border'
                                                }`}
                                            >
                                                <span className="font-heading text-xs font-black text-main-foreground">{item.status}</span>
                                            </div>
                                        )}
                                    </div>
                                </Link>
                            ))}

                            {/* Delete Action - Special styling */}
                            <button
                                className="group block w-full border-2 border-red-500 bg-red-500 p-3 transition-all hover:-translate-x-1 hover:-translate-y-1 hover:bg-red-600 hover:shadow-shadow"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    // Handle delete action
                                    console.log('Delete upload:', upload.id);
                                    setIsOpen(false);
                                }}
                            >
                                <div className="flex items-center space-x-3">
                                    <div className="border-2 border-white bg-white p-2">
                                        <Trash2 className="h-4 w-4 text-red-500" />
                                    </div>
                                    <span className="font-heading text-xs font-black tracking-wide text-white uppercase">DELETE</span>
                                </div>
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
