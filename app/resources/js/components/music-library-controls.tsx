import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Filter, ArrowUpDown, Check, ChevronUp, ChevronDown } from 'lucide-react';
import { router } from '@inertiajs/react';
import { useCallback } from 'react';

interface MusicLibraryControlsProps {
    filters: {
        status?: string;
        type?: string;
        sort?: string;
        direction?: string;
        analysis_status?: string;
        stems_status?: string;
        tempo_status?: string;
    };
    filterOptions: {
        statuses: string[];
        types: string[];
        processingStatuses: Record<string, string>;
    };
}

const sortOptions = [
    { label: 'Last Updated', value: 'updated_at' },
    { label: 'Name', value: 'title' },
    { label: 'Size', value: 'size' },
    { label: 'Duration', value: 'duration' },
];

export function MusicLibraryControls({ filters, filterOptions }: MusicLibraryControlsProps) {
    const handleFilterChange = useCallback((key: keyof typeof filters, value: string | null) => {
        const newFilters: Partial<typeof filters> = { ...filters };
        if (value) {
            newFilters[key] = value;
        } else {
            delete newFilters[key];
        }
        router.get(route('uploads.index'), newFilters, { preserveState: true, replace: true });
    }, [filters]);

    const handleSortChange = useCallback((value: string) => {
        const currentSort = filters.sort || 'updated_at';
        const currentDirection = filters.direction || 'desc';
        let newDirection = 'desc';

        if (currentSort === value) {
            newDirection = currentDirection === 'desc' ? 'asc' : 'desc';
        }

        router.get(route('uploads.index'), { ...filters, sort: value, direction: newDirection }, { preserveState: true, replace: true });
    }, [filters]);

    const activeFilterCount = [filters.status, filters.type, filters.analysis_status, filters.stems_status, filters.tempo_status].filter(Boolean).length;

    return (
        <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="outline" className="flex items-center gap-2">
                            <Filter className="h-4 w-4" />
                            <span>Filter</span>
                            {activeFilterCount > 0 && <span className="ml-2 flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-xs text-white">
                                {activeFilterCount}
                            </span>}
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" className="w-56">
                        <DropdownMenuLabel>Filter by Status</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleFilterChange('status', null)}>
                            <div className="flex items-center justify-between w-full">
                                All Statuses
                                {!filters.status && <Check className="h-4 w-4 text-blue-600" />}
                            </div>
                        </DropdownMenuItem>
                        {filterOptions.statuses.map((status) => (
                            <DropdownMenuItem key={status} onClick={() => handleFilterChange('status', status)}>
                                <div className="flex items-center justify-between w-full">
                                    {status.charAt(0).toUpperCase() + status.slice(1)}
                                    {filters.status === status && <Check className="h-4 w-4 text-blue-600" />}
                                </div>
                            </DropdownMenuItem>
                        ))}
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel>Filter by Type</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleFilterChange('type', null)}>
                            <div className="flex items-center justify-between w-full">
                                All Types
                                {!filters.type && <Check className="h-4 w-4 text-blue-600" />}
                            </div>
                        </DropdownMenuItem>
                        {filterOptions.types.map((type) => (
                            <DropdownMenuItem key={type} onClick={() => handleFilterChange('type', type)}>
                                <div className="flex items-center justify-between w-full">
                                    {type.toUpperCase()}
                                    {filters.type === type && <Check className="h-4 w-4 text-blue-600" />}
                                </div>
                            </DropdownMenuItem>
                        ))}
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel>Analysis Status</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleFilterChange('analysis_status', null)}>
                            <div className="flex items-center justify-between w-full">
                                All Analysis
                                {!filters.analysis_status && <Check className="h-4 w-4 text-blue-600" />}
                            </div>
                        </DropdownMenuItem>
                        {Object.entries(filterOptions.processingStatuses).map(([key, label]) => (
                            <DropdownMenuItem key={key} onClick={() => handleFilterChange('analysis_status', key)}>
                                <div className="flex items-center justify-between w-full">
                                    {label}
                                    {filters.analysis_status === key && <Check className="h-4 w-4 text-blue-600" />}
                                </div>
                            </DropdownMenuItem>
                        ))}
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel>Stems Status</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleFilterChange('stems_status', null)}>
                            <div className="flex items-center justify-between w-full">
                                All Stems
                                {!filters.stems_status && <Check className="h-4 w-4 text-blue-600" />}
                            </div>
                        </DropdownMenuItem>
                        {Object.entries(filterOptions.processingStatuses).map(([key, label]) => (
                            <DropdownMenuItem key={key} onClick={() => handleFilterChange('stems_status', key)}>
                                <div className="flex items-center justify-between w-full">
                                    {label}
                                    {filters.stems_status === key && <Check className="h-4 w-4 text-blue-600" />}
                                </div>
                            </DropdownMenuItem>
                        ))}
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel>Tempo Effects Status</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleFilterChange('tempo_status', null)}>
                            <div className="flex items-center justify-between w-full">
                                All Tempo Effects
                                {!filters.tempo_status && <Check className="h-4 w-4 text-blue-600" />}
                            </div>
                        </DropdownMenuItem>
                        {Object.entries(filterOptions.processingStatuses).map(([key, label]) => (
                            <DropdownMenuItem key={key} onClick={() => handleFilterChange('tempo_status', key)}>
                                <div className="flex items-center justify-between w-full">
                                    {label}
                                    {filters.tempo_status === key && <Check className="h-4 w-4 text-blue-600" />}
                                </div>
                            </DropdownMenuItem>
                        ))}
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="flex items-center gap-2">
                        <ArrowUpDown className="h-4 w-4" />
                        <span>Sort</span>
                        {filters.sort && filters.sort !== 'updated_at' && (
                            <span className="ml-1 flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-xs text-white">
                                1
                            </span>
                        )}
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    {sortOptions.map((option) => {
                        const currentSort = filters.sort || 'updated_at';
                        const currentDirection = filters.direction || 'desc';
                        const isActive = currentSort === option.value;
                        
                        return (
                            <DropdownMenuItem key={option.value} onClick={() => handleSortChange(option.value)}>
                                <div className="flex items-center justify-between w-full">
                                    <span>{option.label}</span>
                                    {isActive && (
                                        <div className="flex items-center">
                                            {currentDirection === 'desc' ? (
                                                <ChevronDown className="h-4 w-4 text-blue-600" />
                                            ) : (
                                                <ChevronUp className="h-4 w-4 text-blue-600" />
                                            )}
                                        </div>
                                    )}
                                </div>
                            </DropdownMenuItem>
                        );
                    })}
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
}
