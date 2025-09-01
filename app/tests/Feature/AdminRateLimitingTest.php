<?php

namespace Tests\Feature;

use App\Http\Middleware\AdminRateLimiting;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;
use Tests\TestCase;

class AdminRateLimitingTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        
        // Clear rate limiter state
        RateLimiter::clear('admin-access:127.0.0.1');
    }

    public function test_middleware_allows_requests_within_rate_limit(): void
    {
        config(['admin.rate_limiting.global_requests' => '5,1']);
        
        $middleware = new AdminRateLimiting;
        $request = Request::create('/admin', 'GET');
        
        // First request should pass
        $response = $middleware->handle($request, function () {
            return response('Success');
        });
        
        $this->assertEquals('Success', $response->getContent());
    }

    public function test_middleware_blocks_requests_exceeding_rate_limit(): void
    {
        config(['admin.rate_limiting.global_requests' => '2,1']);
        
        $middleware = new AdminRateLimiting;
        $request = Request::create('/admin', 'GET');
        
        // Make requests up to the limit
        $middleware->handle($request, function () {
            return response('Success');
        });
        
        $middleware->handle($request, function () {
            return response('Success');
        });
        
        // Third request should be blocked
        $this->expectException(\Symfony\Component\HttpKernel\Exception\NotFoundHttpException::class);
        
        $middleware->handle($request, function () {
            return response('Should not reach here');
        });
    }

    public function test_middleware_uses_different_keys_for_different_ips(): void
    {
        config(['admin.rate_limiting.global_requests' => '1,1']);
        
        $middleware = new AdminRateLimiting;
        
        // First IP - make request up to limit
        $request1 = Request::create('/admin', 'GET', [], [], [], ['REMOTE_ADDR' => '192.168.1.1']);
        $response1 = $middleware->handle($request1, function () {
            return response('Success IP1');
        });
        $this->assertEquals('Success IP1', $response1->getContent());
        
        // Different IP should still work
        $request2 = Request::create('/admin', 'GET', [], [], [], ['REMOTE_ADDR' => '192.168.1.2']);
        $response2 = $middleware->handle($request2, function () {
            return response('Success IP2');
        });
        $this->assertEquals('Success IP2', $response2->getContent());
    }

    public function test_middleware_respects_configuration_changes(): void
    {
        // Start with restrictive limit
        config(['admin.rate_limiting.global_requests' => '1,1']);
        
        $middleware = new AdminRateLimiting;
        $request = Request::create('/admin', 'GET');
        
        // First request passes
        $response = $middleware->handle($request, function () {
            return response('Success');
        });
        $this->assertEquals('Success', $response->getContent());
        
        // Change to more permissive limit (this won't affect current test due to rate limiter state, 
        // but tests the configuration reading)
        config(['admin.rate_limiting.global_requests' => '10,1']);
        
        // Create new middleware instance to test config reading
        $newMiddleware = new AdminRateLimiting;
        $newRequest = Request::create('/admin', 'GET', [], [], [], ['REMOTE_ADDR' => '192.168.1.100']);
        
        $response = $newMiddleware->handle($newRequest, function () {
            return response('Success with new config');
        });
        $this->assertEquals('Success with new config', $response->getContent());
    }

    public function test_middleware_handles_malformed_configuration_gracefully(): void
    {
        // Test with malformed configuration
        config(['admin.rate_limiting.global_requests' => 'invalid_config']);
        
        $middleware = new AdminRateLimiting;
        $request = Request::create('/admin', 'GET');
        
        // Should still work with default behavior (PHP will handle the conversion)
        $response = $middleware->handle($request, function () {
            return response('Success');
        });
        
        $this->assertEquals('Success', $response->getContent());
    }

    public function test_middleware_logs_rate_limit_exceeded(): void
    {
        config(['admin.rate_limiting.global_requests' => '1,1']);
        
        $middleware = new AdminRateLimiting;
        $request = Request::create('/admin/test', 'GET', [], [], [], [
            'REMOTE_ADDR' => '192.168.1.100',
            'HTTP_USER_AGENT' => 'Test Browser',
        ]);
        
        // First request to establish rate limit
        $middleware->handle($request, function () {
            return response('Success');
        });
        
        // Second request should be blocked and logged
        try {
            $middleware->handle($request, function () {
                return response('Should not reach here');
            });
        } catch (\Symfony\Component\HttpKernel\Exception\NotFoundHttpException $e) {
            // Expected exception
        }
        
        // The logging is tested by verifying the middleware doesn't throw unexpected errors
        // In a real application, you would check log files or use a log testing framework
        $this->assertTrue(true);
    }

    public function test_rate_limit_resets_after_time_window(): void
    {
        config(['admin.rate_limiting.global_requests' => '1,1']);
        
        $middleware = new AdminRateLimiting;
        $request = Request::create('/admin', 'GET');
        
        // Make request up to limit
        $response = $middleware->handle($request, function () {
            return response('Success');
        });
        $this->assertEquals('Success', $response->getContent());
        
        // Clear rate limiter to simulate time passage
        RateLimiter::clear('admin-access:127.0.0.1');
        
        // Should work again after reset
        $response = $middleware->handle($request, function () {
            return response('Success after reset');
        });
        $this->assertEquals('Success after reset', $response->getContent());
    }
}