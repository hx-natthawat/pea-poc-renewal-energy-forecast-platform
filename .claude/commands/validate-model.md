# Validate ML Model

You are an ML validation expert for the PEA RE Forecast Platform.

## Task
Validate ML models against TOR accuracy requirements.

## Accuracy Requirements (from TOR)

### RE Forecast (Solar Power Prediction)
| Metric | Target | Description |
|--------|--------|-------------|
| MAPE   | < 10%  | Mean Absolute Percentage Error |
| RMSE   | < 100 kW | Root Mean Square Error |
| R²     | > 0.95 | Coefficient of Determination |

### Voltage Prediction
| Metric | Target | Description |
|--------|--------|-------------|
| MAE    | < 2V   | Mean Absolute Error |
| RMSE   | < 3V   | Root Mean Square Error |
| R²     | > 0.90 | Coefficient of Determination |

## Instructions

1. **Load Model and Test Data**:
   - Load trained model from `ml/models/`
   - Load test dataset (time-series split, not random)
   - Ensure no data leakage

2. **Calculate Metrics**:
   ```python
   from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
   import numpy as np

   def mape(y_true, y_pred):
       return np.mean(np.abs((y_true - y_pred) / y_true)) * 100
   ```

3. **Generate Validation Report**:
   - Overall metrics
   - Metrics by time period (hourly, daily, seasonal)
   - Error distribution analysis
   - Confidence intervals

4. **Output**:
   - Report at `docs/specs/model-validation-report.md`
   - Update `docs/plans/poc-progress.md` with results

5. **Pass/Fail Criteria**:
   - ALL metrics must meet targets
   - If any metric fails, model is NOT production-ready
   - Document improvement recommendations

## Validation Command

```bash
# Run validation in container
docker-compose -f docker/docker-compose.test.yml run --rm ml-service \
  python -m pytest ml/tests/test_model_accuracy.py -v --tb=short
```
