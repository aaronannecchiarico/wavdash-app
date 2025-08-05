import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Filter, ArrowUpDown } from 'lucide-react';
import { router } from '@inertiajs/react';
import { useCallback } from 'react';

interface MusicLibraryControlsProps {
    filters: {
        status?: string;
        type?: string;
        sort?: string;
        direction?: string;
    };
    filterOptions: {
        statuses: string[];
        types: string[];
    };
}

const sortOptions = [
    { label: 'Last Updated', value: 'updated_at' },
    { label: 'Name', value: 'title' },
    { label: 'Size', value: 'size' },
    { label: 'Duration', value: 'duration' },
];

export function MusicLibraryControls({ filters, filterOptions }: MusicLibraryControlsProps) {
    const handleFilterChange = useCallback((key: 'status' | 'type', value: string | null) => {
        const newFilters: Partial<typeof filters> = { ...filters };
        if (value) {
            newFilters[key] = value;
        } else {
            delete newFilters[key];
        }
        router.get(route('uploads.index'), newFilters as any, { preserveState: true, replace: true });
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

    const activeFilterCount = [filters.status, filters.type].filter(Boolean).length;

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
                    <DropdownMenuContent align="start">
                        <DropdownMenuLabel>Filter by Status</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleFilterChange('status', null)}>All Statuses</DropdownMenuItem>
                        {filterOptions.statuses.map((status) => (
                            <DropdownMenuItem key={status} onClick={() => handleFilterChange('status', status)}>
                                {status.charAt(0).toUpperCase() + status.slice(1)}
                            </DropdownMenuItem>
                        ))}
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel>Filter by Type</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleFilterChange('type', null)}>All Types</DropdownMenuItem>
                        {filterOptions.types.map((type) => (
                            <DropdownMenuItem key={type} onClick={() => handleFilterChange('type', type)}>
                                {type.toUpperCase()}
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
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    {sortOptions.map((option) => (
                        <DropdownMenuItem key={option.value} onClick={() => handleSortChange(option.value)}>
                            {option.label}
                        </DropdownMenuItem>
                    ))}
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
}
