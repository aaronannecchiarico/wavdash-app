<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StoreUploadRequest extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        // Only authenticated users can upload files
        return true; // We're already using auth middleware in the routes
    }

    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, \Illuminate\Contracts\Validation\ValidationRule|array|string>
     */
    public function rules(): array
    {
        $rules = [
            'title' => 'required|string|max:255',
            'description' => 'nullable|string|max:1000',
        ];

        if ($this->boolean('client_processed')) {
            $rules['audio_file'] = [
                'required',
                'file',
                'mimes:ogg', // Only OGG for processed files
                'max:25000', // Processed files are typically smaller
            ];
            $rules['original_filename'] = 'required|string';
            $rules['original_size'] = 'required|integer|min:1';
            $rules['duration'] = 'required|numeric|min:0';
        } else {
            $rules['audio_file'] = [
                'required',
                'file',
                'mimes:mp3,wav,aiff,ogg,flac',
                'max:50000', // 50MB max file size
            ];
        }

        return $rules;
    }
}
