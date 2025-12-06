#!/usr/bin/env python3
"""
Load Testing Script for PEA RE Forecast Platform API.

Tests API endpoints under concurrent load to verify:
- Response time < 500ms (per TOR)
- System handles concurrent requests
- No degradation under sustained load

Usage:
    python test_api_load.py
    python test_api_load.py --concurrent 50 --requests 200
"""

import argparse
import asyncio
import statistics
import time
from dataclasses import dataclass
from datetime import datetime

try:
    import aiohttp
except ImportError:
    print("Installing aiohttp...")
    import subprocess

    subprocess.run(["pip", "install", "aiohttp"], check=True)
    import aiohttp


@dataclass
class LoadTestResult:
    """Results from a load test run."""

    endpoint: str
    total_requests: int
    successful: int
    failed: int
    avg_response_ms: float
    min_response_ms: float
    max_response_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    requests_per_second: float
    total_duration_s: float


class APILoadTester:
    """Load tester for PEA RE Forecast Platform API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: list[LoadTestResult] = []

    async def test_health(self, session: aiohttp.ClientSession) -> tuple[bool, float]:
        """Test health endpoint."""
        start = time.perf_counter()
        try:
            async with session.get(f"{self.base_url}/api/v1/health") as resp:
                success = resp.status == 200
                return success, (time.perf_counter() - start) * 1000
        except Exception:
            return False, (time.perf_counter() - start) * 1000

    async def test_solar_forecast(
        self, session: aiohttp.ClientSession
    ) -> tuple[bool, float]:
        """Test solar forecast endpoint."""
        payload = {
            "timestamp": datetime.now().isoformat(),
            "station_id": "POC_STATION_1",
            "horizon_minutes": 60,
            "features": {
                "pyrano1": 850.5,
                "pyrano2": 842.3,
                "pvtemp1": 45.2,
                "pvtemp2": 44.8,
                "ambtemp": 32.5,
                "windspeed": 2.3,
            },
        }
        start = time.perf_counter()
        try:
            async with session.post(
                f"{self.base_url}/api/v1/forecast/solar", json=payload
            ) as resp:
                success = resp.status == 200
                return success, (time.perf_counter() - start) * 1000
        except Exception:
            return False, (time.perf_counter() - start) * 1000

    async def test_voltage_forecast(
        self, session: aiohttp.ClientSession
    ) -> tuple[bool, float]:
        """Test voltage forecast endpoint."""
        payload = {
            "timestamp": datetime.now().isoformat(),
            "prosumer_ids": ["prosumer1", "prosumer3", "prosumer5"],
            "horizon_minutes": 15,
        }
        start = time.perf_counter()
        try:
            async with session.post(
                f"{self.base_url}/api/v1/forecast/voltage", json=payload
            ) as resp:
                success = resp.status == 200
                return success, (time.perf_counter() - start) * 1000
        except Exception:
            return False, (time.perf_counter() - start) * 1000

    async def test_solar_data(
        self, session: aiohttp.ClientSession
    ) -> tuple[bool, float]:
        """Test solar data endpoint."""
        start = time.perf_counter()
        try:
            async with session.get(
                f"{self.base_url}/api/v1/data/solar/latest?hours=1"
            ) as resp:
                success = resp.status == 200
                return success, (time.perf_counter() - start) * 1000
        except Exception:
            return False, (time.perf_counter() - start) * 1000

    async def test_voltage_data(
        self, session: aiohttp.ClientSession
    ) -> tuple[bool, float]:
        """Test voltage data endpoint."""
        start = time.perf_counter()
        try:
            async with session.get(
                f"{self.base_url}/api/v1/data/voltage/latest?hours=1"
            ) as resp:
                success = resp.status == 200
                return success, (time.perf_counter() - start) * 1000
        except Exception:
            return False, (time.perf_counter() - start) * 1000

    async def run_load_test(
        self,
        test_func,
        endpoint_name: str,
        concurrent: int = 10,
        total_requests: int = 100,
    ) -> LoadTestResult:
        """Run load test for a specific endpoint."""
        print(f"\n{'='*60}")
        print(f"Testing: {endpoint_name}")
        print(f"Concurrent: {concurrent} | Total Requests: {total_requests}")
        print(f"{'='*60}")

        response_times: list[float] = []
        successful = 0
        failed = 0

        connector = aiohttp.TCPConnector(limit=concurrent)
        timeout = aiohttp.ClientTimeout(total=30)

        start_time = time.perf_counter()

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            # Create semaphore to limit concurrency
            sem = asyncio.Semaphore(concurrent)

            async def bounded_test():
                async with sem:
                    return await test_func(session)

            # Run all requests
            tasks = [bounded_test() for _ in range(total_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    failed += 1
                    response_times.append(30000)  # Timeout
                else:
                    success, resp_time = result
                    response_times.append(resp_time)
                    if success:
                        successful += 1
                    else:
                        failed += 1

        total_duration = time.perf_counter() - start_time

        # Calculate statistics
        sorted_times = sorted(response_times)
        result = LoadTestResult(
            endpoint=endpoint_name,
            total_requests=total_requests,
            successful=successful,
            failed=failed,
            avg_response_ms=statistics.mean(response_times),
            min_response_ms=min(response_times),
            max_response_ms=max(response_times),
            p50_ms=sorted_times[int(len(sorted_times) * 0.50)],
            p95_ms=sorted_times[int(len(sorted_times) * 0.95)],
            p99_ms=sorted_times[int(len(sorted_times) * 0.99)],
            requests_per_second=total_requests / total_duration,
            total_duration_s=total_duration,
        )

        self.results.append(result)
        self._print_result(result)
        return result

    def _print_result(self, result: LoadTestResult):
        """Print load test result."""
        success_rate = (result.successful / result.total_requests) * 100
        target_met = result.p95_ms < 500

        print(f"\n📊 Results for {result.endpoint}:")
        print(
            f"   Success Rate: {success_rate:.1f}% ({result.successful}/{result.total_requests})"
        )
        print(f"   Avg Response:  {result.avg_response_ms:.1f} ms")
        print(f"   Min Response:  {result.min_response_ms:.1f} ms")
        print(f"   Max Response:  {result.max_response_ms:.1f} ms")
        print(f"   P50 (median):  {result.p50_ms:.1f} ms")
        print(
            f"   P95:           {result.p95_ms:.1f} ms {'✅' if target_met else '❌'} (target: <500ms)"
        )
        print(f"   P99:           {result.p99_ms:.1f} ms")
        print(f"   Throughput:    {result.requests_per_second:.1f} req/s")
        print(f"   Total Time:    {result.total_duration_s:.2f} s")

    def print_summary(self):
        """Print summary of all load tests."""
        print("\n" + "=" * 70)
        print("LOAD TEST SUMMARY")
        print("=" * 70)

        all_passed = True
        for result in self.results:
            target_met = result.p95_ms < 500
            success_rate = (result.successful / result.total_requests) * 100

            status = "✅ PASS" if (target_met and success_rate >= 99) else "❌ FAIL"
            if not (target_met and success_rate >= 99):
                all_passed = False

            print(f"\n{result.endpoint}:")
            print(
                f"   {status} | P95: {result.p95_ms:.1f}ms | Success: {success_rate:.1f}% | {result.requests_per_second:.1f} req/s"
            )

        print("\n" + "=" * 70)
        if all_passed:
            print("✅ ALL LOAD TESTS PASSED")
        else:
            print("❌ SOME LOAD TESTS FAILED")
        print("=" * 70)

        return all_passed


async def main():
    parser = argparse.ArgumentParser(description="Load test PEA RE Forecast API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument(
        "--concurrent", type=int, default=20, help="Concurrent requests"
    )
    parser.add_argument(
        "--requests", type=int, default=100, help="Total requests per endpoint"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("PEA RE Forecast Platform - API Load Testing")
    print("=" * 70)
    print(f"Base URL: {args.url}")
    print(f"Concurrent Requests: {args.concurrent}")
    print(f"Total Requests per Endpoint: {args.requests}")
    print("Target: P95 Response Time < 500ms")

    tester = APILoadTester(args.url)

    # Test endpoints
    endpoints = [
        (tester.test_health, "GET /api/v1/health"),
        (tester.test_solar_data, "GET /api/v1/data/solar/latest"),
        (tester.test_voltage_data, "GET /api/v1/data/voltage/latest"),
        (tester.test_solar_forecast, "POST /api/v1/forecast/solar"),
        (tester.test_voltage_forecast, "POST /api/v1/forecast/voltage"),
    ]

    for test_func, name in endpoints:
        await tester.run_load_test(
            test_func, name, concurrent=args.concurrent, total_requests=args.requests
        )

    # Print summary
    all_passed = tester.print_summary()

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
