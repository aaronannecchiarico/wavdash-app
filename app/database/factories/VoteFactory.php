<?php

namespace Database\Factories;

use App\Models\Contest;
use App\Models\ContestUser;
use App\Models\User;
use App\Models\Vote;
use Illuminate\Database\Eloquent\Factories\Factory;

class VoteFactory extends Factory
{
    /**
     * The name of the factory's corresponding model.
     *
     * @var string
     */
    protected $model = Vote::class;

    /**
     * Define the model's default state.
     */
    public function definition(): array
    {
        return [
            'user_id' => User::factory(),
            'contest_id' => Contest::factory(),
            'participant_id' => ContestUser::factory(),
            'contest_user_id' => ContestUser::factory(),
        ];
    }
}
