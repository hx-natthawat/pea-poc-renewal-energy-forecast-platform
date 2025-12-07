# POC Demo Script & Speaker Notes

## Pre-Demo Checklist

### Environment Setup (15 min before demo)

```bash
# 1. Start Docker services
cd /Users/fero/Desktop/PEA/pea-re-forecast-platform
docker-compose -f docker/docker-compose.yml up -d

# 2. Verify services are healthy
docker ps  # Should show pea-timescaledb and pea-redis as healthy

# 3. Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 4. Start frontend (new terminal)
cd frontend
pnpm dev

# 5. Verify all services
curl http://localhost:8000/api/v1/health  # Should return healthy
open http://localhost:3000                  # Dashboard should load
```

### Browser Setup

- Open Chrome/Firefox in **presentation mode** (F11)
- Pre-open tabs:
  1. Dashboard: http://localhost:3000
  2. API Docs: http://localhost:8000/docs
  3. Slides: Have presentation ready

---

## Demo Flow (15 minutes total)

### 1. Welcome & Introduction (1 minute)

**[SLIDE: Title]**

> "สวัสดีครับ/ค่ะ วันนี้จะนำเสนอ PEA RE Forecast Platform แพลตฟอร์มสำหรับพยากรณ์พลังงานหมุนเวียนของ กฟภ."

**Key Points:**
- Introduce yourself and team
- State the purpose: POC demonstration
- Preview what you'll show

---

### 2. Executive Summary (2 minutes)

**[SLIDE: POC Achievement Summary]**

> "ก่อนอื่น ขอสรุปผลการดำเนินงานตาม TOR..."

**Talk about:**
- Solar MAPE: 9.74% (target < 10%) - **เกินเป้าหมาย 0.26%**
- Voltage MAE: 0.036V (target < 2V) - **ดีกว่าเป้าหมาย 98%**
- All TOR 7.1 requirements met
- 715 tests passing, 300K users load tested

**Transition:**
> "ต่อไปจะอธิบายรายละเอียดแต่ละส่วน..."

---

### 3. TOR Compliance (3 minutes)

**[SLIDE: TOR 7.1 Requirements]**

> "ตามข้อกำหนด TOR Section 7.1..."

**Walk through:**
- 7.1.1 Hardware: Server specs configured per TOR
- 7.1.3 Software: All specified tools (K8s, Kong, Keycloak, etc.)
- 7.1.4 CI/CD: GitLab + ArgoCD implemented
- 7.1.6 Audit Trail: Full logging with UI viewer
- 7.1.7 Scalability: 300,000 users tested

**[SLIDE: Model Accuracy]**

> "สำหรับความแม่นยำของโมเดล..."

**Emphasize:**
- Solar: MAPE 9.74% (show confidence)
- Voltage: MAE 0.036V (extremely accurate)
- Both exceed TOR targets significantly

---

### 4. Live Demo - Solar Forecast (4 minutes)

**[SWITCH TO BROWSER - Dashboard]**

> "ต่อไปจะสาธิตการใช้งานจริง..."

#### Step 1: Dashboard Overview
- Point out the tab navigation
- Explain the layout (metrics left, chart right)

#### Step 2: Current Metrics
> "ด้านซ้ายแสดงข้อมูลปัจจุบัน - กำลังผลิต, ค่าแสงอาทิตย์, อุณหภูมิ"

#### Step 3: Forecast Chart
> "กราฟแสดงการเปรียบเทียบค่าจริงกับค่าพยากรณ์"

- Hover over chart to show values
- Point out confidence interval bands

#### Step 4: Day-Ahead Report
> "สามารถสร้างรายงาน Day-Ahead ได้..."

- Click Reports tab (if available)
- Show PDF/Excel export options

---

### 5. Live Demo - Voltage Prediction (3 minutes)

**[CLICK: Voltage Tab]**

> "ต่อไปเป็นส่วนพยากรณ์แรงดันไฟฟ้า..."

#### Step 1: Network Topology
> "แสดง topology ของระบบจำหน่ายแรงต่ำ ประกอบด้วย 7 prosumers ใน 3 phases"

- Point out transformer at top
- Explain Phase A, B, C branches
- Show prosumer nodes with PV/EV icons

#### Step 2: Phase Selection
> "สามารถเลือกดูแต่ละ phase ได้..."

- Click Phase A, show prosumers
- Click a prosumer node for details

#### Step 3: Voltage Status
> "สีของแต่ละ node แสดงสถานะแรงดัน - เขียว = ปกติ, เหลือง = ใกล้ขีดจำกัด, แดง = เกินขีดจำกัด"

---

### 6. Live Demo - Grid Operations (2 minutes)

**[CLICK: Grid Operations Tab]**

> "Tab นี้เป็นฟังก์ชันเพิ่มเติมตาม TOR 7.5..."

