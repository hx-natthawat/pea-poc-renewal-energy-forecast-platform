import { Gauge, Network, Zap } from "lucide-react";
import type { HelpContentRegistry, HelpSection } from "../types";

const voltageMonitor: HelpSection = {
  id: "voltage-monitor",
  title: "Voltage Monitor",
  titleTh: "ตรวจสอบแรงดัน",
  icon: Zap,
  description:
    "Real-time voltage monitoring across the low-voltage distribution network. Predicts voltage levels with MAE < 2V accuracy as required by TOR.",
  descriptionTh:
    "ตรวจสอบแรงดันแบบ real-time ทั่วระบบจำหน่ายไฟฟ้าแรงต่ำ พยากรณ์ระดับแรงดันด้วยความแม่นยำ MAE < 2V ตามที่ TOR กำหนด",
  features: [
    {
      title: "Voltage Bands",
      titleTh: "แถบแรงดัน",
      description: "Green zone (218-242V), Yellow warning zones, Red violation zones",
      descriptionTh: "โซนเขียว (218-242V), โซนเตือนสีเหลือง, โซนเกินขีดจำกัดสีแดง",
    },
    {
      title: "Phase Selection",
      titleTh: "เลือกเฟส",
      description: "Filter by Phase A, B, or C to focus on specific feeders",
      descriptionTh: "กรองตามเฟส A, B หรือ C เพื่อโฟกัสที่สายป้อนเฉพาะ",
    },
    {
      title: "Prosumer Details",
      titleTh: "รายละเอียด Prosumer",
      description: "Click on any point to see individual prosumer voltage",
      descriptionTh: "คลิกที่จุดใดก็ได้เพื่อดูแรงดันของ prosumer แต่ละราย",
    },
    {
      title: "Prediction Overlay",
      titleTh: "แสดงการพยากรณ์ซ้อน",
      description: "Toggle to show predicted vs actual voltage values",
      descriptionTh: "สลับเพื่อแสดงค่าแรงดันที่พยากรณ์ vs ค่าจริง",
    },
  ],
  relatedSections: ["network-topology", "alert-dashboard"],
  docsUrl: "/docs/voltage-prediction",
  tips: [
    {
      text: "Voltage violations often occur at the end of long feeders (position 3)",
      textTh: "การละเมิดแรงดันมักเกิดขึ้นที่ปลายสายป้อนยาว (ตำแหน่งที่ 3)",
    },
    {
      text: "High PV injection during midday can cause overvoltage",
      textTh: "การจ่ายไฟฟ้าจาก PV สูงในช่วงเที่ยงอาจทำให้แรงดันเกิน",
    },
  ],
};

const networkTopology: HelpSection = {
  id: "network-topology",
  title: "Network Topology",
  titleTh: "โทโพโลยีเครือข่าย",
  icon: Network,
  description:
    "Interactive visualization of the low-voltage distribution network showing transformer, prosumers, and their connections across three phases.",
  descriptionTh:
    "การแสดงผลแบบโต้ตอบของระบบจำหน่ายไฟฟ้าแรงต่ำ แสดงหม้อแปลง prosumer และการเชื่อมต่อของพวกเขาในสามเฟส",
  features: [
    {
      title: "Network Graph",
      titleTh: "กราฟเครือข่าย",
      description: "Visual representation of transformer and prosumer connections",
      descriptionTh: "การแสดงภาพของการเชื่อมต่อหม้อแปลงและ prosumer",
    },
    {
      title: "Voltage Overlay",
      titleTh: "แสดงแรงดันซ้อน",
      description: "Node colors indicate current voltage status (green/yellow/red)",
      descriptionTh: "สีของโหนดบ่งบอกสถานะแรงดันปัจจุบัน (เขียว/เหลือง/แดง)",
    },
    {
      title: "Prosumer Details",
      titleTh: "รายละเอียด Prosumer",
      description: "Click on any node to see prosumer details and equipment",
      descriptionTh: "คลิกที่โหนดใดก็ได้เพื่อดูรายละเอียด prosumer และอุปกรณ์",
    },
    {
      title: "Phase Filtering",
      titleTh: "กรองเฟส",
      description: "Show/hide specific phases to focus analysis",
      descriptionTh: "แสดง/ซ่อนเฟสเฉพาะเพื่อโฟกัสการวิเคราะห์",
    },
  ],
  relatedSections: ["voltage-monitor"],
  tips: [
    {
      text: "Drag nodes to rearrange the network layout",
      textTh: "ลากโหนดเพื่อจัดเรียงเลย์เอาต์เครือข่ายใหม่",
    },
    {
      text: "Icons show equipment: solar panel, EV charger, battery",
      textTh: "ไอคอนแสดงอุปกรณ์: แผงโซลาร์, ที่ชาร์จ EV, แบตเตอรี่",
    },
  ],
};

const voltageStatus: HelpSection = {
  id: "voltage-status",
  title: "Voltage Status",
  titleTh: "สถานะแรงดัน",
  icon: Gauge,
  description:
    "Summary of voltage health across all monitored prosumers. Shows compliance with ±5% voltage regulation standards.",
  descriptionTh: "สรุปสถานะแรงดันของ prosumer ที่ตรวจสอบทั้งหมด แสดงการปฏิบัติตามมาตรฐานการควบคุมแรงดัน ±5%",
  features: [
    {
      title: "Compliance Rate",
      titleTh: "อัตราการปฏิบัติตาม",
      description: "Percentage of prosumers within normal voltage range",
      descriptionTh: "เปอร์เซ็นต์ของ prosumer ที่อยู่ในช่วงแรงดันปกติ",
    },
    {
      title: "Violation Count",
      titleTh: "จำนวนการละเมิด",
      description: "Number of active over/under voltage conditions",
      descriptionTh: "จำนวนสภาวะแรงดันเกิน/ต่ำที่ยังคงอยู่",
    },
  ],
  relatedSections: ["voltage-monitor", "alert-dashboard"],
};

export const voltageHelp: HelpContentRegistry = {
  "voltage-monitor": voltageMonitor,
  "network-topology": networkTopology,
  "voltage-status": voltageStatus,
};
