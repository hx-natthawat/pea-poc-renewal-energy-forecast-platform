# CLAUDE.md - PEA RE Forecast Platform

> **Version**: 2.0.0  
> **Last Updated**: December 2024  
> **Project Code**: PEA-REF-2024  
> **TOR Reference**: Terms of Reference (TOR) แพลตฟอร์มสำหรับศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียนของ กฟภ. (PEA RE Forecast Platform)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [TOR Requirements Summary](#tor-requirements-summary)
3. [Infrastructure Specifications](#infrastructure-specifications)
4. [Required Software Stack (Per TOR)](#required-software-stack-per-tor)
5. [Technology Implementation](#technology-implementation)
6. [Project Structure](#project-structure)
7. [Database Schema](#database-schema)
8. [API Specifications](#api-specifications)
9. [ML Model Guidelines](#ml-model-guidelines)
10. [Network Topology](#network-topology)
11. [Data Dictionary](#data-dictionary)
12. [Coding Standards](#coding-standards)
13. [Environment Configuration](#environment-configuration)
14. [Development Commands](#development-commands)
15. [Deployment Guide](#deployment-guide)
16. [Testing Requirements](#testing-requirements)
17. [Implementation Checklist](#implementation-checklist)
18. [Troubleshooting](#troubleshooting)

---

## Project Overview

### Platform Description

The **PEA Renewable Energy Forecast Platform** (แพลตฟอร์มศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียน) is a comprehensive system for the Provincial Electricity Authority of Thailand (กฟภ.) that provides:

1. **RE Forecast Module (พยากรณ์กำลังผลิตไฟฟ้าพลังงานหมุนเวียน)**
   - Predicts solar PV power output from environmental parameters
   - Supports day-ahead, intraday, and real-time forecasting
   - Target accuracy: MAPE < 10%, RMSE < 100 kW, R² > 0.95

2. **Voltage Prediction Module (พยากรณ์แรงดันไฟฟ้า)**
   - Predicts voltage levels across low-voltage distribution networks
   - Monitors prosumer connections across three phases
   - Target accuracy: MAE < 2V

### Key Objectives

- Forecast renewable energy generation for grid stability
- Predict voltage violations before they occur
- Support grid operators with real-time decision making
- Scale to support **≥ 2,000 RE power plants** and **≥ 300,000 consumers**

---

## TOR Requirements Summary

### Section 7.1: System Installation Requirements (ข้อกำหนดการติดตั้งระบบ)

#### 7.1.1 - Hardware Resources (ทรัพยากรที่ กฟภ. จัดให้)

The contractor must install and configure the PEA RE Forecast Platform on PEA's server resources as specified:

| Server Type | CPU | RAM | Storage | OS |
|-------------|-----|-----|---------|-----|
| **Web Server** | 4 Core | 6 GB | C: 50 GB, D: 80 GB | Ubuntu Server 22.04 LTS |
| **AI/ML Server** | 16 Core | 64 GB | C: 50 GB, D: 100 GB | Ubuntu Server 22.04 LTS |
| **Database Server** | 8 Core | 32 GB | C: 50 GB, D: 200 GB | Ubuntu Server 22.04 LTS |

> **ตารางที่ 1**: ตารางแสดงทรัพยากรที่ กฟภ. จัดให้ผู้รับจ้างใช้ในการพัฒนาระบบ PEA RE Forecast Platform

**Note**: Contractor may propose additional resources with supporting calculations (แนบเอกสารหลักฐานแสดงการคำนวณความต้องการใช้งานทรัพยากรให้ กฟภ. เห็นชอบ)

#### 7.1.2 - Additional Resources (ทรัพยากรอื่นๆ เพิ่มเติม)

Contractor may propose additional hardware beyond Table 1 specifications per Section 7.1.1, with cost responsibility for any additional expenses (ค่าใช้จ่ายอื่นๆ ที่เกี่ยวข้อง)

#### 7.1.3 - Software Requirements (Software ตามตารางที่ 2)

System must be developed using software from Table 2 (see [Required Software Stack](#required-software-stack-per-tor)). Contractor may propose additional software with full cost responsibility for licensing (ผู้รับจ้างต้องเป็นผู้รับผิดชอบค่าใช้จ่ายในส่วน Software ที่เสนอเพิ่ม รวมทั้งค่าใช้จ่ายอื่นๆ ที่เกี่ยวข้อง)

#### 7.1.4 - Deployment Requirements (การติดตั้งบนเครื่องคอมพิวเตอร์แม่ข่าย)

- Must be deployed on **PEA's server infrastructure** (เครื่องคอมพิวเตอร์แม่ข่าย Server ของ กฟภ.)
- Must implement **CI/CD** (Continuous Integration and Continuous Deployment)
- Must coordinate with PEA's system administrators (ร่วมกับผู้ดูแลระบบของ กฟภ.)
- Delivery timeline per PEA specifications (ระยะเวลาการส่งมอบผลิตภัณฑ์ หรือตามที่ กฟภ. กำหนด)

#### 7.1.5 - Software Licensing (ลิขสิทธิ์การใช้งาน)

- All software and databases must be **legally licensed** (ลิขสิทธิ์การใช้งานถูกต้องตามกฎหมาย)
- Must be usable **continuously throughout the project lifecycle** (สามารถใช้งานได้ต่อเนื่องตลอดอายุการใช้งาน)
- **No additional licensing costs** to PEA after deployment (โดย กฟภ. จะต้องไม่มีค่าใช้จ่ายใดๆ เพิ่มเติม)

#### 7.1.6 - Security and Audit Requirements (Log และ Audit Trail)

System must implement per PEA standards (ตามมาตรฐานที่ กฟภ. กำหนด):
- **Access Logs** (Log การเข้าใช้งาน)
- **Attack Detection Logs** (การโจมตีระบบ)
- **Audit Trail** for compliance

#### 7.1.7 - Scalability Requirements (ความสามารถรองรับข้อมูล)

Platform must support data import from:
- **≥ 2,000 RE Power Plants** (แหล่งผลิตไฟฟ้าพลังงานหมุนเวียน จำนวนไม่น้อยกว่า 2,000 โรงไฟฟ้า)
  - Connected to PEA grid (จุดเชื่อมต่อระบบโครงข่ายไฟฟ้า กฟภ.)
- **≥ 300,000 Electricity Consumers** (ผู้ใช้ไฟฟ้าไม่น้อยกว่า 300,000 ราย)

---

## Infrastructure Specifications

### Server Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PEA DATA CENTER                                    │
│                    (ศูนย์ข้อมูลของ กฟภ.)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │    WEB SERVER       │  │   AI/ML SERVER      │  │  DATABASE SERVER    │  │
│  │                     │  │                     │  │                     │  │
│  │  CPU: 4 Core        │  │  CPU: 16 Core       │  │  CPU: 8 Core        │  │
│  │  RAM: 6 GB          │  │  RAM: 64 GB         │  │  RAM: 32 GB         │  │
│  │  HDD C: 50 GB       │  │  HDD C: 50 GB       │  │  HDD C: 50 GB       │  │
│  │  HDD D: 80 GB       │  │  HDD D: 100 GB      │  │  HDD D: 200 GB      │  │
│  │  Ubuntu 22.04 LTS   │  │  Ubuntu 22.04 LTS   │  │  Ubuntu 22.04 LTS   │  │
│  │                     │  │                     │  │                     │  │
│  │  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │  │
│  │  │ Nginx        │  │  │  │ ML Models     │  │  │  │ TimescaleDB   │  │  │
│  │  │ React SPA    │  │  │  │ TensorFlow    │  │  │  │ PostgreSQL 15 │  │  │
│  │  │ Kong API GW  │  │  │  │ XGBoost       │  │  │  │ Redis 7       │  │  │
│  │  │ FastAPI      │  │  │  │ MLflow        │  │  │  │               │  │  │
│  │  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │  │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘  │
│             │                        │                        │             │
│             └────────────────────────┼────────────────────────┘             │
│                                      │                                      │
│  ┌───────────────────────────────────┴─────────────────────────────────┐    │
│  │                      KUBERNETES CLUSTER                             │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │  │ Containerd  │ │ Cilium CNI  │ │  Longhorn   │ │    Helm     │   │    │
│  │  │  Runtime    │ │  Network    │ │  Storage    │ │  Charts     │   │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    SUPPORTING SERVICES                              │    │
│  │                                                                     │    │
│  │  CI/CD:        Argo, GitLab                                        │    │
│  │  Security:     Keycloak, Vault, Trivy, SonarQube, Black Duck       │    │
│  │  Messaging:    Kafka, RabbitMQ                                     │    │
│  │  Observability: Prometheus, Grafana, Jaeger, Opensearch, Fluentbit │    │
│  │  API Gateway:  Kong, ApiSix                                        │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Resource Allocation Plan

```yaml
# Resource allocation per component

web_server:
  total_cpu: 4
  total_ram: 6GB
  allocation:
    nginx: { cpu: 0.5, ram: 512MB }
    react_app: { cpu: 0.5, ram: 512MB }
    fastapi: { cpu: 2, ram: 3GB }
    kong: { cpu: 1, ram: 1.5GB }

ml_server:
  total_cpu: 16
  total_ram: 64GB
  allocation:
    model_inference: { cpu: 8, ram: 32GB }
    model_training: { cpu: 6, ram: 24GB }
    mlflow: { cpu: 2, ram: 8GB }

database_server:
  total_cpu: 8
  total_ram: 32GB
  allocation:
    timescaledb: { cpu: 6, ram: 24GB }
    redis: { cpu: 2, ram: 8GB }
```

---

## Required Software Stack (Per TOR)

### Table 2: Mandatory Software Components (ตารางที่ 2)

> ตารางแสดง Software ที่กำหนดให้ผู้รับจ้างใช้ในการพัฒนาระบบ PEA RE Forecast Platform

| Category | Required Tools | Implementation |
|----------|----------------|----------------|
| **Application Definition & Image Build** | Helm | K8s package manager |
| **CI/CD** | Argo, GitLab | GitLab CI + ArgoCD GitOps |
| **Database** | Microsoft SQL, PostgreSQL, Redis | PostgreSQL + TimescaleDB, Redis |
| **Streaming & Messaging** | RabbitMQ, Kafka | Apache Kafka |
| **Scheduling & Orchestration** | Kubernetes | K8s 1.28+ |
| **API Gateway** | Kong, ApiSix | Kong Gateway |
| **Storage** | MINIO, Longhorn, Ceph | Longhorn for K8s |
| **Security & Compliance** | Keycloak, Black Duck, Trivy, Sonarqube, Fortify SCA, Nessus | Full stack |
| **Container Registry** | GitLab Registry | Integrated CI/CD |
| **Observability** | Fluentbit, Prometheus, Jaeger, Grafana, Opensearch, Sentry | Full observability |
| **Cloud Native Network** | Cilium | eBPF networking |
| **Key Management** | Hashicorp Vault | Secrets management |
| **Container Runtime** | Containerd | K8s runtime |
| **Service Proxy** | Nginx | Ingress + reverse proxy |

### Software Version Matrix

```yaml
# versions.yaml - TOR Compliant Versions

# Core Runtime
runtime:
  python: "3.11.x"
  node: "20.x LTS"
  ubuntu: "22.04 LTS"

# Databases (TOR: Microsoft SQL, PostgreSQL, Redis)
databases:
  postgresql: "15.x"
  timescaledb: "2.13.x"  # PostgreSQL extension
  redis: "7.2.x"

# Kubernetes Stack (TOR: Kubernetes, Containerd, Helm)
kubernetes:
  kubernetes: "1.28.x"
  containerd: "1.7.x"
  helm: "3.13.x"
  cilium: "1.14.x"       # TOR: Cloud Native Network

# CI/CD (TOR: Argo, GitLab)
cicd:
  gitlab: "16.6.x"
  argocd: "2.9.x"
  gitlab_registry: "integrated"

# Messaging (TOR: RabbitMQ, Kafka)
messaging:
  kafka: "3.6.x"
  rabbitmq: "3.12.x"

# API Gateway (TOR: Kong, ApiSix)
api_gateway:
  kong: "3.5.x"
  apisix: "3.7.x"

# Security (TOR: Keycloak, Black Duck, Trivy, Sonarqube, Fortify SCA, Nessus)
security:
  keycloak: "23.0.x"
  vault: "1.15.x"        # TOR: Key Management
  trivy: "0.48.x"
  sonarqube: "10.3.x"
  black_duck: "latest"
  nessus: "latest"

# Observability (TOR: Fluentbit, Prometheus, Jaeger, Grafana, Opensearch, Sentry)
observability:
  prometheus: "2.48.x"
  grafana: "10.2.x"
  jaeger: "1.52.x"
  opensearch: "2.11.x"
  fluentbit: "2.2.x"
  sentry: "23.11.x"

# Storage (TOR: MINIO, Longhorn, Ceph)
storage:
  longhorn: "1.5.x"
  minio: "latest"
  ceph: "18.x"

# Service Proxy (TOR: Nginx)
proxy:
  nginx: "1.25.x"
```

---

## Technology Implementation

### Architecture Decision Records

| Component | TOR Requirement | Implementation | Justification |
|-----------|-----------------|----------------|---------------|
| Primary DB | PostgreSQL | **TimescaleDB 2.13** | PostgreSQL extension, optimized for time-series, hypertables for solar/voltage data |
| Cache | Redis | **Redis 7.2** | Per TOR, prediction caching |
| Backend | Not specified | **FastAPI + Python 3.11** | Async, auto-docs, ML ecosystem |
| Frontend | Not specified | **React 18 + TypeScript** | Industry standard, rich ecosystem |
| ML Framework | Not specified | **XGBoost + TensorFlow** | Tabular (XGBoost) + Sequence (LSTM) |
| Container Runtime | Containerd | **Containerd 1.7** | Per TOR |
| Orchestration | Kubernetes | **Kubernetes 1.28** | Per TOR |
| CI/CD | GitLab, Argo | **GitLab CI + ArgoCD** | Per TOR |
| API Gateway | Kong | **Kong 3.5** | Per TOR |
| Auth | Keycloak | **Keycloak 23** | Per TOR |
| Secrets | Vault | **Hashicorp Vault 1.15** | Per TOR |
| Monitoring | Prometheus, Grafana | **Prometheus + Grafana** | Per TOR |
| Logging | Fluentbit, Opensearch | **Fluentbit → Opensearch** | Per TOR |
| Tracing | Jaeger | **Jaeger 1.52** | Per TOR |
| Network | Cilium | **Cilium 1.14** | Per TOR |
| Storage | Longhorn | **Longhorn 1.5** | Per TOR, K8s native |

---

## Project Structure

```
pea-re-forecast/
├── CLAUDE.md                          # This file - Claude Code reference
├── README.md                          # Project overview
├── CHANGELOG.md                       # Version history
├── LICENSE                            # License file
│
├── .gitlab-ci.yml                     # GitLab CI/CD (TOR: GitLab)
├── .gitignore
├── .env.example
│
├── docker/
│   ├── docker-compose.yml             # Local development
│   ├── docker-compose.prod.yml        # Production simulation
│   └── docker-compose.test.yml        # Testing
│
├── backend/                           # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # Application entry
│   │   ├── config.py                  # Settings (Pydantic)
│   │   │
│   │   ├── api/v1/
│   │   │   ├── router.py
│   │   │   ├── endpoints/
│   │   │   │   ├── forecast.py        # Solar forecast
│   │   │   │   ├── voltage.py         # Voltage prediction
│   │   │   │   ├── data.py            # Data ingestion
│   │   │   │   ├── alerts.py          # Alert management
│   │   │   │   └── health.py          # Health checks
│   │   │   └── websocket/
│   │   │       └── realtime.py        # Real-time updates
│   │   │
│   │   ├── core/
│   │   │   ├── security.py            # Keycloak integration
│   │   │   ├── logging.py             # Structured logging
│   │   │   └── middleware.py          # Audit trail middleware
│   │   │
│   │   ├── models/
│   │   │   ├── domain/                # Domain entities
│   │   │   ├── database.py            # SQLAlchemy models
│   │   │   └── schemas/               # Pydantic schemas
│   │   │
│   │   ├── services/
│   │   │   ├── forecast_service.py
│   │   │   ├── voltage_service.py
│   │   │   ├── data_service.py
│   │   │   └── alert_service.py
│   │   │
│   │   ├── ml/
│   │   │   ├── feature_engineering.py
│   │   │   ├── models/
│   │   │   │   ├── solar_model.py
│   │   │   │   └── voltage_model.py
│   │   │   ├── inference.py
│   │   │   └── registry.py            # MLflow integration
│   │   │
│   │   ├── db/
│   │   │   ├── session.py             # Async sessions
│   │   │   ├── repository/
│   │   │   └── migrations/            # Alembic
│   │   │
│   │   └── tasks/                     # Celery tasks
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/                          # React Frontend
│   ├── src/
│   │   ├── app/                       # Next.js App Router
│   │   │   ├── (dashboard)/
│   │   │   │   ├── page.tsx           # Overview
│   │   │   │   ├── solar/
│   │   │   │   ├── voltage/
│   │   │   │   ├── network/
│   │   │   │   └── alerts/
│   │   │   └── api/
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui
│   │   │   ├── dashboard/
│   │   │   ├── charts/
│   │   │   └── network/
│   │   │
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── stores/
│   │   └── types/
│   │
│   ├── package.json
│   ├── Dockerfile
│   └── next.config.js
│
├── ml/                                # ML Training Pipeline
│   ├── data/
│   │   ├── raw/                       # POC_Data.xlsx
│   │   ├── processed/
│   │   └── features/
│   │
│   ├── notebooks/
│   │   ├── 01_eda_solar.ipynb
│   │   ├── 02_eda_voltage.ipynb
│   │   ├── 03_feature_engineering.ipynb
│   │   ├── 04_solar_model.ipynb
│   │   └── 05_voltage_model.ipynb
│   │
│   ├── src/
│   │   ├── data/
│   │   ├── features/
│   │   ├── models/
│   │   ├── training/
│   │   └── evaluation/
│   │
│   ├── scripts/
│   │   ├── train_solar.py
│   │   ├── train_voltage.py
│   │   └── export_models.py
│   │
│   ├── configs/
│   │   ├── solar_config.yaml
│   │   └── voltage_config.yaml
│   │
│   └── models/                        # Saved models
│
├── infrastructure/
│   ├── kubernetes/
│   │   ├── base/
│   │   │   ├── namespace.yaml
│   │   │   ├── configmap.yaml
│   │   │   └── secrets.yaml
│   │   ├── apps/
│   │   │   ├── backend/
│   │   │   ├── frontend/
│   │   │   └── ml-service/
│   │   ├── databases/
│   │   │   ├── timescaledb/
│   │   │   └── redis/
│   │   ├── messaging/
│   │   │   └── kafka/
│   │   ├── security/
│   │   │   ├── keycloak/
│   │   │   └── vault/
│   │   ├── observability/
│   │   │   ├── prometheus/
│   │   │   ├── grafana/
│   │   │   ├── jaeger/
│   │   │   └── opensearch/
│   │   └── ingress/
│   │       └── kong/
│   │
│   ├── helm/
│   │   └── pea-re-forecast/
│   │       ├── Chart.yaml
│   │       ├── values.yaml
│   │       ├── values-staging.yaml
│   │       └── values-prod.yaml
│   │
│   ├── argocd/                        # GitOps (TOR: Argo)
│   │   ├── application.yaml
│   │   └── project.yaml
│   │
│   └── security/
│       ├── trivy/                     # Container scanning
│       ├── sonarqube/                 # Code quality
│       └── vault/                     # Secrets
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── deployment/
│   └── user-guide/
│
└── scripts/
    ├── setup-dev.sh
    ├── run-tests.sh
    └── deploy.sh
```

---

## Database Schema

### TimescaleDB Schema

```sql
-- ============================================================
-- PEA RE Forecast Platform - Database Schema
-- TimescaleDB (PostgreSQL 15 + TimescaleDB 2.13)
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- ============================================================
-- SOLAR MEASUREMENTS (RE Forecast Data)
-- Source: POC_Data.xlsx - Solar sheet
-- ============================================================

CREATE TABLE solar_measurements (
    time TIMESTAMPTZ NOT NULL,
    station_id VARCHAR(50) DEFAULT 'POC_STATION_1',
    
    -- Temperature sensors (°C)
    pvtemp1 DOUBLE PRECISION,
    pvtemp2 DOUBLE PRECISION,
    ambtemp DOUBLE PRECISION,
    
    -- Irradiance sensors (W/m²)
    pyrano1 DOUBLE PRECISION,
    pyrano2 DOUBLE PRECISION,
    
    -- Environmental
    windspeed DOUBLE PRECISION,
    
    -- Output (Target variable)
    power_kw DOUBLE PRECISION,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, station_id)
);

SELECT create_hypertable('solar_measurements', 'time',
    chunk_time_interval => INTERVAL '1 day');

CREATE INDEX idx_solar_station ON solar_measurements (station_id, time DESC);

-- ============================================================
-- PROSUMER NETWORK TOPOLOGY
-- Source: Network diagram from TOR
-- ============================================================

CREATE TABLE prosumers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phase CHAR(1) NOT NULL CHECK (phase IN ('A', 'B', 'C')),
    position_in_phase INTEGER NOT NULL,
    has_pv BOOLEAN DEFAULT false,
    has_ev BOOLEAN DEFAULT false,
    has_battery BOOLEAN DEFAULT false,
    pv_capacity_kw DOUBLE PRECISION,
    transformer_id VARCHAR(50) DEFAULT 'TX_50KVA_01',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert prosumer topology from network diagram
INSERT INTO prosumers (id, name, phase, position_in_phase, has_pv, has_ev) VALUES
    ('prosumer1', 'Prosumer 1', 'A', 3, true, true),
    ('prosumer2', 'Prosumer 2', 'A', 2, true, false),
    ('prosumer3', 'Prosumer 3', 'A', 1, true, false),
    ('prosumer4', 'Prosumer 4', 'B', 2, true, false),
    ('prosumer5', 'Prosumer 5', 'B', 3, true, true),
    ('prosumer6', 'Prosumer 6', 'B', 1, true, false),
    ('prosumer7', 'Prosumer 7', 'C', 1, true, true);

-- ============================================================
-- SINGLE-PHASE METER DATA (Voltage Prediction)
-- Source: POC_Data.xlsx - 1 Phase sheet
-- ============================================================

CREATE TABLE single_phase_meters (
    time TIMESTAMPTZ NOT NULL,
    prosumer_id VARCHAR(50) NOT NULL REFERENCES prosumers(id),
    
    active_power DOUBLE PRECISION,
    reactive_power DOUBLE PRECISION,
    energy_meter_active_power DOUBLE PRECISION,
    energy_meter_current DOUBLE PRECISION,
    energy_meter_voltage DOUBLE PRECISION,  -- Target for prediction
    energy_meter_reactive_power DOUBLE PRECISION,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, prosumer_id)
);

SELECT create_hypertable('single_phase_meters', 'time',
    chunk_time_interval => INTERVAL '1 day');

CREATE INDEX idx_single_phase_prosumer ON single_phase_meters (prosumer_id, time DESC);
CREATE INDEX idx_single_phase_voltage ON single_phase_meters (energy_meter_voltage);

-- ============================================================
-- THREE-PHASE METER DATA (Transformer level)
-- Source: POC_Data.xlsx - 3 Phase sheet
-- ============================================================

CREATE TABLE three_phase_meters (
    time TIMESTAMPTZ NOT NULL,
    meter_id VARCHAR(50) NOT NULL DEFAULT 'TX_METER_01',
    
    -- Phase A
    p1_amp DOUBLE PRECISION,
    p1_volt DOUBLE PRECISION,
    p1_w DOUBLE PRECISION,
    
    -- Phase B
    p2_amp DOUBLE PRECISION,
    p2_volt DOUBLE PRECISION,
    p2_w DOUBLE PRECISION,
    
    -- Phase C
    p3_amp DOUBLE PRECISION,
    p3_volt DOUBLE PRECISION,
    p3_w DOUBLE PRECISION,
    
    -- Reactive power
    q1_var DOUBLE PRECISION,
    q2_var DOUBLE PRECISION,
    q3_var DOUBLE PRECISION,
    
    -- Total
    total_w DOUBLE PRECISION,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, meter_id)
);

SELECT create_hypertable('three_phase_meters', 'time',
    chunk_time_interval => INTERVAL '1 day');

-- ============================================================
-- PREDICTIONS TABLE
-- ============================================================

CREATE TABLE predictions (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    model_type VARCHAR(20) NOT NULL CHECK (model_type IN ('solar', 'voltage')),
    model_version VARCHAR(50) NOT NULL,
    target_id VARCHAR(50),
    horizon_minutes INTEGER,
    
    predicted_value DOUBLE PRECISION NOT NULL,
    confidence_lower DOUBLE PRECISION,
    confidence_upper DOUBLE PRECISION,
    actual_value DOUBLE PRECISION,
    
    features JSONB,
    prediction_time_ms INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, time)
);

SELECT create_hypertable('predictions', 'time',
    chunk_time_interval => INTERVAL '1 day');

-- ============================================================
-- ML MODEL REGISTRY
-- ============================================================

CREATE TABLE ml_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(20) NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}',
    parameters JSONB NOT NULL DEFAULT '{}',
    features_used JSONB NOT NULL DEFAULT '[]',
    file_path VARCHAR(500),
    is_active BOOLEAN DEFAULT false,
    is_production BOOLEAN DEFAULT false,
    trained_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, version)
);

-- ============================================================
-- ALERTS TABLE
-- ============================================================

CREATE TABLE alerts (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    target_id VARCHAR(50),
    message TEXT NOT NULL,
    current_value DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    acknowledged BOOLEAN DEFAULT false,
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, time)
);

SELECT create_hypertable('alerts', 'time',
    chunk_time_interval => INTERVAL '7 days');

-- ============================================================
-- AUDIT LOG (TOR 7.1.6 Requirement)
-- ============================================================

CREATE TABLE audit_log (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(100),
    user_email VARCHAR(255),
    user_ip INET,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    request_method VARCHAR(10),
    request_path TEXT,
    request_body JSONB,
    response_status INTEGER,
    user_agent TEXT,
    session_id VARCHAR(100),
    PRIMARY KEY (id, time)
);

SELECT create_hypertable('audit_log', 'time',
    chunk_time_interval => INTERVAL '7 days');

-- ============================================================
-- DATA RETENTION POLICIES
-- ============================================================

SELECT add_retention_policy('solar_measurements', INTERVAL '2 years');
SELECT add_retention_policy('single_phase_meters', INTERVAL '2 years');
SELECT add_retention_policy('three_phase_meters', INTERVAL '2 years');
SELECT add_retention_policy('predictions', INTERVAL '1 year');
SELECT add_retention_policy('alerts', INTERVAL '1 year');
SELECT add_retention_policy('audit_log', INTERVAL '5 years');

-- ============================================================
-- CONTINUOUS AGGREGATES
-- ============================================================

CREATE MATERIALIZED VIEW solar_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    station_id,
    AVG(power_kw) AS avg_power,
    MAX(power_kw) AS max_power,
    AVG(pyrano1) AS avg_irradiance,
    COUNT(*) AS samples
FROM solar_measurements
GROUP BY bucket, station_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('solar_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

---

## API Specifications

### Authentication (Keycloak)

```bash
# Get access token
curl -X POST https://auth.pea-forecast.go.th/realms/pea-forecast/protocol/openid-connect/token \
  -d "client_id=pea-forecast-api" \
  -d "client_secret=<secret>" \
  -d "grant_type=client_credentials"

# Use token in requests
Authorization: Bearer <access_token>
```

### Core Endpoints

#### POST /api/v1/forecast/solar

```json
// Request
{
  "timestamp": "2024-01-15T10:00:00+07:00",
  "horizon_minutes": 60,
  "features": {
    "pyrano1": 850.5,
    "pyrano2": 842.3,
    "pvtemp1": 45.2,
    "pvtemp2": 44.8,
    "ambtemp": 32.5,
    "windspeed": 2.3
  }
}

// Response
{
  "status": "success",
  "data": {
    "timestamp": "2024-01-15T10:00:00+07:00",
    "prediction": {
      "power_kw": 3542.5,
      "confidence_interval": {
        "lower": 3380.2,
        "upper": 3704.8
      }
    },
    "model_version": "solar-xgb-v1.0.0"
  }
}
```

#### POST /api/v1/forecast/voltage

```json
// Request
{
  "timestamp": "2024-01-15T10:00:00+07:00",
  "prosumer_ids": ["prosumer1", "prosumer2"]
}

// Response
{
  "status": "success",
  "data": {
    "predictions": [
      {
        "prosumer_id": "prosumer1",
        "phase": "A",
        "predicted_voltage": 232.5,
        "status": "normal"
      }
    ]
  }
}
```

---

## ML Model Guidelines

### Feature Engineering

```python
# ml/src/features/solar_features.py

class SolarFeatureEngineer:
    """Feature engineering for RE Forecast (solar power prediction)."""
    
    REQUIRED_COLUMNS = [
        'timestamp', 'pyrano1', 'pyrano2',
        'pvtemp1', 'pvtemp2', 'ambtemp', 'windspeed'
    ]
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Temporal features
        df['hour'] = df['timestamp'].dt.hour
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['is_peak_hour'] = df['hour'].between(10, 14).astype(int)
        
        # Derived features
        df['pyrano_avg'] = (df['pyrano1'] + df['pyrano2']) / 2
        df['pvtemp_avg'] = (df['pvtemp1'] + df['pvtemp2']) / 2
        df['temp_delta'] = df['pvtemp_avg'] - df['ambtemp']
        
        # Lag features
        for lag in [1, 2, 3]:
            df[f'pyrano1_lag_{lag}'] = df['pyrano1'].shift(lag)
        
        # Rolling statistics
        df['pyrano1_rolling_mean_12'] = df['pyrano1'].rolling(12).mean()
        
        return df
    
    def get_feature_columns(self) -> list:
        return [
            'pyrano1', 'pyrano2', 'pyrano_avg',
            'pvtemp1', 'pvtemp2', 'pvtemp_avg', 'ambtemp', 'temp_delta',
            'windspeed',
            'hour_sin', 'hour_cos', 'is_peak_hour',
            'pyrano1_lag_1', 'pyrano1_lag_2', 'pyrano1_lag_3',
            'pyrano1_rolling_mean_12'
        ]
```

### Model Accuracy Requirements

| Model | Metric | Target | Validation |
|-------|--------|--------|------------|
| **RE Forecast (Solar)** | MAPE | < 10% | Time-series CV |
| | RMSE | < 100 kW | |
| | R² | > 0.95 | |
| **Voltage Prediction** | MAE | < 2V | Time-series CV |
| | RMSE | < 3V | |
| | R² | > 0.90 | |

---

## Network Topology

### Distribution Network Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              LOW VOLTAGE DISTRIBUTION NETWORK (POC)                         │
│              ระบบไฟฟ้าแรงต่ำสำหรับการทดสอบสาธิต                              │
└─────────────────────────────────────────────────────────────────────────────┘

      ┌────────────────────────┐
      │  Distribution          │
      │  Transformer           │
      │  (หม้อแปลงไฟฟ้า)         │
      │                        │
      │    22 kV / 0.4 kV      │
      │       50 kVA           │
      └───────────┬────────────┘
                  │
                  ▼
      ┌────────────────────────┐
      │   Community Battery    │
      │   (แบตเตอรี่ชุมชน)       │
      └───────────┬────────────┘
                  │
    ══════════════╪══════════════════════════════════════════════════════
                  │
    ┌─────────────┴─────────────────────────────────────────────────────┐
    │                                                                   │
    │  PHASE A ═══════════╤════════════════╤═══════════════════════╗   │
    │                     │                │                       ║   │
    │               ┌─────┴─────┐    ┌─────┴─────┐          ┌─────┴─────┐
    │               │ Prosumer3 │    │ Prosumer2 │          │ Prosumer1 │
    │               │   [PV]    │    │   [PV]    │          │ [PV][EV]  │
    │               │ Pos: 1    │    │ Pos: 2    │          │ Pos: 3    │
    │               └───────────┘    └───────────┘          └───────────┘
    │                                                                   │
    │  PHASE B ═══════════╤════════════════╤═══════════════════════╗   │
    │                     │                │                       ║   │
    │               ┌─────┴─────┐    ┌─────┴─────┐          ┌─────┴─────┐
    │               │ Prosumer6 │    │ Prosumer4 │          │ Prosumer5 │
    │               │   [PV]    │    │   [PV]    │          │ [PV][EV]  │
    │               │ Pos: 1    │    │ Pos: 2    │          │ Pos: 3    │
    │               └───────────┘    └───────────┘          └───────────┘
    │                                                                   │
    │  PHASE C ═══════════╤════════════════════════════════════════════╝
    │                     │                                             │
    │               ┌─────┴─────┐                                       │
    │               │ Prosumer7 │                                       │
    │               │ [PV][EV]  │                                       │
    │               │ Pos: 1    │                                       │
    │               └───────────┘                                       │
    │                                                                   │
    └───────────────────────────────────────────────────────────────────┘

    LEGEND:
    ═══════  Phase conductor
    [PV]     Solar PV installation (แผงโซลาร์)
    [EV]     Electric Vehicle charger (ที่ชาร์จรถไฟฟ้า)
    Pos: n   Position in phase (1=near, 3=far from transformer)

    VOLTAGE LIMITS (ขีดจำกัดแรงดัน):
    ├── Nominal:     230V (single-phase) / 400V (three-phase)
    ├── Upper Limit: 242V (+5%)
    └── Lower Limit: 218V (-5%)
```

### Prosumer Configuration

| ID | Phase | Position | PV | EV | Description |
|----|-------|----------|----|----|-------------|
| prosumer1 | A | 3 (far) | ✓ | ✓ | End of Phase A feeder |
| prosumer2 | A | 2 (mid) | ✓ | ✗ | Middle of Phase A |
| prosumer3 | A | 1 (near) | ✓ | ✗ | Near transformer |
| prosumer4 | B | 2 (mid) | ✓ | ✗ | Middle of Phase B |
| prosumer5 | B | 3 (far) | ✓ | ✓ | End of Phase B feeder |
| prosumer6 | B | 1 (near) | ✓ | ✗ | Near transformer |
| prosumer7 | C | 1 (near) | ✓ | ✓ | Phase C prosumer |

---

## Data Dictionary

### Solar Measurements (RE Forecast)

| Column | Unit | Description | Range |
|--------|------|-------------|-------|
| `pvtemp1` | °C | PV panel temperature 1 | -10 to 100 |
| `pvtemp2` | °C | PV panel temperature 2 | -10 to 100 |
| `ambtemp` | °C | Ambient temperature | -10 to 60 |
| `pyrano1` | W/m² | Irradiance sensor 1 | 0 to 1500 |
| `pyrano2` | W/m² | Irradiance sensor 2 | 0 to 1500 |
| `windspeed` | m/s | Wind speed | 0 to 50 |
| `power_kw` | kW | Power output (target) | 0 to 5000 |

### Single-Phase Meters (Voltage Prediction)

| Column | Unit | Description |
|--------|------|-------------|
| `active_power` | kW | Active power |
| `reactive_power` | kVAR | Reactive power |
| `energy_meter_voltage` | V | Voltage (target) |
| `energy_meter_current` | A | Current |

---

## Coding Standards

### Python

```python
# Use type hints, Pydantic models, async/await
from pydantic import BaseModel, Field

class SolarPredictionRequest(BaseModel):
    timestamp: datetime
    pyrano1: float = Field(..., ge=0, le=1500)
    pyrano2: float = Field(..., ge=0, le=1500)
    pvtemp1: float = Field(..., ge=-10, le=100)
    pvtemp2: float = Field(..., ge=-10, le=100)
    ambtemp: float = Field(..., ge=-10, le=60)
    windspeed: float = Field(..., ge=0, le=50)

async def predict_solar(request: SolarPredictionRequest) -> SolarPredictionResponse:
    """Generate solar power prediction."""
    pass
```

### TypeScript

```typescript
interface SolarForecast {
  timestamp: string;
  predicted_power: number;
  confidence_lower: number;
  confidence_upper: number;
}

const SolarChart: React.FC<{ data: SolarForecast[] }> = ({ data }) => {
  // Implementation
};
```

---

## Environment Configuration

```bash
# .env.example

# Application
APP_ENV=development
APP_SECRET_KEY=change-me-in-production

# Database (TimescaleDB)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pea_forecast
DB_USER=postgres
DB_PASSWORD=postgres

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=pea-forecast
KEYCLOAK_CLIENT_ID=pea-forecast-api

# ML
MODEL_REGISTRY_PATH=/app/models
MLFLOW_TRACKING_URI=http://localhost:5000
```

---

## Development Commands

```bash
# Setup
git clone https://gitlab.pea.co.th/re-forecast/pea-re-forecast.git
cd pea-re-forecast
docker-compose -f docker/docker-compose.yml up -d

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install && npm run dev

# ML Training
cd ml
python scripts/train_solar.py --config configs/solar_config.yaml

# Tests
pytest tests/ -v --cov=app

# Deploy
helm upgrade --install pea-re-forecast ./infrastructure/helm/pea-re-forecast
```

---

## Implementation Checklist

### Phase 1: Foundation (Weeks 1-4)
- [ ] Initialize GitLab repository
- [ ] Setup Docker Compose
- [ ] Configure TimescaleDB schema
- [ ] Implement FastAPI skeleton
- [ ] Setup Keycloak authentication
- [ ] Configure GitLab CI/CD + ArgoCD

### Phase 2: ML Development (Weeks 5-8)
- [ ] Load POC data (POC_Data.xlsx)
- [ ] Feature engineering pipeline
- [ ] Train RE Forecast model (MAPE < 10%)
- [ ] Train Voltage model (MAE < 2V)
- [ ] Setup MLflow tracking

### Phase 3: Application (Weeks 9-12)
- [ ] Implement forecast APIs
- [ ] Build React dashboard
- [ ] WebSocket real-time updates
- [ ] Alert management system

### Phase 4: Deployment (Weeks 13-16)
- [ ] Unit tests (80% coverage)
- [ ] Load testing (300,000 users)
- [ ] Security scanning (Trivy, SonarQube)
- [ ] Production deployment
- [ ] Documentation & training

---

## Troubleshooting

### Common Issues

```bash
# TimescaleDB connection
docker-compose ps timescaledb
psql -h localhost -U postgres -d pea_forecast

# Model latency > 500ms
# Check Redis cache
redis-cli PING

# Keycloak auth
curl http://localhost:8080/health

# Kafka consumer lag
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group pea-forecast --describe
```

---

## References

- **TOR Document**: Terms of Reference (TOR) แพลตฟอร์มสำหรับศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียนของ กฟภ.
- **POC Data**: POC_Data.xlsx (Solar, 1 Phase, 3 Phase sheets)
- **Network Diagram**: Appendix 6 - Distribution Network Topology

---

*Document Version: 2.0.0*  
*TOR Compliant: Section 7.1.1 - 7.1.7*  
*Last Updated: December 2024*