"""
Load Testing Scenarios for PEA RE Forecast Platform.

This file contains Locust load test scenarios to validate:
- TOR requirement: Support 2,000+ RE plants and 300,000+ consumers
- API response time targets: < 500ms
- System throughput under load

Usage:
    # Start Locust web UI
    locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Headless mode (for CI/CD)
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --headless -u 1000 -r 100 -t 5m \
           --csv=load_test_results

    # Distributed mode (multiple workers)
    # Master:
    locust -f tests/load/locustfile.py --master --host=http://localhost:8000
    # Worker:
    locust -f tests/load/locustfile.py --worker --master-host=localhost
"""

import random
from datetime import datetime, timedelta

from locust import HttpUser, between, events, tag, task


# =============================================================================
# Test Data
# =============================================================================

PROSUMER_IDS = [f"prosumer{i}" for i in range(1, 8)]
STATION_ID = "POC_STATION_1"

# Simulated solar measurement features
def generate_solar_features():
    """Generate realistic solar measurement data."""
    hour = datetime.now().hour
    # Simulate daylight hours (6 AM to 6 PM)
    is_daylight = 6 <= hour <= 18

    if is_daylight:
        base_irradiance = 400 + 400 * abs(12 - hour) / 6 * -1 + 800
        irradiance = max(0, base_irradiance + random.uniform(-100, 100))
    else:
        irradiance = random.uniform(0, 10)

    return {
        "timestamp": datetime.now().isoformat(),
        "pyrano1": round(irradiance, 2),
        "pyrano2": round(irradiance * random.uniform(0.95, 1.05), 2),
        "pvtemp1": round(25 + irradiance / 30 + random.uniform(-2, 2), 2),
        "pvtemp2": round(25 + irradiance / 30 + random.uniform(-2, 2), 2),
        "ambtemp": round(28 + random.uniform(-3, 5), 2),
        "windspeed": round(random.uniform(0.5, 8), 2),
    }


def generate_voltage_data():
    """Generate realistic voltage measurement data."""
    return {
        "prosumer_id": random.choice(PROSUMER_IDS),
        "timestamp": datetime.now().isoformat(),
        "voltage": round(230 + random.uniform(-5, 5), 2),
        "active_power": round(random.uniform(0, 5), 3),
        "reactive_power": round(random.uniform(-0.5, 0.5), 3),
    }


# =============================================================================
# User Behaviors
# =============================================================================


