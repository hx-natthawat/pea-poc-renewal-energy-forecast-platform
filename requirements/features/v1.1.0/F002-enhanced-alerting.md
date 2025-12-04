# F002: Enhanced Alerting System

## Feature Overview

| Attribute | Value |
|-----------|-------|
| Feature ID | F002 |
| Version | v1.1.0 |
| Status | 📋 Planned |
| Priority | P1 - Important |

## Description

Multi-channel notification system with email (SMTP) and LINE Notify integration for alert delivery. Includes alert escalation rules, acknowledgment workflow, and bilingual templates (Thai/English).

**Reference**: v1.1.0 Roadmap - Enhanced Alerting System

## Requirements

### Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| F002-R01 | Email notifications via SMTP | 📋 Planned |
| F002-R02 | LINE Notify integration | 📋 Planned |
| F002-R03 | Alert escalation rules | 📋 Planned |
| F002-R04 | Alert acknowledgment workflow | 📋 Planned |
| F002-R05 | Bilingual templates (Thai/English) | 📋 Planned |
| F002-R06 | Scheduled report emails (daily/weekly) | 📋 Planned |
| F002-R07 | User notification preferences | 📋 Planned |
| F002-R08 | Alert grouping and deduplication | 📋 Planned |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| F002-NF01 | Email delivery time | < 30 seconds |
| F002-NF02 | LINE notification time | < 10 seconds |
| F002-NF03 | Retry on failure | 3 attempts |

## Alert Channels

| Channel | Provider | Use Case |
|---------|----------|----------|
| Email | SMTP (Gmail/PEA SMTP) | Detailed reports, escalations |
| LINE Notify | LINE API | Instant mobile alerts |
| Dashboard | WebSocket | Real-time in-app notifications |
| Webhook | HTTP POST | Integration with external systems |

## API Specification

### POST /api/v1/alerts/notify

**Request:**
```json
{
  "alert_id": "alert-001",
  "channels": ["email", "line"],
  "recipients": ["user@pea.co.th"],
  "template": "voltage_violation",
  "language": "th",
  "data": {
    "prosumer_id": "prosumer1",
    "voltage": 245.5,
    "threshold": 242.0
  }
}
```

### GET /api/v1/alerts/preferences/{user_id}

Get user notification preferences.

### PUT /api/v1/alerts/preferences/{user_id}

Update notification preferences.

### POST /api/v1/alerts/{alert_id}/acknowledge

Acknowledge an alert.

### GET /api/v1/alerts/escalation-rules

Get configured escalation rules.

## Alert Templates

### Voltage Violation (Thai)

```
🚨 แจ้งเตือน: แรงดันไฟฟ้าเกินขีดจำกัด

สถานที่: {{ prosumer_id }}
แรงดันปัจจุบัน: {{ voltage }} V
ขีดจำกัด: {{ threshold }} V
เวลา: {{ timestamp }}

กรุณาตรวจสอบและดำเนินการแก้ไข
```

### Voltage Violation (English)

```
🚨 Alert: Voltage Limit Exceeded

Location: {{ prosumer_id }}
Current Voltage: {{ voltage }} V
Threshold: {{ threshold }} V
Time: {{ timestamp }}

Please investigate and take corrective action.
```

## Escalation Rules

| Level | Condition | Action |
|-------|-----------|--------|
| L1 | Alert created | Notify assigned operator |
| L2 | Not acknowledged in 15 min | Notify supervisor |
| L3 | Not resolved in 1 hour | Notify manager |
| L4 | Critical + not resolved 2 hours | Notify director |

## Implementation Plan

| Component | File | Priority |
|-----------|------|----------|
| Notification Service | `backend/app/services/notification_service.py` | P1 |
| Email Provider | `backend/app/services/providers/email_provider.py` | P1 |
| LINE Provider | `backend/app/services/providers/line_provider.py` | P1 |
| Alert Templates | `backend/app/templates/alerts/` | P1 |
| Notification API | `backend/app/api/v1/endpoints/notifications.py` | P1 |
| Escalation Engine | `backend/app/services/escalation_service.py` | P2 |
| Scheduled Reports | `backend/app/tasks/scheduled_reports.py` | P2 |

## Dependencies

- Email: SMTP server credentials (PEA or Gmail)
- LINE: LINE Notify API token
- Templates: Jinja2 for rendering
- Scheduler: Celery Beat for scheduled reports

## Acceptance Criteria

- [ ] Email notifications delivered within 30 seconds
- [ ] LINE Notify integration working
- [ ] Alert templates in Thai and English
- [ ] Acknowledgment workflow functional
- [ ] Escalation rules configurable
- [ ] Daily/weekly scheduled reports
- [ ] User preferences saved and applied
- [ ] Unit and integration tests

---

*Feature Version: 1.0*
*Created: December 2024*
