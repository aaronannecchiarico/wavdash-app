<?php

namespace Tests\Feature;

use App\Http\Middleware\AdminAuditLog;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Tests\TestCase;

class AdminAuditLogTest extends TestCase
{
    use RefreshDatabase;

    public function test_middleware_logs_non_get_authenticated_requests(): void
    {
        $user = User::factory()->create(['email' => 'admin@test.com']);
        $this->actingAs($user);

        // Mock the logger to capture log calls
        Log::shouldReceive('info')
            ->once()
            ->with('Admin action performed', \Mockery::on(function ($data) use ($user) {
                return $data['user_id'] === $user->id
                    && $data['user_email'] === 'admin@test.com'
                    && $data['action'] === 'POST'
                    && str_contains($data['url'], '/admin/test')
                    && $data['response_status'] === 200
                    && isset($data['timestamp'])
                    && isset($data['ip'])
                    && isset($data['user_agent']);
            }));

        $middleware = new AdminAuditLog;
        $request = Request::create('/admin/test', 'POST', ['key' => 'value']);

        $response = $middleware->handle($request, function () {
            return response('Success', 200);
        });

        $this->assertEquals('Success', $response->getContent());
    }

    public function test_middleware_ignores_get_requests(): void
    {
        $user = User::factory()->create();
        $this->actingAs($user);

        // Should not receive any log calls for GET requests
        Log::shouldReceive('info')->never();

        $middleware = new AdminAuditLog;
        $request = Request::create('/admin/test', 'GET');

        $response = $middleware->handle($request, function () {
            return response('Success');
        });

        $this->assertEquals('Success', $response->getContent());
    }

    public function test_middleware_ignores_unauthenticated_requests(): void
    {
        // Should not receive any log calls for unauthenticated requests
        Log::shouldReceive('info')->never();

        $middleware = new AdminAuditLog;
        $request = Request::create('/admin/test', 'POST', ['key' => 'value']);

        $response = $middleware->handle($request, function () {
            return response('Success');
        });

        $this->assertEquals('Success', $response->getContent());
    }

    public function test_middleware_sanitizes_sensitive_data(): void
    {
        $user = User::factory()->create();
        $this->actingAs($user);

        Log::shouldReceive('info')
            ->once()
            ->with('Admin action performed', \Mockery::on(function ($data) {
                $requestData = $data['request_data'];

                return $requestData['password'] === '[REDACTED]'
                    && $requestData['token'] === '[REDACTED]'
                    && $requestData['safe_data'] === 'visible'
                    && $requestData['api_key'] === '[REDACTED]';
            }));

        $middleware = new AdminAuditLog;
        $request = Request::create('/admin/test', 'POST', [
            'safe_data' => 'visible',
            'password' => 'secret123',
            'token' => 'abc123',
            'api_key' => 'key123',
        ]);

        $middleware->handle($request, function () {
            return response('Success');
        });
    }

    public function test_middleware_handles_large_request_data(): void
    {
        $user = User::factory()->create();
        $this->actingAs($user);

        Log::shouldReceive('info')
            ->once()
            ->with('Admin action performed', \Mockery::on(function ($data) {
                $requestData = $data['request_data'];

                return isset($requestData['size_exceeded']);
            }));

        $middleware = new AdminAuditLog;

        // Create large request data
        $largeData = [];
        for ($i = 0; $i < 1000; $i++) {
            $largeData["field_$i"] = str_repeat('x', 100);
        }

        $request = Request::create('/admin/test', 'POST', $largeData);

        $middleware->handle($request, function () {
            return response('Success');
        });
    }

    public function test_middleware_logs_different_http_methods(): void
    {
        $user = User::factory()->create();
        $this->actingAs($user);

        $methods = ['POST', 'PUT', 'PATCH', 'DELETE'];

        foreach ($methods as $method) {
            Log::shouldReceive('info')
                ->once()
                ->with('Admin action performed', \Mockery::on(function ($data) use ($method) {
                    return $data['action'] === $method;
                }));

            $middleware = new AdminAuditLog;
            $request = Request::create('/admin/test', $method);

            $middleware->handle($request, function () {
                return response('Success');
            });
        }
    }

    public function test_middleware_logs_response_status_codes(): void
    {
        $user = User::factory()->create();
        $this->actingAs($user);

        $statusCodes = [200, 201, 400, 500];

        foreach ($statusCodes as $statusCode) {
            Log::shouldReceive('info')
                ->once()
                ->with('Admin action performed', \Mockery::on(function ($data) use ($statusCode) {
                    return $data['response_status'] === $statusCode;
                }));

            $middleware = new AdminAuditLog;
            $request = Request::create('/admin/test', 'POST');

            $middleware->handle($request, function () use ($statusCode) {
                return response('Response', $statusCode);
            });
        }
    }

    public function test_middleware_includes_request_metadata(): void
    {
        $user = User::factory()->create(['email' => 'test@example.com']);
        $this->actingAs($user);

        Log::shouldReceive('info')
            ->once()
            ->with('Admin action performed', \Mockery::on(function ($data) {
                return isset($data['ip'])
                    && isset($data['user_agent'])
                    && isset($data['timestamp'])
                    && isset($data['url'])
                    && ! empty($data['timestamp']);
            }));

        $middleware = new AdminAuditLog;
        $request = Request::create('/admin/test', 'POST', [], [], [], [
            'REMOTE_ADDR' => '192.168.1.100',
            'HTTP_USER_AGENT' => 'Test Browser/1.0',
        ]);

        $middleware->handle($request, function () {
            return response('Success');
        });
    }

    public function test_sanitize_request_data_handles_edge_cases(): void
    {
        $user = User::factory()->create();
        $this->actingAs($user);

        Log::shouldReceive('info')
            ->once()
            ->with('Admin action performed', \Mockery::on(function ($data) {
                $requestData = $data['request_data'];

                return $requestData['password_confirmation'] === '[REDACTED]'
                    && $requestData['secret'] === '[REDACTED]'
                    && $requestData['normal_field'] === 'value'
                    && $requestData['_token'] === '[REDACTED]';
            }));

        $middleware = new AdminAuditLog;
        $request = Request::create('/admin/test', 'POST', [
            'normal_field' => 'value',
            'password_confirmation' => 'secret123',
            'secret' => 'top_secret',
            '_token' => 'csrf_token',
        ]);

        $middleware->handle($request, function () {
            return response('Success');
        });
    }
}
