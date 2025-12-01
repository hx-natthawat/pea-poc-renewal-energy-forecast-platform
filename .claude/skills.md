# PEA RE Forecast Platform - Claude Skills

This document defines specialized skills for the PEA RE Forecast Platform development.

## Skill Categories

### 1. Data Engineering Skills

- **POC Data Analysis**: Analyze Excel data from POC_Data.xlsx
- **Data Simulation**: Generate realistic simulation data for Thailand conditions
- **ETL Pipeline**: Build data ingestion pipelines

### 2. ML Engineering Skills

- **Solar Forecasting**: XGBoost/LSTM models for power prediction
- **Voltage Prediction**: Neural network models for voltage forecasting
- **Model Validation**: Ensure models meet TOR accuracy requirements

### 3. Backend Development Skills

- **FastAPI Development**: RESTful APIs with async support
- **TimescaleDB Integration**: Time-series database operations
- **Keycloak Auth**: OAuth2/OIDC authentication

### 4. Frontend Development Skills

- **React Dashboard**: Real-time visualization dashboards
- **Chart Components**: Recharts/D3.js for time-series visualization
- **WebSocket Integration**: Real-time data updates

### 5. DevOps Skills

- **Docker Compose**: Local development environment
- **Kind Cluster**: Local Kubernetes testing
- **GitLab CI/CD**: Pipeline configuration
- **ArgoCD GitOps**: Kubernetes deployment automation

### 6. Domain Knowledge Skills

- **Thailand Solar Patterns**: Tropical climate, monsoon seasons
- **Distribution Networks**: Low-voltage prosumer networks
- **PEA Standards**: Thai electrical utility requirements

## Skill Application Matrix

| Task | Required Skills |
|------|-----------------|
| Analyze POC data | POC Data Analysis |
| Generate training data | Data Simulation, Thailand Solar Patterns |
| Train solar model | Solar Forecasting, Model Validation |
| Train voltage model | Voltage Prediction, Distribution Networks |
| Build API | FastAPI Development, TimescaleDB Integration |
| Build dashboard | React Dashboard, Chart Components |
| Deploy locally | Docker Compose, Kind Cluster |
| Deploy to PEA | GitLab CI/CD, ArgoCD GitOps |

## Usage with Claude Code

When working on tasks, Claude Code will automatically apply relevant skills based on context. You can also explicitly invoke skills through slash commands:

```bash
# Data analysis skill
/analyze-poc-data

# Simulation skill
/simulate-solar
/simulate-voltage

# Validation skill
/validate-model

# Deployment skill
/deploy-local
```