class DashboardUser(HttpUser):
    """
    Simulates a dashboard user viewing forecasts and monitoring data.

    This represents operators and analysts using the web dashboard.
    Expected: ~100 concurrent users during peak hours.
    """

    wait_time = between(2, 10)  # Users browse, wait, then click
    weight = 3  # Higher weight - most common user type

    @tag("health")
    @task(1)
    def check_health(self):
        """Check API health - called on page load."""
        with self.client.get("/api/v1/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @tag("forecast", "solar")
    @task(5)
    def get_solar_forecast(self):
        """Get current solar forecast - main dashboard view."""
        self.client.get(
            "/api/v1/forecast/solar/current",
            name="/api/v1/forecast/solar/current"
        )

    @tag("forecast", "voltage")
    @task(3)
    def get_voltage_forecast(self):
        """Get voltage forecasts for prosumers."""
        prosumer_id = random.choice(PROSUMER_IDS)
        self.client.get(
            f"/api/v1/forecast/voltage/prosumer/{prosumer_id}",
            name="/api/v1/forecast/voltage/prosumer/{id}"
        )

    @tag("monitoring")
    @task(2)
    def get_model_health(self):
        """Check model health status."""
        self.client.get(
            "/api/v1/monitoring/health",
            name="/api/v1/monitoring/health"
        )

    @tag("alerts")
    @task(2)
    def get_active_alerts(self):
        """Get active alerts for dashboard."""
        self.client.get(
            "/api/v1/alerts/",
            name="/api/v1/alerts/"
        )

    @tag("dayahead")
    @task(1)
    def get_dayahead_solar(self):
        """Get day-ahead solar forecast."""
        self.client.get(
            "/api/v1/dayahead/solar",
            name="/api/v1/dayahead/solar"
        )

    @tag("history")
    @task(1)
    def get_solar_history(self):
        """Get historical solar data."""
        self.client.get(
            "/api/v1/history/solar/summary",
            name="/api/v1/history/solar/summary"
        )


class APIConsumerUser(HttpUser):
    """
    Simulates automated API consumers (other systems, IoT devices).

    This represents:
    - 2,000+ RE power plants sending data
    - Automated monitoring systems polling for updates
    - Integration systems fetching forecasts

    Expected: High volume, frequent requests.
    """

    wait_time = between(0.5, 2)  # Faster polling
    weight = 5  # Higher weight - represents many automated systems

    @tag("forecast", "solar")
    @task(10)
    def request_solar_prediction(self):
        """Request solar power prediction - most common API call."""
        features = generate_solar_features()
        self.client.post(
            "/api/v1/forecast/solar/predict",
            json=features,
            name="/api/v1/forecast/solar/predict"
        )

    @tag("forecast", "voltage")
    @task(5)
    def request_voltage_prediction(self):
        """Request voltage prediction for a prosumer."""
        prosumer_id = random.choice(PROSUMER_IDS)
        data = generate_voltage_data()
        data["prosumer_id"] = prosumer_id

        self.client.post(
            f"/api/v1/forecast/voltage/predict",
            json=data,
            name="/api/v1/forecast/voltage/predict"
        )

    @tag("health")
    @task(1)
    def health_check(self):
        """Periodic health check."""
        self.client.get("/api/v1/health")


class DataIngestionUser(HttpUser):
    """
    Simulates IoT devices sending measurement data.

    This represents:
    - Solar monitoring equipment
    - Smart meters
    - Prosumer data collectors

    Expected: Continuous stream of data from 300,000+ points.
    """

    wait_time = between(1, 5)  # Measurement intervals
    weight = 10  # Highest weight - represents many IoT devices

    @tag("ingest", "solar")
    @task(3)
    def ingest_solar_measurement(self):
        """Send solar measurement data."""
        data = generate_solar_features()
        data["station_id"] = STATION_ID

        self.client.post(
            "/api/v1/data/ingest/solar",
            json=data,
            name="/api/v1/data/ingest/solar"
        )

    @tag("ingest", "voltage")
    @task(7)
    def ingest_voltage_measurement(self):
        """Send voltage measurement data - more frequent than solar."""
        data = generate_voltage_data()

        self.client.post(
            "/api/v1/data/ingest/voltage",
            json=data,
            name="/api/v1/data/ingest/voltage"
        )


class AnalystUser(HttpUser):
    """
    Simulates analysts running complex queries.

    This represents users running historical analysis,
    generating reports, and doing data exploration.

    Expected: Low volume but complex queries.
    """

    wait_time = between(10, 30)  # Long thinking time
    weight = 1  # Low weight - fewer analysts

    @tag("history", "analysis")
    @task(3)
    def query_historical_solar(self):
        """Query historical solar data with date range."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=random.randint(1, 30))

        self.client.get(
            "/api/v1/history/solar",
            params={
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "interval": random.choice(["5m", "15m", "1h", "1d"]),
            },
            name="/api/v1/history/solar"
        )

    @tag("history", "analysis")
    @task(2)
    def query_historical_voltage(self):
        """Query historical voltage data."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=random.randint(1, 7))

        self.client.get(
            "/api/v1/history/voltage",
            params={
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "prosumer_id": random.choice(PROSUMER_IDS),
            },
            name="/api/v1/history/voltage"
        )

    @tag("comparison")
    @task(2)
    def get_forecast_comparison(self):
        """Get forecast vs actual comparison."""
        self.client.get(
            "/api/v1/comparison/solar",
            params={"days": random.randint(1, 7)},
            name="/api/v1/comparison/solar"
        )

    @tag("monitoring", "performance")
    @task(1)
    def get_model_performance(self):
        """Get model performance metrics."""
        model_type = random.choice(["solar", "voltage"])
        self.client.get(
            f"/api/v1/monitoring/performance/{model_type}",
            params={"days": random.randint(7, 30)},
            name="/api/v1/monitoring/performance/{model_type}"
        )

    @tag("dayahead", "report")
    @task(1)
    def get_dayahead_report(self):
        """Get day-ahead report."""
        self.client.get(
            "/api/v1/dayahead/report",
            name="/api/v1/dayahead/report"
        )


# =============================================================================
# Event Hooks
# =============================================================================


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("=" * 60)
    print("PEA RE Forecast Platform - Load Test Starting")
    print("=" * 60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.user_count if environment.runner else 'N/A'}")
    print()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print()
    print("=" * 60)
    print("Load Test Complete")
    print("=" * 60)

    if environment.stats.total.num_requests > 0:
        print(f"Total Requests: {environment.stats.total.num_requests}")
        print(f"Failures: {environment.stats.total.num_failures}")
        print(f"Failure Rate: {environment.stats.total.fail_ratio * 100:.2f}%")
        print(f"Avg Response Time: {environment.stats.total.avg_response_time:.2f}ms")
        print(f"P95 Response Time: {environment.stats.total.get_response_time_percentile(0.95):.2f}ms")
        print(f"Requests/sec: {environment.stats.total.current_rps:.2f}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track request metrics for TOR compliance."""
    # Log slow requests (TOR requires < 500ms)
    if response_time > 500:
        print(f"SLOW REQUEST: {name} took {response_time:.2f}ms (target: <500ms)")


# =============================================================================
# Custom Scenarios
# =============================================================================


class ScaleTestUser(HttpUser):
    """
    Combined user for scale testing to TOR requirements.

    Simulates mixed workload representing:
    - 2,000+ RE plants
    - 300,000+ consumers

    Target metrics:
    - P95 response time < 500ms
    - Error rate < 1%
    - Sustained throughput
    """

    wait_time = between(0.1, 1)

    @task(50)
    def api_request(self):
        """Mixed API request pattern."""
        endpoint = random.choices(
            [
                ("/api/v1/health", "GET", None),
                ("/api/v1/forecast/solar/current", "GET", None),
                ("/api/v1/forecast/voltage/prosumer/prosumer1", "GET", None),
                ("/api/v1/alerts/", "GET", None),
                ("/api/v1/data/ingest/solar", "POST", generate_solar_features()),
                ("/api/v1/data/ingest/voltage", "POST", generate_voltage_data()),
            ],
            weights=[5, 20, 15, 10, 25, 25],
            k=1
        )[0]

        path, method, data = endpoint

        if method == "GET":
            self.client.get(path, name=path)
        else:
            self.client.post(path, json=data, name=path)
