<?php

namespace App\Policies;

use App\Models\FailedJob;
use App\Models\User;
use Illuminate\Auth\Access\Response;

class FailedJobPolicy
{
    /**
     * Determine whether the user can view any models.
     */
    public function viewAny(User $user): bool
    {
        // Only SuperAdmin users can view failed jobs
        return $user->hasRole('SuperAdmin');
    }

    /**
     * Determine whether the user can view the model.
     */
    public function view(User $user, FailedJob $failedJob): bool
    {
        // Only SuperAdmin users can view failed jobs
        return $user->hasRole('SuperAdmin');
    }

    /**
     * Determine whether the user can create models.
     */
    public function create(User $user): bool
    {
        // Failed jobs cannot be created manually
        return false;
    }

    /**
     * Determine whether the user can update the model.
     */
    public function update(User $user, FailedJob $failedJob): bool
    {
        // Failed jobs cannot be edited
        return false;
    }

    /**
     * Determine whether the user can delete the model.
     */
    public function delete(User $user, FailedJob $failedJob): bool
    {
        // Only SuperAdmin users can delete failed jobs
        return $user->hasRole('SuperAdmin');
    }

    /**
     * Determine whether the user can restore the model.
     */
    public function restore(User $user, FailedJob $failedJob): bool
    {
        // Failed jobs cannot be restored (they don't use soft deletes)
        return false;
    }

    /**
     * Determine whether the user can bulk delete models.
     */
    public function deleteAny(User $user): bool
    {
        // Only SuperAdmin users can bulk delete failed jobs
        return $user->hasRole('SuperAdmin');
    }

    /**
     * Determine whether the user can permanently delete the model.
     */
    public function forceDelete(User $user, FailedJob $failedJob): bool
    {
        // Only SuperAdmin users can force delete failed jobs
        return $user->hasRole('SuperAdmin');
    }
}
