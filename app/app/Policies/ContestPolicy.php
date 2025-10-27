<?php

namespace App\Policies;

use App\Models\Contest;
use App\Models\User;

class ContestPolicy
{
    /**
     * Determine whether the user can view any models.
     */
    public function viewAny(User $user): bool
    {
        return true; // Allow admin users to view contests
    }

    /**
     * Determine whether the user can view the model.
     */
    public function view(User $user, Contest $contest): bool
    {
        return true; // Allow admin users to view individual contests
    }

    /**
     * Determine whether the user can create models.
     */
    public function create(User $user): bool
    {
        return true; // Allow admin users to create contests
    }

    /**
     * Determine whether the user can update the model.
     */
    public function update(User $user, Contest $contest): bool
    {
        return true; // Allow admin users to update contests
    }

    /**
     * Determine whether the user can delete the model.
     */
    public function delete(User $user, Contest $contest): bool
    {
        return true; // Allow admin users to delete contests
    }

    /**
     * Determine whether the user can bulk delete models.
     */
    public function deleteAny(User $user): bool
    {
        return true; // Allow admin users to bulk delete contests
    }

    /**
     * Determine whether the user can restore the model.
     */
    public function restore(User $user, Contest $contest): bool
    {
        return true; // Allow admin users to restore contests
    }

    /**
     * Determine whether the user can bulk restore models.
     */
    public function restoreAny(User $user): bool
    {
        return true; // Allow admin users to bulk restore contests
    }

    /**
     * Determine whether the user can permanently delete the model.
     */
    public function forceDelete(User $user, Contest $contest): bool
    {
        return true; // Allow admin users to force delete contests
    }

    /**
     * Determine whether the user can bulk force delete models.
     */
    public function forceDeleteAny(User $user): bool
    {
        return true; // Allow admin users to bulk force delete contests
    }
}
