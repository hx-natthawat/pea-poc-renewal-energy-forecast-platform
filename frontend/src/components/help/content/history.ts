import { Calendar, Download, History } from "lucide-react";
import type { HelpContentRegistry, HelpSection } from "../types";

const historicalAnalysis: HelpSection = {
  id: "historical-analysis",
  title: "Historical Analysis",
  titleTh: "การวิเคราะห์ข้อมูลย้อนหลัง",
  icon: History,
  description:
    "Explore historical solar generation and voltage data. Analyze patterns, trends, and model accuracy over past periods.",
  descriptionTh:
    "สำรวจข้อมูลการผลิตไฟฟ้าแสงอาทิตย์และแรงดันย้อนหลัง วิเคราะห์รูปแบบ แนวโน้ม และความแม่นยำของโมเดลในช่วงที่ผ่านมา",
  features: [
    {
      title: "Date Range Selection",
      titleTh: "เลือกช่วงวันที่",
      description: "Select custom date ranges for analysis",
      descriptionTh: "เลือกช่วงวันที่ที่กำหนดเองสำหรับการวิเคราะห์",
    },
    {
      title: "Data Comparison",
      titleTh: "เปรียบเทียบข้อมูล",
      description: "Compare actual vs predicted values over time",
      descriptionTh: "เปรียบเทียบค่าจริง vs ค่าพยากรณ์ตลอดเวลา",
    },
    {
      title: "Pattern Detection",
      titleTh: "ตรวจจับรูปแบบ",
      description: "Identify seasonal patterns, weekly cycles, and anomalies",
      descriptionTh: "ระบุรูปแบบตามฤดูกาล วงจรรายสัปดาห์ และความผิดปกติ",
    },
    {
      title: "Statistics Summary",
      titleTh: "สรุปสถิติ",
      description: "View min, max, average, and standard deviation",
      descriptionTh: "ดูค่าต่ำสุด สูงสุด เฉลี่ย และส่วนเบี่ยงเบนมาตรฐาน",
    },
  ],
  relatedSections: ["solar-forecast", "voltage-monitor", "day-ahead-report"],
  docsUrl: "/docs/historical-analysis",
  tips: [
    {
      text: "Use the zoom controls to focus on specific time periods",
      textTh: "ใช้ตัวควบคุมการซูมเพื่อโฟกัสที่ช่วงเวลาเฉพาะ",
    },
    {
      text: "Export data for offline analysis using the download button",
      textTh: "ส่งออกข้อมูลสำหรับการวิเคราะห์ออฟไลน์โดยใช้ปุ่มดาวน์โหลด",
    },
  ],
};

const dayAheadReport: HelpSection = {
  id: "day-ahead-report",
  title: "Day-Ahead Report",
  titleTh: "รายงานล่วงหน้า 1 วัน",
  icon: Calendar,
  description:
    "Comprehensive forecast report for the next day. Includes solar generation forecast, expected peak times, and potential voltage issues.",
  descriptionTh:
    "รายงานพยากรณ์ที่ครอบคลุมสำหรับวันถัดไป รวมถึงการพยากรณ์การผลิตไฟฟ้าแสงอาทิตย์ ช่วงเวลาพีคที่คาดว่าจะเกิดขึ้น และปัญหาแรงดันที่อาจเกิดขึ้น",
  features: [
    {
      title: "Generation Forecast",
      titleTh: "พยากรณ์การผลิต",
      description: "Hour-by-hour solar generation prediction",
      descriptionTh: "การพยากรณ์การผลิตไฟฟ้าแสงอาทิตย์รายชั่วโมง",
    },
    {
      title: "Peak Summary",
      titleTh: "สรุปพีค",
      description: "Expected peak generation time and value",
      descriptionTh: "เวลาและค่าการผลิตสูงสุดที่คาดว่าจะเกิดขึ้น",
    },
    {
      title: "Risk Indicators",
      titleTh: "ตัวบ่งชี้ความเสี่ยง",
      description: "Potential voltage issues or forecast uncertainty",
      descriptionTh: "ปัญหาแรงดันที่อาจเกิดขึ้นหรือความไม่แน่นอนของการพยากรณ์",
    },
    {
      title: "Weather Outlook",
      titleTh: "พยากรณ์อากาศ",
      description: "Weather conditions affecting the forecast",
      descriptionTh: "สภาพอากาศที่ส่งผลต่อการพยากรณ์",
    },
  ],
  relatedSections: ["solar-forecast", "historical-analysis"],
  tips: [
    {
      text: "Reports are generated at 18:00 for the next day",
      textTh: "รายงานถูกสร้างขึ้นเวลา 18:00 สำหรับวันถัดไป",
    },
    {
      text: "Download as PDF for distribution to stakeholders",
      textTh: "ดาวน์โหลดเป็น PDF เพื่อเผยแพร่ให้ผู้มีส่วนได้ส่วนเสีย",
    },
  ],
};

const dataExport: HelpSection = {
  id: "data-export",
  title: "Data Export",
  titleTh: "ส่งออกข้อมูล",
  icon: Download,
  description:
    "Export historical data and reports in various formats (CSV, Excel, PDF) for offline analysis and reporting.",
  descriptionTh:
    "ส่งออกข้อมูลย้อนหลังและรายงานในรูปแบบต่างๆ (CSV, Excel, PDF) สำหรับการวิเคราะห์ออฟไลน์และการรายงาน",
  features: [
    {
      title: "Format Selection",
      titleTh: "เลือกรูปแบบ",
      description: "Choose CSV, Excel, or PDF format",
      descriptionTh: "เลือกรูปแบบ CSV, Excel หรือ PDF",
    },
    {
      title: "Date Range",
      titleTh: "ช่วงวันที่",
      description: "Select specific date range for export",
      descriptionTh: "เลือกช่วงวันที่เฉพาะสำหรับการส่งออก",
    },
    {
      title: "Data Selection",
      titleTh: "เลือกข้อมูล",
      description: "Choose which data fields to include",
      descriptionTh: "เลือกฟิลด์ข้อมูลที่จะรวม",
    },
  ],
  relatedSections: ["historical-analysis", "day-ahead-report"],
};

export const historyHelp: HelpContentRegistry = {
  "historical-analysis": historicalAnalysis,
  "day-ahead-report": dayAheadReport,
  "data-export": dataExport,
};
