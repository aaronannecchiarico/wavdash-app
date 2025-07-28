<?php

namespace App\Http\Resources;

use Carbon\Carbon;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class ContestResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'description' => $this->description,
            'start_date' => $this->start_date,
            'end_date' => $this->end_date,
            'status' => $this->getStatus(),
            'user' => [
                'id' => $this->user->id,
                'name' => $this->user->name,
            ],
            'contest_users_count' => $this->whenCounted('contestUsers'),
        ];
    }

    /**
     * Get the status of the contest based on its dates.
     */
    protected function getStatus(): string
    {
        $now = Carbon::now();
        $startDate = Carbon::parse($this->start_date);
        $endDate = Carbon::parse($this->end_date);

        if ($now->lt($startDate)) {
            return 'Upcoming';
        }

        if ($now->between($startDate, $endDate)) {
            return 'Active';
        }

        return 'Finished';
    }
}