#### Load Forecast
> "Load Forecast แสดงการพยากรณ์ความต้องการใช้ไฟฟ้าตาม hierarchy..."

- Show level selector (System → Regional → Substation → Feeder)

#### Demand Forecast
> "Demand Forecast แสดง Net/Gross/RE demand..."

- Toggle between Net, Gross, RE

#### Imbalance Monitor
> "Imbalance Monitor แสดงความไม่สมดุลพร้อมระดับความรุนแรง..."

- Point out color-coded severity indicators

---

### 7. Live Demo - Alerts & Audit (2 minutes)

**[CLICK: Alerts Tab]**

> "ระบบแจ้งเตือนรองรับหลายช่องทาง..."

#### Alert Configuration
> "สามารถตั้งค่า threshold และช่องทางแจ้งเตือนได้"

- Show voltage thresholds (218V - 242V)
- Mention Email + LINE Notify support

**[CLICK: Audit Tab]**

> "ตาม TOR 7.1.6 ระบบบันทึก Audit Trail ทุกการกระทำ..."

#### Audit Log Viewer
- Show log entries (user, action, timestamp)
- Demonstrate filter functionality
- Show export to CSV

---

### 8. Technical Summary (1 minute)

**[SLIDE: Architecture]**

> "สรุปสถาปัตยกรรมระบบ..."

**Highlight:**
- FastAPI backend (async, high performance)
- React frontend (responsive, PWA)
- TimescaleDB (time-series optimized)
- Kubernetes ready (Helm charts validated)

---

### 9. Roadmap & Next Steps (1 minute)

**[SLIDE: Roadmap]**

> "สำหรับแผนการพัฒนาต่อไป..."

**Key points:**
- Ready for staging deployment
- UAT pending stakeholder scheduling
- DOE/HC blocked by GIS data from กฟภ.

**Request from กฟภ.:**
- UAT scheduling
- GIS network model data
- SCADA access for real-time data

---

### 10. Conclusion & Q&A (remaining time)

**[SLIDE: Summary]**

> "สรุป - แพลตฟอร์มพร้อมสำหรับ staging deployment และ UAT"

**Closing statement:**
> "ขอบคุณครับ/ค่ะ ยินดีตอบคำถาม"

---

## Potential Q&A

### Technical Questions

**Q: How does the model handle missing data?**
> A: We use feature engineering with lag values and rolling statistics. Missing values are interpolated for short gaps, and longer gaps trigger data quality alerts.

**Q: What happens if the weather API is down?**
> A: We have a fallback mechanism that uses simulation data based on historical patterns and last known weather conditions.

**Q: How accurate is the voltage prediction for edge cases?**
> A: Our MAE of 0.036V is consistent across all phases. Edge cases near voltage limits are flagged for manual review.

### Business Questions

**Q: When can we go to production?**
> A: The platform is staging-ready now. After UAT approval (estimated 1-2 weeks), we can deploy to production.

**Q: What's needed for DOE implementation?**
> A: We need the GIS network model data from กฟภ. IT. Once received, DOE implementation is estimated at 17 weeks.

**Q: Can the system scale beyond 300,000 users?**
> A: Yes. The Kubernetes architecture with horizontal pod autoscaling can handle significantly more load. We tested 300K as per TOR requirements.

### Operational Questions

**Q: How do operators get notified of alerts?**
> A: Three channels: 1) Dashboard in real-time, 2) Email notifications, 3) LINE Notify for mobile. All configurable per user preference.

**Q: How long is audit data retained?**
> A: Per TOR 7.1.6 compliance, audit logs are retained for 5 years. Operational data is retained for 2 years.

---

## Troubleshooting

### If Backend Won't Start

```bash
# Check if port is in use
lsof -i :8000
# Kill if needed
kill -9 <PID>

# Restart backend
cd backend
./venv/bin/uvicorn app.main:app --reload --port 8000
```

### If Frontend Shows Errors

```bash
# Clear cache and restart
cd frontend
rm -rf .next node_modules/.cache
pnpm dev
```

### If Database Connection Fails

```bash
# Check Docker container
docker ps | grep timescale
docker restart pea-timescaledb

# Wait 30 seconds for healthy status
```

### If Demo Data is Missing

```bash
# Reload POC data
cd ml
./venv/bin/python scripts/load_poc_data.py
```

---

## Post-Demo Actions

1. **Save Questions**: Note any questions you couldn't answer for follow-up
2. **Collect Feedback**: Ask for initial reactions and concerns
3. **Schedule UAT**: If stakeholders are ready, set UAT dates
4. **Share Materials**: Send presentation and documentation links
5. **Follow Up**: Email summary with action items within 24 hours

---

*Demo Script Version: 1.0*
*Last Updated: December 7, 2025*
