# PEA RE Forecast Platform - Demo Scenarios

> **Version**: 1.0.0
> **Last Updated**: 2025-12-03
> **Duration**: 15-20 minutes

---

## Demo Overview

This document outlines demonstration scenarios for the PEA RE Forecast Platform POC, showcasing:
1. Solar power forecasting capabilities
2. Voltage monitoring and prediction
3. Real-time dashboard updates
4. API functionality

---

## Pre-Demo Checklist

- [ ] Kind cluster running (`kubectl get nodes`)
- [ ] All pods healthy (`kubectl get pods -n pea-forecast`)
- [ ] Port forwards active (3000, 8000)
- [ ] Browser open to http://localhost:3000
- [ ] Terminal ready for API demonstrations
- [ ] Data loaded in database

---

## Demo Script

### Scene 1: Platform Overview (3 min)

**Narration**: "Welcome to the PEA RE Forecast Platform - a comprehensive solution for renewable energy forecasting and grid voltage monitoring."

**Actions**:
1. Open http://localhost:3000 in browser
2. Point out the main dashboard components:
   - Solar Output card (3,542 kW typical)
   - Average Voltage card (228.5 V)
   - Active Alerts card (0 - all systems normal)
   - System Status (Online with WebSocket)
3. Show the navigation tabs: Overview, Solar Forecast, Voltage Monitor

**Key Points**:
- Real-time WebSocket connection indicator
- PEA brand colors and Thai language support
- Responsive design for different screen sizes

---

### Scene 2: Solar Power Forecasting (5 min)

**Narration**: "The platform predicts solar power output with high accuracy, helping grid operators plan for renewable energy integration."

**Actions**:

1. **View Solar Chart**
   - Click "Solar Forecast" tab
   - Show the solar power curve throughout the day
   - Point out actual (orange) vs predicted (purple) lines

2. **Explain Key Metrics**
   - Current Output
   - Peak Today
   - Accuracy percentage (94.2%)

3. **API Demonstration** (Terminal)
   ```bash
   # Get solar forecast for specific conditions
   curl -X POST http://localhost:8000/api/v1/forecast/solar \
     -H "Content-Type: application/json" \
     -d '{
       "timestamp": "2024-06-01T12:00:00",
       "features": {
         "pyrano1": 900,
         "pyrano2": 895,
         "pvtemp1": 48,
         "pvtemp2": 47,
         "ambtemp": 35,
         "windspeed": 2.0
       }
     }'
   ```

4. **Explain ML Model**
   - RandomForest with 500 estimators
   - 59 features including temporal, physics-based, and lag features
   - Trained on 30 days of simulated data
   - **MAPE: 9.74%** (target: <10%)

**Key Points**:
- Model accuracy meets TOR requirements
- Real-time predictions available
- Historical data visualization

---

### Scene 3: Voltage Monitoring (5 min)

**Narration**: "The platform monitors voltage levels across the low-voltage distribution network, predicting potential violations before they occur."

**Actions**:

1. **View Voltage Chart**
   - Click "Voltage Monitor" tab
   - Show voltage levels for 7 prosumers
   - Point out the voltage limits (218V - 242V)

2. **Explain Network Topology**
   - 7 prosumers across 3 phases (A, B, C)
   - Each prosumer has solar PV
   - Some have EV chargers

3. **Show Prosumer Status**
   - Color-coded indicators (green=normal, yellow=warning, red=critical)
   - Phase information (A, B, C)
   - Current voltage reading

4. **API Demonstration** (Terminal)
   ```bash
   # Get voltage prediction for prosumers
   curl -X POST http://localhost:8000/api/v1/forecast/voltage \
     -H "Content-Type: application/json" \
     -d '{
       "timestamp": "2024-06-01T14:00:00",
       "prosumer_ids": ["prosumer1", "prosumer2"]
     }'
   ```

5. **Explain ML Model**
   - XGBoost regressor
   - 47 features per prosumer
   - **MAE: 0.036V** (target: <2V)
   - **R²: 0.9949** (target: >0.90)

**Key Points**:
- Exceeds accuracy requirements significantly
- Phase-aware monitoring
- Proactive violation detection

