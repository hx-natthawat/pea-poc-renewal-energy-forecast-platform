import { Activity, Bell, LayoutDashboard, Sun, Zap } from "lucide-react";
import type { HelpContentRegistry, HelpSection } from "../types";

const overviewSummary: HelpSection = {
  id: "overview-summary",
  title: "Dashboard Overview",
  titleTh: "ภาพรวมแดชบอร์ด",
  icon: LayoutDashboard,
  description:
    "The main dashboard provides a real-time overview of the renewable energy forecast platform. Monitor solar output, voltage levels, and system alerts at a glance.",
  descriptionTh:
    "แดชบอร์ดหลักแสดงภาพรวมแบบ real-time ของแพลตฟอร์มพยากรณ์พลังงานหมุนเวียน ติดตามกำลังผลิตไฟฟ้าแสงอาทิตย์ ระดับแรงดัน และการแจ้งเตือนของระบบได้ในมุมมองเดียว",
  features: [
    {
      title: "Real-time Metrics",
      titleTh: "ตัวชี้วัดแบบ Real-time",
      description: "Key performance indicators update every 5 minutes",
      descriptionTh: "ตัวชี้วัดหลักอัปเดตทุก 5 นาที",
    },
    {
      title: "Quick Navigation",
      titleTh: "นำทางอย่างรวดเร็ว",
      description: "Use tabs to switch between Solar, Voltage, Grid, and more",
      descriptionTh: "ใช้แท็บเพื่อสลับระหว่าง Solar, Voltage, Grid และอื่นๆ",
    },
    {
      title: "System Health",
      titleTh: "สถานะระบบ",
      description: "Green indicator shows all systems operational",
      descriptionTh: "ไฟเขียวแสดงว่าระบบทั้งหมดทำงานปกติ",
    },
  ],
  relatedSections: ["solar-forecast", "voltage-monitor", "alert-dashboard"],
  tips: [
    {
      text: "Click on any card to see detailed information",
      textTh: "คลิกที่การ์ดใดก็ได้เพื่อดูรายละเอียด",
    },
    {
      text: "The status bar shows real-time connection status",
      textTh: "แถบสถานะแสดงสถานะการเชื่อมต่อแบบ real-time",
    },
  ],
};

const solarOutput: HelpSection = {
  id: "solar-output-card",
  title: "Solar Output",
  titleTh: "กำลังผลิตไฟฟ้าแสงอาทิตย์",
  icon: Sun,
  description:
    "Current solar power generation from all connected PV systems in your region. Shows total output in MW.",
  descriptionTh:
    "กำลังผลิตไฟฟ้าพลังงานแสงอาทิตย์ปัจจุบันจากระบบ PV ที่เชื่อมต่อทั้งหมดในพื้นที่ของคุณ แสดงกำลังผลิตรวมเป็น MW",
  features: [
    {
      title: "Live Data",
      titleTh: "ข้อมูลสด",
      description: "Updated every 5 minutes from smart meters",
      descriptionTh: "อัปเดตทุก 5 นาทีจากมิเตอร์อัจฉริยะ",
    },
    {
      title: "Trend Indicator",
      titleTh: "ตัวบ่งชี้แนวโน้ม",
      description: "Arrow shows if output is increasing or decreasing",
      descriptionTh: "ลูกศรแสดงว่ากำลังผลิตเพิ่มขึ้นหรือลดลง",
    },
  ],
  relatedSections: ["solar-forecast"],
};

const voltageCard: HelpSection = {
  id: "voltage-card",
  title: "Average Voltage",
  titleTh: "แรงดันเฉลี่ย",
  icon: Zap,
  description:
    "Average voltage level across all monitored prosumer connections. Normal range: 218V - 242V (±5% of 230V nominal).",
  descriptionTh:
    "ระดับแรงดันเฉลี่ยของจุดเชื่อมต่อ prosumer ที่ตรวจสอบทั้งหมด ช่วงปกติ: 218V - 242V (±5% ของแรงดัน 230V)",
  features: [
    {
      title: "Status Color",
      titleTh: "สีสถานะ",
      description: "Green = normal, Yellow = warning, Red = violation",
      descriptionTh: "เขียว = ปกติ, เหลือง = เตือน, แดง = เกินขีดจำกัด",
    },
    {
      title: "Phase Monitoring",
      titleTh: "ตรวจสอบเฟส",
      description: "Monitors all 3 phases (A, B, C) of the distribution network",
      descriptionTh: "ตรวจสอบทั้ง 3 เฟส (A, B, C) ของระบบจำหน่ายไฟฟ้า",
    },
  ],
  relatedSections: ["voltage-monitor", "network-topology"],
};

const alertsCard: HelpSection = {
  id: "alerts-card",
  title: "Active Alerts",
  titleTh: "การแจ้งเตือนที่ใช้งานอยู่",
  icon: Bell,
  description:
    "Number of unacknowledged alerts requiring attention. Click to view alert details and take action.",
  descriptionTh: "จำนวนการแจ้งเตือนที่ยังไม่ได้รับทราบและต้องดำเนินการ คลิกเพื่อดูรายละเอียดการแจ้งเตือนและดำเนินการ",
  features: [
    {
      title: "Priority Levels",
      titleTh: "ระดับความสำคัญ",
      description: "Critical (red), Warning (yellow), Info (blue)",
      descriptionTh: "วิกฤต (แดง), เตือน (เหลือง), ข้อมูล (น้ำเงิน)",
    },
    {
      title: "Quick Actions",
      titleTh: "ดำเนินการด่วน",
      description: "Acknowledge or dismiss alerts directly from the card",
      descriptionTh: "รับทราบหรือปิดการแจ้งเตือนโดยตรงจากการ์ด",
    },
  ],
  relatedSections: ["alert-dashboard"],
};

const systemStatus: HelpSection = {
  id: "system-status-card",
  title: "System Status",
  titleTh: "สถานะระบบ",
  icon: Activity,
  description:
    "Overall health of the forecast platform including API, database, and ML model services.",
  descriptionTh: "สถานะโดยรวมของแพลตฟอร์มพยากรณ์ รวมถึง API, ฐานข้อมูล และบริการโมเดล ML",
  features: [
    {
      title: "Component Status",
      titleTh: "สถานะส่วนประกอบ",
      description: "Shows status of Backend, ML Service, Database, and Cache",
      descriptionTh: "แสดงสถานะของ Backend, ML Service, Database และ Cache",
    },
    {
      title: "Uptime",
      titleTh: "เวลาทำงาน",
      description: "System uptime percentage over the last 30 days",
      descriptionTh: "เปอร์เซ็นต์เวลาทำงานของระบบในช่วง 30 วันที่ผ่านมา",
    },
  ],
  relatedSections: ["model-performance"],
};

export const overviewHelp: HelpContentRegistry = {
  "overview-summary": overviewSummary,
  "solar-output-card": solarOutput,
  "voltage-card": voltageCard,
  "alerts-card": alertsCard,
  "system-status-card": systemStatus,
};
