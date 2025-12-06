# Test API Endpoints

You are an API testing expert for the PEA RE Forecast Platform.

## Task
Comprehensively test all API endpoints before deployment.

## API Endpoints to Test

### Health & Status
- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness probe

### Solar Forecast
- `POST /api/v1/forecast/solar` - Single prediction
- `POST /api/v1/forecast/solar/batch` - Batch prediction
- `GET /api/v1/forecast/solar/history` - Historical predictions

### Voltage Prediction
- `POST /api/v1/forecast/voltage` - Single prediction
- `POST /api/v1/forecast/voltage/batch` - Batch prediction
- `GET /api/v1/forecast/voltage/prosumer/{id}` - Per-prosumer history

### Data Ingestion
- `POST /api/v1/data/solar` - Ingest solar measurements
- `POST /api/v1/data/meter/single-phase` - Ingest 1-phase data
- `POST /api/v1/data/meter/three-phase` - Ingest 3-phase data

### Alerts
- `GET /api/v1/alerts` - List alerts
- `POST /api/v1/alerts/{id}/acknowledge` - Acknowledge alert

## Instructions

1. **Setup Test Environment**:
   ```bash
   docker-compose -f docker/docker-compose.test.yml up -d
   ```

2. **Run API Tests**:
   ```bash
   # Using pytest
   pytest backend/tests/integration/test_api.py -v

   # Using httpie for manual testing
   http POST localhost:8000/api/v1/forecast/solar \
     timestamp="2025-01-15T10:00:00+07:00" \
     pyrano1:=850.5 pyrano2:=842.3 \
     pvtemp1:=45.2 pvtemp2:=44.8 \
     ambtemp:=32.5 windspeed:=2.3
   ```

3. **Test Criteria**:
   | Test Type | Criteria |
   |-----------|----------|
   | Response time | < 500ms for single prediction |
   | Batch throughput | > 100 predictions/second |
   | Error handling | Proper 4xx/5xx responses |
   | Validation | Reject invalid inputs |

4. **Output**:
   - Test report at `docs/specs/api-test-report.md`
   - Update `docs/plans/poc-progress.md`

5. **Fix Until Pass**:
   - If any test fails, fix the issue
   - Re-run tests
   - Only proceed when ALL tests pass
