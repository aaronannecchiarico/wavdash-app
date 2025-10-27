<?php

namespace App\Policies;

use App\Models\Upload;
use App\Models\User;
use Illuminate\Auth\Access\HandlesAuthorization;

class UploadPolicy
{
    use HandlesAuthorization;

    /**
     * Determine whether the user can view any models.
     */
    public function viewAny(User $user): bool
    {
        // All authenticated users can view uploads (filtered by individual permissions)
        // SuperAdmin can see all, regular users see only their own
        return true;
    }

    /**
     * Determine whether the user can view the model.
     */
    public function view(User $user, Upload $upload): bool
    {
        // SuperAdmin can view any upload
        if ($user->hasRole('SuperAdmin')) {
            return true;
        }

        // Regular users can only view their own uploads
        return $user->id === $upload->user_id;
    }

    /**
     * Determine whether the user can create models.
     */
    public function create(User $user): bool
    {
        return true; // All authenticated users can create uploads
    }

    /**
     * Determine whether the user can update the model.
     */
    public function update(User $user, Upload $upload): bool
    {
        // SuperAdmin can update any upload
        if ($user->hasRole('SuperAdmin')) {
            return true;
        }

        // Regular users can only update their own uploads
        return $user->id === $upload->user_id;
    }

    /**
     * Determine whether the user can delete the model.
     */
    public function delete(User $user, Upload $upload): bool
    {
        // SuperAdmin can delete any upload
        if ($user->hasRole('SuperAdmin')) {
            return true;
        }

        // Regular users can only delete their own uploads
        return $user->id === $upload->user_id;
    }

    /**
     * Determine whether the user can bulk delete models.
     */
    public function deleteAny(User $user): bool
    {
        return true; // Admin users can bulk delete uploads
    }

    /**
     * Determine whether the user can restore the model.
     */
    public function restore(User $user, Upload $upload): bool
    {
        return true; // Admin users can restore uploads
    }

    /**
     * Determine whether the user can bulk restore models.
     */
    public function restoreAny(User $user): bool
    {
        return true; // Admin users can bulk restore uploads
    }

    /**
     * Determine whether the user can permanently delete the model.
     */
    public function forceDelete(User $user, Upload $upload): bool
    {
        return true; // Admin users can force delete uploads
    }

    /**
     * Determine whether the user can bulk force delete models.
     */
    public function forceDeleteAny(User $user): bool
    {
        return true; // Admin users can bulk force delete uploads
    }
}
