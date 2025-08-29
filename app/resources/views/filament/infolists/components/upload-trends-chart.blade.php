<x-dynamic-component
    :component="$getEntryWrapperView()"
    :entry="$entry"
>
    <div class="bg-red-100 p-4 border border-red-300 rounded">
        <h4>Debug View Test</h4>
        <p>Labels: {{ count($uploadTrends['labels']) }}</p>
        <p>Data: {{ array_sum($uploadTrends['data']) }}</p>
        <p>First Label: {{ $uploadTrends['labels'][0] ?? 'N/A' }}</p>
    </div>
</x-dynamic-component>