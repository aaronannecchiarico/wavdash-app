<?php

declare(strict_types=1);

namespace Tests\Support;

use PHPUnit\Event\Test\Finished;
use PHPUnit\Event\Test\FinishedSubscriber;
use PHPUnit\Event\Test\Prepared;
use PHPUnit\Event\Test\PreparedSubscriber;
use PHPUnit\Event\TestRunner\ExecutionFinished;
use PHPUnit\Event\TestRunner\ExecutionFinishedSubscriber;
use PHPUnit\Runner\Extension\Extension;
use PHPUnit\Runner\Extension\Facade;
use PHPUnit\Runner\Extension\ParameterCollection;
use PHPUnit\TextUI\Configuration\Configuration;

final class SpeedTrapExtension implements Extension
{
    private array $slowTests = [];

    private array $testStartTimes = [];

    private int $slowThreshold = 500; // milliseconds

    private int $reportLength = 10;

    public function bootstrap(Configuration $configuration, Facade $facade, ParameterCollection $parameters): void
    {
        $this->slowThreshold = (int) ($parameters->get('slowThreshold') ?? 500);
        $this->reportLength = (int) ($parameters->get('reportLength') ?? 10);

        $facade->registerSubscriber(new class($this) implements PreparedSubscriber
        {
            public function __construct(private SpeedTrapExtension $extension) {}

            public function notify(Prepared $event): void
            {
                $this->extension->handleTestStarted($event);
            }
        });

        $facade->registerSubscriber(new class($this) implements FinishedSubscriber
        {
            public function __construct(private SpeedTrapExtension $extension) {}

            public function notify(Finished $event): void
            {
                $this->extension->handleTestFinished($event);
            }
        });

        $facade->registerSubscriber(new class($this) implements ExecutionFinishedSubscriber
        {
            public function __construct(private SpeedTrapExtension $extension) {}

            public function notify(ExecutionFinished $event): void
            {
                $this->extension->handleExecutionFinished();
            }
        });
    }

    public function handleTestStarted(Prepared $event): void
    {
        $test = $event->test();
        if ($test->isTestMethod()) {
            $label = sprintf('%s::%s', $test->className(), $test->methodName());
            $this->testStartTimes[$label] = microtime(true);
        }
    }

    public function handleTestFinished(Finished $event): void
    {
        $test = $event->test();
        if (! $test->isTestMethod()) {
            return;
        }

        $label = sprintf('%s::%s', $test->className(), $test->methodName());

        if (! isset($this->testStartTimes[$label])) {
            return;
        }

        $startTime = $this->testStartTimes[$label];
        $endTime = microtime(true);
        $durationInMs = (int) round(($endTime - $startTime) * 1000);

        // Clean up the start time
        unset($this->testStartTimes[$label]);

        if ($durationInMs >= $this->slowThreshold) {
            $this->slowTests[$label] = $durationInMs;
        }
    }

    public function handleExecutionFinished(): void
    {
        if (empty($this->slowTests)) {
            return;
        }

        // Sort slowest tests first
        arsort($this->slowTests);

        $this->renderReport();
    }

    private function renderReport(): void
    {
        $count = min(count($this->slowTests), $this->reportLength);

        echo "\n\n";
        echo sprintf("⚠️  You should really fix these slow tests (>%dms)...\n", $this->slowThreshold);

        $i = 1;
        foreach (array_slice($this->slowTests, 0, $count, true) as $label => $duration) {
            echo sprintf(" %d. %dms to run %s\n", $i++, $duration, $label);
        }

        $hidden = count($this->slowTests) - $count;
        if ($hidden > 0) {
            echo sprintf("...and there %s %d more above your threshold hidden from view\n",
                $hidden === 1 ? 'is' : 'are', $hidden);
        }
    }
}
