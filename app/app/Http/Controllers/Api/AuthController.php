<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;

class AuthController extends Controller
{
    /**
     * Check if the user is authenticated and return user data
     *
     * This endpoint is used by the marketing site to display
     * authentication state without handling auth logic.
     *
     * @return \Illuminate\Http\JsonResponse
     */
    public function check(Request $request)
    {
        $user = $request->user();

        return response()->json([
            'authenticated' => $user !== null,
            'user' => $user ? [
                'id' => $user->id,
                'name' => $user->name,
                'email' => $user->email,
                // Add other safe, non-sensitive user data as needed
            ] : null,
        ]);
    }
}
