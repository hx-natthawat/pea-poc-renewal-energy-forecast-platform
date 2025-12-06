# F002: Enhanced Alerting System

## Feature Overview

| Attribute | Value |
|-----------|-------|
| Feature ID | F002 |
| Version | v1.1.0 |
| Status | ✅ Core Completed |
| Priority | P1 - Important |

## Description

Multi-channel notification system with email (SMTP) and LINE Notify integration for alert delivery. Includes alert escalation rules, acknowledgment workflow, and bilingual templates (Thai/English).

**Reference**: v1.1.0 Roadmap - Enhanced Alerting System

## Requirements

### Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| F002-R01 | Email notifications via SMTP | ✅ Done |
| F002-R02 | LINE Notify integration | ✅ Done |
| F002-R03 | Alert escalation rules | 📋 Planned |
| F002-R04 | Alert acknowledgment workflow | ✅ Done |
| F002-R05 | Bilingual templates (Thai/English) | ✅ Done |
| F002-R06 | Scheduled report emails (daily/weekly) | 📋 Planned |
| F002-R07 | User notification preferences | ✅ Done |
| F002-R08 | Alert grouping and deduplication | 📋 Planned |

### Non-Functional Requirements

| ID | Requirement | Target | Actual |
|----|-------------|--------|--------|
| F002-NF01 | Email delivery time | < 30 seconds | ✅ Simulated |
| F002-NF02 | LINE notification time | < 10 seconds | ✅ Simulated |
| F002-NF03 | Retry on failure | 3 attempts | ✅ Done |

## Alert Channels

| Channel | Provider | Status |
|---------|----------|--------|
| Email | SMTP (Gmail/PEA SMTP) | ✅ Implemented |
| LINE Notify | LINE API | ✅ Implemented |
| Dashboard | In-memory storage | ✅ Implemented |
| Webhook | HTTP POST | 📋 Planned |

## API Specification

### POST /api/v1/notifications/send

**Request:**
```json
{
  "alert_id": "alert-001",
  "alert_type": "voltage_violation",
  "severity": "warning",
  "recipients": ["user@pea.co.th"],
  "channels": ["email", "line", "dashboard"],
  "template_name": "voltage_violation",
  "language": "th",
  "data": {
    "prosumer_id": "prosumer1",
    "voltage": 245.5,
    "threshold": 242.0,
    "timestamp": "2025-01-15 10:00:00"
  },
  "priority": "high"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "alert_id": "alert-001",
    "channels_sent": ["email", "line", "dashboard"],
    "channels_failed": [],
    "sent_at": "2025-01-15T10:00:00Z"
  }
}
```

### GET /api/v1/notifications/dashboard

Get recent dashboard notifications.

### POST /api/v1/notifications/dashboard/{id}/read

Mark a notification as read.

### GET /api/v1/notifications/preferences

Get user notification preferences.

### PUT /api/v1/notifications/preferences

Update notification preferences.

### POST /api/v1/notifications/test

Send a test notification (admin only).

### GET /api/v1/notifications/channels

Get available channels and their configuration status.

### GET /api/v1/notifications/templates

Get available notification templates.

## Alert Templates

### Available Templates

| Template | Languages | Use Case |
|----------|-----------|----------|
| voltage_violation | EN, TH | Voltage limit exceeded |
| solar_forecast_deviation | EN, TH | Forecast accuracy issues |
| ramp_rate_exceeded | EN, TH | Rapid power changes |
| storm_warning | EN, TH | Weather alerts |
| model_drift_detected | EN, TH | Model performance issues |

### Voltage Violation (Thai)

```
แจ้งเตือนแรงดันไฟฟ้าเกินขีดจำกัด

สถานที่: {{ prosumer_id }}
แรงดันปัจจุบัน: {{ voltage }} V
ขีดจำกัด: {{ threshold }} V
เวลา: {{ timestamp }}

กรุณาตรวจสอบและดำเนินการแก้ไข
```

### Voltage Violation (English)

```
VOLTAGE VIOLATION ALERT

Location: {{ prosumer_id }}
Current Voltage: {{ voltage }} V
Threshold: {{ threshold }} V
Time: {{ timestamp }}

Please investigate and take corrective action.
```

## Escalation Rules (Planned)

| Level | Condition | Action |
|-------|-----------|--------|
| L1 | Alert created | Notify assigned operator |
| L2 | Not acknowledged in 15 min | Notify supervisor |
| L3 | Not resolved in 1 hour | Notify manager |
| L4 | Critical + not resolved 2 hours | Notify director |

## Implementation

| Component | File | Status |
|-----------|------|--------|
| Notification Service | `backend/app/services/notification_service.py` | ✅ |
| Email Provider | `backend/app/services/providers/email_provider.py` | ✅ |
| LINE Provider | `backend/app/services/providers/line_provider.py` | ✅ |
| Providers Init | `backend/app/services/providers/__init__.py` | ✅ |
| Notification API | `backend/app/api/v1/endpoints/notifications.py` | ✅ |
| Unit Tests | `backend/tests/unit/test_notification_service.py` | ✅ |
| Escalation Engine | `backend/app/services/escalation_service.py` | 📋 |
| Scheduled Reports | `backend/app/tasks/scheduled_reports.py` | 📋 |

## Configuration

### Email Provider

```python
EmailConfig(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="",       # Configure for production
    smtp_password="",   # Configure for production
    use_tls=True,
    max_retries=3,
)
```

### LINE Provider

```python
LineConfig(
    access_token="",    # Get from LINE Notify
    timeout_seconds=10,
    max_retries=3,
)
```

## Acceptance Criteria

- [x] Email notifications delivered (simulated mode works)
- [x] LINE Notify integration implemented
- [x] Alert templates in Thai and English (5 templates)
- [x] Dashboard notification storage and retrieval
- [x] Mark notifications as read
- [x] User preferences API endpoints
- [x] Test notification endpoint for verification
- [x] Unit tests pass (32 tests)
- [ ] Escalation rules configurable
- [ ] Scheduled reports

---

*Feature Version: 1.0*
*Created: December 2025*
*Updated: December 2025 - Core implementation completed*