---

### Scene 4: Real-Time Updates (3 min)

**Narration**: "The platform provides real-time updates via WebSocket, ensuring operators always have the latest data."

**Actions**:

1. **Show WebSocket Status**
   - Point out "Online" indicator in header
   - Show "LIVE" badge on charts

2. **Demonstrate WebSocket Connection** (Terminal)
   ```bash
   # Connect to WebSocket
   python3 -c "
   import asyncio
   import websockets

   async def test():
       async with websockets.connect('ws://localhost:8000/api/v1/ws?channels=all') as ws:
           print('Connected!')
           for i in range(3):
               msg = await asyncio.wait_for(ws.recv(), timeout=10)
               print(f'Message {i+1}:', msg[:100])

   asyncio.run(test())
   "
   ```

3. **Explain Architecture**
   - WebSocket channels: solar, voltage, alerts
   - Automatic reconnection
   - Ping/pong keep-alive

---

### Scene 5: API Documentation (2 min)

**Narration**: "All functionality is available through a well-documented REST API."

**Actions**:

1. **Open Swagger UI**
   - Navigate to http://localhost:8000/api/v1/docs

2. **Show Available Endpoints**
   - `/health` - System health
   - `/data/solar/latest` - Historical solar data
   - `/data/voltage/latest` - Historical voltage data
   - `/forecast/solar` - Solar predictions
   - `/forecast/voltage` - Voltage predictions
   - `/alerts` - Alert management

3. **Try an Endpoint**
   - Click on `/api/v1/health`
   - Click "Try it out" then "Execute"
   - Show the response

---

### Scene 6: Model Performance Summary (2 min)

**Narration**: "Let me summarize the ML model performance against TOR requirements."

**Show Performance Table**:

| Model | Metric | Achieved | Target | Status |
|-------|--------|----------|--------|--------|
| Solar | MAPE | 9.74% | <10% | PASS |
| Solar | RMSE | 35.60 kW | <100 kW | PASS |
| Solar | R² | 0.9686 | >0.95 | PASS |
| Voltage | MAE | 0.036 V | <2 V | PASS |
| Voltage | RMSE | 0.101 V | <3 V | PASS |
| Voltage | R² | 0.9949 | >0.90 | PASS |

**Key Points**:
- All TOR accuracy requirements met
- Models ready for production deployment
- Scalable architecture supports 2,000+ RE plants and 300,000+ consumers

---

## Q&A Preparation

### Expected Questions

1. **"How does the system handle data from multiple RE plants?"**
   - TimescaleDB with hypertables for time-series data
   - Designed to scale to 2,000+ plants
   - Partitioning by time and station_id

2. **"What happens if the model accuracy degrades?"**
   - MLflow model registry for version control
   - Monitoring metrics tracked in database
   - Easy model retraining with new data

3. **"How does the system integrate with existing PEA systems?"**
   - REST API for integration
   - Kafka support for streaming data (TOR requirement)
   - Keycloak for authentication (planned)

4. **"What is the latency for predictions?"**
   - Voltage: P95 < 400ms
   - Solar: P95 < 1.5s (with optimization: <500ms via Redis caching)

5. **"Can this run on PEA infrastructure?"**
   - Kubernetes-native deployment
   - Resource requirements match TOR specifications
   - Uses all mandated software stack

---

## Backup Demonstrations

If live demo fails, use these backup options:

### Option 1: API-Only Demo
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get solar data
curl "http://localhost:8000/api/v1/data/solar/latest?hours=24"

# Get voltage data
curl "http://localhost:8000/api/v1/data/voltage/latest?hours=2"
```

### Option 2: Screenshots
Prepare screenshots of:
- Dashboard overview
- Solar forecast chart
- Voltage monitoring view
- API documentation

### Option 3: Video Recording
Pre-record a demo video as backup

---

## Post-Demo Actions

1. Save any generated data/outputs
2. Document feedback received
3. Update poc-progress.md with demo completion
4. Plan next steps based on stakeholder input

---

*Document Version: 1.0.0*
*Last Updated: 2025-12-03*
