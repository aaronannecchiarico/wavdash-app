<?php

namespace Tests;

use Illuminate\Foundation\Testing\TestCase as BaseTestCase;
use Illuminate\Support\Facades\Event;

abstract class TestCase extends BaseTestCase
{
    use CreatesApplication;

    /**
     * Setup the test environment.
     */
    protected function setUp(): void
    {
        parent::setUp();

        // Ensure broadcasting is disabled during tests
        $this->assertBroadcastingIsDisabled();
    }

    /**
     * Assert that broadcasting is disabled during tests.
     */
    protected function assertBroadcastingIsDisabled(): void
    {
        $broadcastConnection = config('broadcasting.default');
        $this->assertTrue(
            $broadcastConnection === null || $broadcastConnection === 'null',
            'Broadcasting should be disabled during tests. Current connection: '.($broadcastConnection ?? 'null')
        );
    }

    /**
     * Helper method to fake events and broadcasts for testing.
     * Use this when you need to test event dispatching behavior.
     */
    protected function fakeEventsAndBroadcasts(): void
    {
        Event::fake();
    }
}
