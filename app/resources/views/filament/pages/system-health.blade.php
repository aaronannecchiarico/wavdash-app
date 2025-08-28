<x-filament-panels::page>
    <div class="space-y-8">
        <!-- Services Status -->
        <div class="w-full">
            {{ $this->servicesInfolist }}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Queue Status -->
            <div>
                {{ $this->queueInfolist }}
            </div>

            <!-- Storage Status -->
            <div>
                {{ $this->storageInfolist }}
            </div>
        </div>

        <!-- Database Status -->
        <div class="w-full">
            {{ $this->databaseInfolist }}
        </div>
    </div>
</x-filament-panels::page>
