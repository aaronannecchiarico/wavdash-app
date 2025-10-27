<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class ContestStoreRequest extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return true;
    }

    /**
     * Get the validation rules that apply to the request.
     */
    public function rules(): array
    {
        return [
            'user_id' => ['required', 'integer', 'exists:Users,id'],
            'name' => ['required', 'string'],
            'description' => ['nullable', 'string'],
            'genre' => ['required', 'string', 'max:100'],
            'state' => ['required', 'in:open,voting,finished'],
            'start_date' => ['required'],
            'end_date' => ['required'],
            'winner_id' => ['nullable', 'integer', 'exists:users,id'],
        ];
    }
}
