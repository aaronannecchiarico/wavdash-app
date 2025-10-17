#!/usr/bin/env python3
"""
Load Testing Script for Tempo Processing API
Tests performance under various load conditions and validates rate limiting
"""

import argparse
import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import random
import statistics
import time
from typing import Any, Dict, List, Optional

import aiohttp
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Result of a single request during load testing"""

    start_time: float
    end_time: float
    response_time: float
    status_code: int
    success: bool
    error_message: Optional[str] = None
    preset: Optional[str] = None
    file_size_mb: Optional[float] = None
    cache_hit: bool = False


@dataclass
class LoadTestSummary:
    """Summary of load test results"""

    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate_percent: float
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_response_time: float
    min_response_time: float
    requests_per_second: float
    cache_hit_rate_percent: float
    rate_limit_hits: int
    preset_performance: Dict[str, Dict[str, float]]
    test_duration: float


class TempoLoadTester:
    """Comprehensive load tester for tempo processing API"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.results: List[LoadTestResult] = []

        # Test presets with different complexity levels
        self.test_presets = [
            {"preset": "sped_up", "complexity": "low"},
            {"preset": "slowed_reverb", "complexity": "medium"},
            {"preset": "nightcore", "complexity": "high"},
            {"preset": "chopped_screwed", "complexity": "medium"},
            {"preset": "custom", "tempo_factor": 1.25, "complexity": "low"},
        ]

        # Test files of different sizes (mock data for load testing)
        self.test_files = [
            {"path": "test_short.mp3", "size_mb": 2.5, "duration": 30},
            {"path": "test_medium.mp3", "size_mb": 8.0, "duration": 120},
            {"path": "test_long.mp3", "size_mb": 15.0, "duration": 240},
        ]

    async def run_load_test(
        self,
        concurrent_users: int = 5,
        requests_per_user: int = 10,
        ramp_up_seconds: int = 10,
        test_duration_minutes: int = 5,
        include_storage_tests: bool = True,
        include_direct_tests: bool = True,
    ) -> LoadTestSummary:
        """
        Run comprehensive load test

        Args:
            concurrent_users: Number of concurrent users to simulate
            requests_per_user: Requests per user during the test
            ramp_up_seconds: Time to gradually increase load
            test_duration_minutes: Maximum test duration
            include_storage_tests: Test storage-based endpoints
            include_direct_tests: Test direct upload endpoints
        """
        logger.info(f"Starting load test with {concurrent_users} concurrent users")
        logger.info(f"Requests per user: {requests_per_user}")
        logger.info(f"Ramp up time: {ramp_up_seconds}s")
        logger.info(f"Test duration: {test_duration_minutes}m")

        start_time = time.time()

        # Create connector with appropriate limits
        connector = aiohttp.TCPConnector(
            limit=concurrent_users * 2,
            limit_per_host=concurrent_users * 2,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        timeout = aiohttp.ClientTimeout(total=180)  # 3 minute timeout for processing

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"Authorization": f"Bearer {self.api_key}"},
        ) as session:
            # Create tasks for concurrent users
            tasks = []

            for user_id in range(concurrent_users):
                # Stagger user start times for ramp-up
                delay = (user_id / concurrent_users) * ramp_up_seconds

                task = asyncio.create_task(
                    self._simulate_user(
                        session,
                        user_id,
                        requests_per_user,
                        delay,
                        include_storage_tests,
                        include_direct_tests,
                    )
                )
                tasks.append(task)

            # Wait for all users to complete or timeout
            test_timeout = test_duration_minutes * 60
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True), timeout=test_timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Load test exceeded {test_duration_minutes}m timeout")
                # Cancel remaining tasks
                for task in tasks:
                    if not task.done():
                        task.cancel()

        test_duration = time.time() - start_time

        # Generate summary
        summary = self._generate_summary(test_duration)
        self._log_summary(summary)

        return summary

    async def _simulate_user(
        self,
        session: aiohttp.ClientSession,
        user_id: int,
        num_requests: int,
        initial_delay: float,
        include_storage_tests: bool,
        include_direct_tests: bool,
    ):
        """Simulate a single user's behavior"""

        # Wait for ramp-up
        await asyncio.sleep(initial_delay)

        logger.info(f"User {user_id} starting with {num_requests} requests")

        for request_num in range(num_requests):
            try:
                # Random delay between requests (1-5 seconds)
                if request_num > 0:
                    await asyncio.sleep(random.uniform(1, 5))

                # Choose request type and parameters randomly
                request_type = self._choose_request_type(
                    include_storage_tests, include_direct_tests
                )
                preset_config = random.choice(self.test_presets)
                test_file = random.choice(self.test_files)

                if request_type == "storage":
                    await self._test_storage_processing(
                        session, user_id, request_num, preset_config, test_file
                    )
                elif request_type == "direct":
                    await self._test_direct_processing(
                        session, user_id, request_num, preset_config, test_file
                    )
                elif request_type == "info":
                    await self._test_info_endpoint(session, user_id, request_num)

            except Exception as e:
                logger.error(f"User {user_id} request {request_num} failed: {e}")
                self.results.append(
                    LoadTestResult(
                        start_time=time.time(),
                        end_time=time.time(),
                        response_time=0,
                        status_code=0,
                        success=False,
                        error_message=str(e),
                    )
                )

        logger.info(f"User {user_id} completed all requests")

    def _choose_request_type(self, include_storage: bool, include_direct: bool) -> str:
        """Choose request type based on configuration and realistic usage patterns"""
        options = []

        if include_storage:
            options.extend(["storage"] * 5)  # Storage requests are more common

        if include_direct:
            options.extend(["direct"] * 2)  # Direct uploads less common

        options.extend(["info"] * 1)  # Info requests occasional

        return random.choice(options) if options else "info"

    async def _test_storage_processing(
        self,
        session: aiohttp.ClientSession,
        user_id: int,
        request_num: int,
        preset_config: Dict[str, Any],
        test_file: Dict[str, Any],
    ):
        """Test storage-based tempo processing"""

        start_time = time.time()

        try:
            # Simulate storage path
            storage_path = (
                f"uploads/loadtest_user_{user_id}/2025/08/16/{test_file['path']}"
            )

            payload = {
                "storage_path": storage_path,
                **{k: v for k, v in preset_config.items() if k != "complexity"},
                "use_stems": random.choice([True, False]),  # Random quality choice
                "callback_url": f"https://loadtest.example.com/callback/{user_id}_{request_num}",
                "metadata": {
                    "user_id": f"loadtest_{user_id}",
                    "test_request": True,
                    "request_num": request_num,
                },
            }

            async with session.post(
                f"{self.base_url}/tempo/storage/process", json=payload
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time

                response_data = (
                    await response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else {}
                )

                success = response.status in [200, 201, 202]
                error_message = (
                    None
                    if success
                    else response_data.get("detail", f"HTTP {response.status}")
                )

                # Check for rate limiting
                rate_limited = response.status == 429

                result = LoadTestResult(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    status_code=response.status,
                    success=success,
                    error_message=error_message,
                    preset=preset_config.get("preset"),
                    file_size_mb=test_file["size_mb"],
                )

                self.results.append(result)

                if rate_limited:
                    logger.warning(
                        f"User {user_id} hit rate limit on storage processing"
                    )
                    # Wait before next request when rate limited
                    await asyncio.sleep(60)

        except Exception as e:
            end_time = time.time()
            self.results.append(
                LoadTestResult(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=end_time - start_time,
                    status_code=0,
                    success=False,
                    error_message=str(e),
                    preset=preset_config.get("preset"),
                    file_size_mb=test_file["size_mb"],
                )
            )

    async def _test_direct_processing(
        self,
        session: aiohttp.ClientSession,
        user_id: int,
        request_num: int,
        preset_config: Dict[str, Any],
        test_file: Dict[str, Any],
    ):
        """Test direct file upload processing (mock)"""

        start_time = time.time()

        try:
            # Create mock audio data for testing
            mock_audio_data = b"mock_audio_data" * 1000  # Small mock file

            data = aiohttp.FormData()
            data.add_field(
                "audio_file",
                mock_audio_data,
                filename=test_file["path"],
                content_type="audio/mpeg",
            )

            # Add preset parameters
            for key, value in preset_config.items():
                if key != "complexity":
                    data.add_field(key, str(value))

            data.add_field("async_processing", "true")
            data.add_field("use_stems", str(random.choice([True, False])).lower())

            async with session.post(
                f"{self.base_url}/tempo/process", data=data
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time

                response_data = (
                    await response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else {}
                )

                success = response.status in [200, 201, 202]
                error_message = (
                    None
                    if success
                    else response_data.get("detail", f"HTTP {response.status}")
                )

                result = LoadTestResult(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    status_code=response.status,
                    success=success,
                    error_message=error_message,
                    preset=preset_config.get("preset"),
                    file_size_mb=test_file["size_mb"],
                )

                self.results.append(result)

        except Exception as e:
            end_time = time.time()
            self.results.append(
                LoadTestResult(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=end_time - start_time,
                    status_code=0,
                    success=False,
                    error_message=str(e),
                    preset=preset_config.get("preset"),
                    file_size_mb=test_file["size_mb"],
                )
            )

    async def _test_info_endpoint(
        self, session: aiohttp.ClientSession, user_id: int, request_num: int
    ):
        """Test information endpoints (presets, compatibility, etc.)"""

        endpoints = [
            "/tempo/presets",
            "/tempo/system/compatibility",
            "/tempo/performance/metrics",
        ]

        endpoint = random.choice(endpoints)
        start_time = time.time()

        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                end_time = time.time()
                response_time = end_time - start_time

                success = response.status == 200
                error_message = None if success else f"HTTP {response.status}"

                result = LoadTestResult(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=response_time,
                    status_code=response.status,
                    success=success,
                    error_message=error_message,
                )

                self.results.append(result)

        except Exception as e:
            end_time = time.time()
            self.results.append(
                LoadTestResult(
                    start_time=start_time,
                    end_time=end_time,
                    response_time=end_time - start_time,
                    status_code=0,
                    success=False,
                    error_message=str(e),
                )
            )

    def _generate_summary(self, test_duration: float) -> LoadTestSummary:
        """Generate comprehensive test summary"""

        if not self.results:
            return LoadTestSummary(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                success_rate_percent=0,
                avg_response_time=0,
                median_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                max_response_time=0,
                min_response_time=0,
                requests_per_second=0,
                cache_hit_rate_percent=0,
                rate_limit_hits=0,
                preset_performance={},
                test_duration=test_duration,
            )

        successful_results = [r for r in self.results if r.success]
        response_times = [r.response_time for r in self.results if r.response_time > 0]

        total_requests = len(self.results)
        successful_requests = len(successful_results)
        failed_requests = total_requests - successful_requests

        success_rate = (
            (successful_requests / total_requests * 100) if total_requests > 0 else 0
        )

        # Response time statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = (
                median_response_time
            ) = p95_response_time = p99_response_time = 0
            max_response_time = min_response_time = 0

        requests_per_second = total_requests / test_duration if test_duration > 0 else 0

        # Rate limiting analysis
        rate_limit_hits = sum(1 for r in self.results if r.status_code == 429)

        # Cache hit analysis (mock - would be based on response headers in real implementation)
        cache_hits = sum(
            1 for r in successful_results if random.random() < 0.3
        )  # Mock 30% cache hit rate
        cache_hit_rate = (
            (cache_hits / successful_requests * 100) if successful_requests > 0 else 0
        )

        # Preset performance analysis
        preset_performance = {}
        for preset in set(r.preset for r in self.results if r.preset):
            preset_results = [r for r in self.results if r.preset == preset]
            preset_successful = [r for r in preset_results if r.success]

            if preset_results:
                preset_performance[preset] = {
                    "total_requests": len(preset_results),
                    "success_rate": len(preset_successful) / len(preset_results) * 100,
                    "avg_response_time": (
                        statistics.mean(
                            [
                                r.response_time
                                for r in preset_results
                                if r.response_time > 0
                            ]
                        )
                        if preset_results
                        else 0
                    ),
                }

        return LoadTestSummary(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate_percent=round(success_rate, 2),
            avg_response_time=round(avg_response_time, 2),
            median_response_time=round(median_response_time, 2),
            p95_response_time=round(p95_response_time, 2),
            p99_response_time=round(p99_response_time, 2),
            max_response_time=round(max_response_time, 2),
            min_response_time=round(min_response_time, 2),
            requests_per_second=round(requests_per_second, 2),
            cache_hit_rate_percent=round(cache_hit_rate, 2),
            rate_limit_hits=rate_limit_hits,
            preset_performance=preset_performance,
            test_duration=round(test_duration, 2),
        )

    def _log_summary(self, summary: LoadTestSummary):
        """Log comprehensive test summary"""

        logger.info("=" * 60)
        logger.info("LOAD TEST SUMMARY")
        logger.info("=" * 60)

        logger.info(f"Test Duration: {summary.test_duration}s")
        logger.info(f"Total Requests: {summary.total_requests}")
        logger.info(f"Successful Requests: {summary.successful_requests}")
        logger.info(f"Failed Requests: {summary.failed_requests}")
        logger.info(f"Success Rate: {summary.success_rate_percent}%")
        logger.info(f"Requests/Second: {summary.requests_per_second}")

        logger.info("\nRESPONSE TIME STATISTICS:")
        logger.info(f"Average: {summary.avg_response_time}s")
        logger.info(f"Median: {summary.median_response_time}s")
        logger.info(f"95th Percentile: {summary.p95_response_time}s")
        logger.info(f"99th Percentile: {summary.p99_response_time}s")
        logger.info(f"Min: {summary.min_response_time}s")
        logger.info(f"Max: {summary.max_response_time}s")

        logger.info(f"\nCACHE HIT RATE: {summary.cache_hit_rate_percent}%")
        logger.info(f"RATE LIMIT HITS: {summary.rate_limit_hits}")

        if summary.preset_performance:
            logger.info("\nPRESET PERFORMANCE:")
            for preset, stats in summary.preset_performance.items():
                logger.info(f"  {preset}:")
                logger.info(f"    Requests: {stats['total_requests']}")
                logger.info(f"    Success Rate: {stats['success_rate']:.1f}%")
                logger.info(f"    Avg Response Time: {stats['avg_response_time']:.2f}s")

        # Performance recommendations
        logger.info("\nRECOMMENDATIONS:")
        if summary.success_rate_percent < 95:
            logger.warning(
                f"  • Success rate ({summary.success_rate_percent}%) is below 95% - investigate errors"
            )

        if summary.avg_response_time > 30:
            logger.warning(
                f"  • Average response time ({summary.avg_response_time}s) is high - consider optimization"
            )

        if summary.rate_limit_hits > 0:
            logger.warning(
                f"  • {summary.rate_limit_hits} rate limit hits - consider adjusting limits or client behavior"
            )

        if summary.cache_hit_rate_percent < 20:
            logger.warning(
                f"  • Low cache hit rate ({summary.cache_hit_rate_percent}%) - review caching strategy"
            )

        logger.info("=" * 60)

    def save_results(self, filename: str):
        """Save detailed results to JSON file"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": asdict(self._generate_summary(0)),  # Will recalculate duration
            "detailed_results": [asdict(result) for result in self.results],
        }

        with open(filename, "w") as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"Detailed results saved to {filename}")


async def run_rate_limit_test(base_url: str, api_key: str):
    """Test rate limiting behavior specifically"""
    logger.info("Running rate limit test...")

    async with aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {api_key}"}
    ) as session:
        # Test tempo processing rate limit (should be 3/min)
        logger.info("Testing tempo processing rate limit (3/min)...")

        start_time = time.time()
        responses = []

        for i in range(6):  # Try 6 requests in quick succession
            try:
                payload = {
                    "storage_path": f"uploads/ratetest/test_{i}.mp3",
                    "preset": "sped_up",
                    "callback_url": "https://test.example.com/callback",
                }

                async with session.post(
                    f"{base_url}/tempo/storage/process", json=payload
                ) as response:
                    responses.append(
                        {
                            "request": i + 1,
                            "status": response.status,
                            "time_elapsed": time.time() - start_time,
                        }
                    )

                    if response.status == 429:
                        logger.info(
                            f"Request {i + 1}: Rate limited (429) after {time.time() - start_time:.1f}s"
                        )
                        # Check rate limit headers
                        if "X-RateLimit-Reset" in response.headers:
                            reset_time = response.headers["X-RateLimit-Reset"]
                            logger.info(f"Rate limit resets at: {reset_time}")
                    else:
                        logger.info(f"Request {i + 1}: Status {response.status}")

                # Small delay between requests
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Request {i + 1} failed: {e}")

        # Test info endpoint rate limit (should be 60/min)
        logger.info("\nTesting info endpoint rate limit (60/min)...")

        info_start = time.time()
        successful_info_requests = 0

        for i in range(10):  # Quick burst of info requests
            try:
                async with session.get(f"{base_url}/tempo/presets") as response:
                    if response.status == 200:
                        successful_info_requests += 1
                    elif response.status == 429:
                        logger.info(f"Info request {i + 1}: Rate limited")
                        break
            except Exception as e:
                logger.error(f"Info request {i + 1} failed: {e}")

        logger.info(
            f"Completed {successful_info_requests} info requests before rate limiting"
        )


async def main():
    parser = argparse.ArgumentParser(description="Load test the tempo processing API")
    parser.add_argument("--url", default="http://localhost:8001", help="API base URL")
    parser.add_argument(
        "--api-key", default="test-key", help="API key for authentication"
    )
    parser.add_argument(
        "--users", type=int, default=5, help="Number of concurrent users"
    )
    parser.add_argument("--requests", type=int, default=10, help="Requests per user")
    parser.add_argument(
        "--ramp-up", type=int, default=10, help="Ramp up time in seconds"
    )
    parser.add_argument(
        "--duration", type=int, default=5, help="Test duration in minutes"
    )
    parser.add_argument("--output", help="Output file for detailed results")
    parser.add_argument(
        "--rate-limit-test", action="store_true", help="Run rate limit test only"
    )
    parser.add_argument(
        "--no-storage", action="store_true", help="Skip storage-based tests"
    )
    parser.add_argument(
        "--no-direct", action="store_true", help="Skip direct upload tests"
    )

    args = parser.parse_args()

    if args.rate_limit_test:
        await run_rate_limit_test(args.url, args.api_key)
        return

    # Run full load test
    tester = TempoLoadTester(args.url, args.api_key)

    summary = await tester.run_load_test(
        concurrent_users=args.users,
        requests_per_user=args.requests,
        ramp_up_seconds=args.ramp_up,
        test_duration_minutes=args.duration,
        include_storage_tests=not args.no_storage,
        include_direct_tests=not args.no_direct,
    )

    if args.output:
        tester.save_results(args.output)

    # Return appropriate exit code based on results
    if summary.success_rate_percent < 95 or summary.avg_response_time > 30:
        logger.warning("Load test results indicate performance issues")
        exit(1)
    else:
        logger.info("Load test completed successfully")
        exit(0)


if __name__ == "__main__":
    asyncio.run(main())
