import {
  Activity,
  BarChart3,
  Battery,
  BookOpen,
  FileCheck,
  Gauge,
  GitBranch,
  LineChart,
  Network,
  Server,
  Shield,
  Sun,
  Users,
  Zap,
} from "lucide-react";
import type { HelpContentRegistry, HelpSection } from "../types";

// TOR 7.5.1.2 - RE Forecast
const tor7512: HelpSection = {
  id: "tor-7.5.1.2",
  title: "TOR 7.5.1.2 - RE Forecast",
  titleTh: "TOR 7.5.1.2 - พยากรณ์กำลังผลิต RE",
  icon: Sun,
  description:
    "Requirements for Renewable Energy power output forecasting. Covers Solar PV (7.5.1.2.1), Wind (7.5.1.2.2), and other RE sources. Target accuracy: MAPE < 10%.",
  descriptionTh:
    "ข้อกำหนดสำหรับการพยากรณ์กำลังผลิตไฟฟ้าพลังงานหมุนเวียน ครอบคลุมโซลาร์เซลล์ (7.5.1.2.1), พลังงานลม (7.5.1.2.2) และแหล่งพลังงานหมุนเวียนอื่นๆ เป้าหมายความแม่นยำ: MAPE < 10%",
  features: [
    {
      title: "Solar PV (7.5.1.2.1)",
      titleTh: "โซลาร์เซลล์ (7.5.1.2.1)",
      description: "Primary focus for POC. Uses weather data (GHI, temperature) for prediction",
      descriptionTh: "เป็นจุดเน้นหลักสำหรับ POC ใช้ข้อมูลสภาพอากาศ (GHI, อุณหภูมิ) ในการพยากรณ์",
    },
    {
      title: "Intraday Forecast",
      titleTh: "พยากรณ์ระหว่างวัน",
      description: "15 min - 6 hour horizon (POC Test 1)",
      descriptionTh: "ช่วงเวลา 15 นาที - 6 ชั่วโมง (การทดสอบ POC 1)",
    },
    {
      title: "Day-Ahead Forecast",
      titleTh: "พยากรณ์ล่วงหน้า 1 วัน",
      description: "24-48 hour horizon (POC Test 2)",
      descriptionTh: "ช่วงเวลา 24-48 ชั่วโมง (การทดสอบ POC 2)",
    },
  ],
  relatedSections: ["solar-forecast", "tor-7.3.4.4"],
  docsUrl: "/docs/tor-7.5.1.2",
  tips: [
    {
      text: "Weather parameters from TOR 7.3.4.4 are used as input features",
      textTh: "พารามิเตอร์สภาพอากาศจาก TOR 7.3.4.4 ถูกใช้เป็นคุณสมบัติ input",
    },
  ],
};

// TOR 7.5.1.3 - Load Forecast
const tor7513: HelpSection = {
  id: "tor-7.5.1.3",
  title: "TOR 7.5.1.3 - Load Forecast",
  titleTh: "TOR 7.5.1.3 - พยากรณ์โหลด",
  icon: LineChart,
  description:
    "Multi-level load forecasting requirements. System level (MAPE < 3%), Regional (< 5%), Provincial (< 8%), Substation (< 8%), Feeder (< 12%).",
  descriptionTh:
    "ข้อกำหนดการพยากรณ์โหลดหลายระดับ ระดับระบบ (MAPE < 3%), ระดับภูมิภาค (< 5%), ระดับจังหวัด (< 8%), ระดับสถานีไฟฟ้าย่อย (< 8%), ระดับสายป้อน (< 12%)",
  features: [
    {
      title: "System Level",
      titleTh: "ระดับระบบ",
      description: "Total PEA system load (MAPE < 3%)",
      descriptionTh: "โหลดรวมของระบบ กฟภ. (MAPE < 3%)",
    },
    {
      title: "Regional Level",
      titleTh: "ระดับภูมิภาค",
      description: "12 PEA regions (MAPE < 5%)",
      descriptionTh: "12 ภูมิภาคของ กฟภ. (MAPE < 5%)",
    },
    {
      title: "Substation/Feeder Level",
      titleTh: "ระดับสถานีไฟฟ้า/สายป้อน",
      description: "Detailed grid point forecasts",
      descriptionTh: "พยากรณ์ระดับจุดในระบบโครงข่ายโดยละเอียด",
    },
  ],
  relatedSections: ["tor-7.5.1.2", "tor-7.5.1.4"],
  docsUrl: "/docs/tor-7.5.1.3",
};

// TOR 7.5.1.4 - Imbalance Forecast
const tor7514: HelpSection = {
  id: "tor-7.5.1.4",
  title: "TOR 7.5.1.4 - Imbalance Forecast",
  titleTh: "TOR 7.5.1.4 - พยากรณ์ความไม่สมดุล",
  icon: Gauge,
  description:
    "System imbalance forecasting for grid stability. Formula: Imbalance = Actual Demand - Scheduled Generation - Actual RE Generation. Target: MAE < 5% of average load.",
  descriptionTh:
    "การพยากรณ์ความไม่สมดุลของระบบเพื่อเสถียรภาพของกริด สูตร: ความไม่สมดุล = ความต้องการจริง - กำลังผลิตตามกำหนด - กำลังผลิต RE จริง เป้าหมาย: MAE < 5% ของโหลดเฉลี่ย",
  features: [
    {
      title: "Real-time Calculation",
      titleTh: "คำนวณแบบ Real-time",
      description: "Combines RE, Load, and Generation forecasts",
      descriptionTh: "รวมการพยากรณ์ RE, โหลด และการผลิตไฟฟ้า",
    },
    {
      title: "Reserve Recommendations",
      titleTh: "คำแนะนำสำรอง",
      description: "Suggests spinning/non-spinning reserve requirements",
      descriptionTh: "แนะนำความต้องการสำรองหมุน/ไม่หมุน",
    },
    {
      title: "Grid Stability Alerts",
      titleTh: "การแจ้งเตือนเสถียรภาพกริด",
      description: "Warnings when imbalance exceeds thresholds",
      descriptionTh: "แจ้งเตือนเมื่อความไม่สมดุลเกินเกณฑ์",
    },
  ],
  relatedSections: ["tor-7.5.1.2", "tor-7.5.1.3"],
  docsUrl: "/docs/tor-7.5.1.4",
};

// TOR 7.5.1.5 - Voltage Prediction
const tor7515: HelpSection = {
  id: "tor-7.5.1.5",
  title: "TOR 7.5.1.5 - Voltage Prediction",
  titleTh: "TOR 7.5.1.5 - พยากรณ์แรงดันไฟฟ้า",
  icon: Zap,
  description:
    "Voltage level prediction across LV/MV distribution networks. Monitors prosumer connections, detects overvoltage/undervoltage before occurrence. Target: MAE < 2V for LV, MAE < 1% for MV.",
  descriptionTh:
    "การพยากรณ์ระดับแรงดันไฟฟ้าในระบบจำหน่ายแรงต่ำ/แรงกลาง ตรวจสอบการเชื่อมต่อ prosumer ตรวจจับแรงดันเกิน/ต่ำก่อนเกิดขึ้น เป้าหมาย: MAE < 2V สำหรับ LV, MAE < 1% สำหรับ MV",
  features: [
    {
      title: "LV 1-Phase (230V ± 5%)",
      titleTh: "LV 1 เฟส (230V ± 5%)",
      description: "Primary focus for POC (POC Tests 3, 4)",
      descriptionTh: "จุดเน้นหลักสำหรับ POC (การทดสอบ POC 3, 4)",
    },
    {
      title: "LV 3-Phase (400V ± 5%)",
      titleTh: "LV 3 เฟส (400V ± 5%)",
      description: "Transformer-level monitoring",
      descriptionTh: "การตรวจสอบระดับหม้อแปลง",
    },
    {
      title: "Prosumer Impact Analysis",
      titleTh: "การวิเคราะห์ผลกระทบ Prosumer",
      description: "Tracks voltage impact from solar PV injection",
      descriptionTh: "ติดตามผลกระทบแรงดันจากการฉีดไฟฟ้า Solar PV",
    },
  ],
  relatedSections: ["voltage-prediction", "tor-7.5.1.6"],
  docsUrl: "/docs/tor-7.5.1.5",
  tips: [
    {
      text: "Voltage limits: Normal 218-242V, Warning ±4%, Critical ±5%",
      textTh: "ขีดจำกัดแรงดัน: ปกติ 218-242V, เตือน ±4%, วิกฤต ±5%",
    },
  ],
};

// TOR 7.5.1.6 - DOE
const tor7516: HelpSection = {
  id: "tor-7.5.1.6",
  title: "TOR 7.5.1.6 - Dynamic Operating Envelope",
  titleTh: "TOR 7.5.1.6 - DOE กรอบการทำงานแบบพลวัต",
  icon: Battery,
  description:
    "Dynamic Operating Envelope (DOE) calculates time-varying export/import limits for DER at each connection point. Replaces static limits with real-time constraints based on network conditions.",
  descriptionTh:
    "Dynamic Operating Envelope (DOE) คำนวณขีดจำกัดส่งออก/นำเข้าแบบเปลี่ยนแปลงตามเวลาสำหรับ DER ที่แต่ละจุดเชื่อมต่อ แทนที่ขีดจำกัดคงที่ด้วยข้อจำกัดแบบ real-time ตามสภาพเครือข่าย",
  features: [
    {
      title: "Real-time Limits",
      titleTh: "ขีดจำกัดแบบ Real-time",
      description: "Updates every 15 minutes based on network state",
      descriptionTh: "อัปเดตทุก 15 นาทีตามสถานะเครือข่าย",
    },
    {
      title: "Per-Connection Limits",
      titleTh: "ขีดจำกัดต่อจุดเชื่อมต่อ",
      description: "Individual export/import limits for each prosumer",
      descriptionTh: "ขีดจำกัดส่งออก/นำเข้าแต่ละรายสำหรับแต่ละ prosumer",
    },
    {
      title: "Constraint Identification",
      titleTh: "ระบุข้อจำกัด",
      description: "Identifies limiting factor (voltage, thermal, transformer)",
      descriptionTh: "ระบุปัจจัยจำกัด (แรงดัน, ความร้อน, หม้อแปลง)",
    },
  ],
  relatedSections: ["tor-7.5.1.5", "tor-7.5.1.7"],
  docsUrl: "/docs/tor-7.5.1.6",
};

// TOR 7.5.1.7 - Hosting Capacity
const tor7517: HelpSection = {
  id: "tor-7.5.1.7",
  title: "TOR 7.5.1.7 - Hosting Capacity Forecast",
  titleTh: "TOR 7.5.1.7 - พยากรณ์ Hosting Capacity",
  icon: Network,
  description:
    "Forecasts maximum DER capacity that can connect to each network point. Supports planning decisions for 1, 3, 5, and 10 year horizons. Target accuracy: ± 10%.",
  descriptionTh:
    "พยากรณ์ความจุ DER สูงสุดที่สามารถเชื่อมต่อกับแต่ละจุดในเครือข่าย สนับสนุนการตัดสินใจวางแผนสำหรับช่วง 1, 3, 5 และ 10 ปี เป้าหมายความแม่นยำ: ± 10%",
  features: [
    {
      title: "Current Hosting Capacity",
      titleTh: "Hosting Capacity ปัจจุบัน",
      description: "Remaining capacity at each connection point",
      descriptionTh: "ความจุคงเหลือที่แต่ละจุดเชื่อมต่อ",
    },
    {
      title: "Future Projections",
      titleTh: "การคาดการณ์อนาคต",
      description: "1, 3, 5, 10 year capacity forecasts",
      descriptionTh: "การพยากรณ์ความจุ 1, 3, 5, 10 ปี",
    },
    {
      title: "Upgrade Recommendations",
      titleTh: "คำแนะนำการอัปเกรด",
      description: "Identifies when network upgrades are needed",
      descriptionTh: "ระบุเมื่อต้องการอัปเกรดเครือข่าย",
    },
  ],
  relatedSections: ["tor-7.5.1.5", "tor-7.5.1.6"],
  docsUrl: "/docs/tor-7.5.1.7",
};

// TOR 7.1 - Infrastructure
const tor71: HelpSection = {
  id: "tor-7.1",
  title: "TOR 7.1 - System Installation Requirements",
  titleTh: "TOR 7.1 - ข้อกำหนดการติดตั้งระบบ",
  icon: Server,
  description:
    "Infrastructure specifications including hardware resources (7.1.1), additional resources (7.1.2), software requirements (7.1.3), deployment (7.1.4), licensing (7.1.5), security/audit (7.1.6), and scalability (7.1.7).",
  descriptionTh:
    "ข้อกำหนดโครงสร้างพื้นฐาน รวมถึงทรัพยากรฮาร์ดแวร์ (7.1.1), ทรัพยากรเพิ่มเติม (7.1.2), ข้อกำหนดซอฟต์แวร์ (7.1.3), การติดตั้ง (7.1.4), ลิขสิทธิ์ (7.1.5), ความปลอดภัย/ตรวจสอบ (7.1.6) และความสามารถรองรับ (7.1.7)",
  features: [
    {
      title: "Web Server (7.1.1)",
      titleTh: "เซิร์ฟเวอร์เว็บ (7.1.1)",
      description: "4 Core, 6GB RAM, Ubuntu 22.04 LTS",
      descriptionTh: "4 Core, 6GB RAM, Ubuntu 22.04 LTS",
    },
    {
      title: "AI/ML Server (7.1.1)",
      titleTh: "เซิร์ฟเวอร์ AI/ML (7.1.1)",
      description: "16 Core, 64GB RAM, Ubuntu 22.04 LTS",
      descriptionTh: "16 Core, 64GB RAM, Ubuntu 22.04 LTS",
    },
    {
      title: "Database Server (7.1.1)",
      titleTh: "เซิร์ฟเวอร์ฐานข้อมูล (7.1.1)",
      description: "8 Core, 32GB RAM, Ubuntu 22.04 LTS",
      descriptionTh: "8 Core, 32GB RAM, Ubuntu 22.04 LTS",
    },
  ],
  relatedSections: ["tor-7.1.6", "tor-7.1.7"],
  docsUrl: "/docs/tor-7.1",
};

// TOR 7.1.6 - Security & Audit
const tor716: HelpSection = {
  id: "tor-7.1.6",
  title: "TOR 7.1.6 - Security & Audit Trail",
  titleTh: "TOR 7.1.6 - ความปลอดภัยและ Audit Trail",
  icon: Shield,
  description:
    "Security and audit trail requirements per PEA standards. Includes access logs, attack detection, and comprehensive audit trail for compliance.",
  descriptionTh:
    "ข้อกำหนดความปลอดภัยและ audit trail ตามมาตรฐาน กฟภ. รวมถึง log การเข้าใช้งาน การตรวจจับการโจมตี และ audit trail ที่ครอบคลุมเพื่อการปฏิบัติตามกฎระเบียบ",
  features: [
    {
      title: "Access Logs",
      titleTh: "Log การเข้าใช้งาน",
      description: "All user access is logged with timestamp and IP",
      descriptionTh: "บันทึกการเข้าใช้งานทั้งหมดพร้อมเวลาและ IP",
    },
    {
      title: "Attack Detection",
      titleTh: "ตรวจจับการโจมตี",
      description: "Monitors for suspicious activity and intrusion attempts",
      descriptionTh: "ตรวจสอบกิจกรรมที่น่าสงสัยและความพยายามบุกรุก",
    },
    {
      title: "Audit Trail",
      titleTh: "Audit Trail",
      description: "Complete record of all system changes for compliance",
      descriptionTh: "บันทึกการเปลี่ยนแปลงระบบทั้งหมดสำหรับการปฏิบัติตามกฎระเบียบ",
    },
  ],
  relatedSections: ["audit-logs", "tor-7.1"],
  docsUrl: "/docs/tor-7.1.6",
};

// TOR 7.1.7 - Scalability
const tor717: HelpSection = {
  id: "tor-7.1.7",
  title: "TOR 7.1.7 - Scalability Requirements",
  titleTh: "TOR 7.1.7 - ข้อกำหนดความสามารถรองรับ",
  icon: Users,
  description:
    "Platform must support data import from ≥ 2,000 RE Power Plants and ≥ 300,000 electricity consumers connected to PEA grid.",
  descriptionTh:
    "แพลตฟอร์มต้องรองรับการนำเข้าข้อมูลจากโรงไฟฟ้า RE ไม่น้อยกว่า 2,000 แห่ง และผู้ใช้ไฟฟ้าไม่น้อยกว่า 300,000 ราย ที่เชื่อมต่อกับระบบ กฟภ.",
  features: [
    {
      title: "RE Power Plants",
      titleTh: "โรงไฟฟ้า RE",
      description: "Support ≥ 2,000 connected plants",
      descriptionTh: "รองรับโรงไฟฟ้าที่เชื่อมต่อไม่น้อยกว่า 2,000 แห่ง",
    },
    {
      title: "Electricity Consumers",
      titleTh: "ผู้ใช้ไฟฟ้า",
      description: "Support ≥ 300,000 consumers",
      descriptionTh: "รองรับผู้ใช้ไฟฟ้าไม่น้อยกว่า 300,000 ราย",
    },
    {
      title: "Load Testing",
      titleTh: "การทดสอบโหลด",
      description: "Validated with concurrent user simulations",
      descriptionTh: "ทดสอบด้วยการจำลองผู้ใช้พร้อมกัน",
    },
  ],
  relatedSections: ["tor-7.1"],
  docsUrl: "/docs/tor-7.1.7",
};

// TOR 7.1.4 - Deployment/CI/CD
const tor714: HelpSection = {
  id: "tor-7.1.4",
  title: "TOR 7.1.4 - Deployment Requirements",
  titleTh: "TOR 7.1.4 - ข้อกำหนดการติดตั้ง",
  icon: GitBranch,
  description:
    "Deployment requirements for PEA RE Forecast Platform. Must implement CI/CD (Continuous Integration and Continuous Deployment) and coordinate with PEA system administrators.",
  descriptionTh:
    "ข้อกำหนดการติดตั้งสำหรับแพลตฟอร์มพยากรณ์ RE ของ กฟภ. ต้องดำเนินการ CI/CD (Continuous Integration และ Continuous Deployment) และประสานงานกับผู้ดูแลระบบของ กฟภ.",
  features: [
    {
      title: "CI/CD Pipeline",
      titleTh: "Pipeline CI/CD",
      description: "GitLab CI + ArgoCD for automated deployments",
      descriptionTh: "GitLab CI + ArgoCD สำหรับการติดตั้งอัตโนมัติ",
    },
    {
      title: "PEA Server Infrastructure",
      titleTh: "โครงสร้างเซิร์ฟเวอร์ กฟภ.",
      description: "Deploy on PEA's server resources",
      descriptionTh: "ติดตั้งบนทรัพยากรเซิร์ฟเวอร์ของ กฟภ.",
    },
    {
      title: "Coordination",
      titleTh: "การประสานงาน",
      description: "Work with PEA system administrators",
      descriptionTh: "ทำงานร่วมกับผู้ดูแลระบบของ กฟภ.",
    },
  ],
  relatedSections: ["tor-7.1", "tor-7.1.5"],
  docsUrl: "/docs/tor-7.1.4",
};

// TOR 7.1.5 - Licensing
const tor715: HelpSection = {
  id: "tor-7.1.5",
  title: "TOR 7.1.5 - Software Licensing",
  titleTh: "TOR 7.1.5 - ลิขสิทธิ์ซอฟต์แวร์",
  icon: FileCheck,
  description:
    "All software and databases must be legally licensed. Must be usable continuously throughout the project lifecycle. No additional licensing costs to PEA after deployment.",
  descriptionTh:
    "ซอฟต์แวร์และฐานข้อมูลทั้งหมดต้องมีลิขสิทธิ์ถูกต้องตามกฎหมาย ต้องใช้งานได้ต่อเนื่องตลอดอายุการใช้งาน กฟภ. ต้องไม่มีค่าใช้จ่ายเพิ่มเติมหลังการติดตั้ง",
  features: [
    {
      title: "Legal Compliance",
      titleTh: "การปฏิบัติตามกฎหมาย",
      description: "All software properly licensed",
      descriptionTh: "ซอฟต์แวร์ทั้งหมดมีลิขสิทธิ์ถูกต้อง",
    },
    {
      title: "Continuous Use",
      titleTh: "ใช้งานต่อเนื่อง",
      description: "Licenses valid throughout project lifecycle",
      descriptionTh: "ลิขสิทธิ์ใช้ได้ตลอดอายุโครงการ",
    },
    {
      title: "No Additional Costs",
      titleTh: "ไม่มีค่าใช้จ่ายเพิ่มเติม",
      description: "PEA pays no extra licensing fees",
      descriptionTh: "กฟภ. ไม่ต้องจ่ายค่าลิขสิทธิ์เพิ่มเติม",
    },
  ],
  relatedSections: ["tor-7.1", "tor-7.1.4"],
  docsUrl: "/docs/tor-7.1.5",
};

// TOR 7.3.4.4 - Weather Parameters
const tor7344: HelpSection = {
  id: "tor-7.3.4.4",
  title: "TOR 7.3.4.4 - Weather Parameters",
  titleTh: "TOR 7.3.4.4 - พารามิเตอร์สภาพอากาศ",
  icon: Activity,
  description:
    "Weather data parameters required for forecasting: Temperature, Humidity, Pressure, Wind Speed/Direction, Cloud Index, and Solar Irradiation (GHI).",
  descriptionTh:
    "พารามิเตอร์ข้อมูลสภาพอากาศที่จำเป็นสำหรับการพยากรณ์: อุณหภูมิ, ความชื้น, ความกดอากาศ, ความเร็ว/ทิศทางลม, ดัชนีเมฆ และความเข้มแสงอาทิตย์ (GHI)",
  features: [
    {
      title: "Temperature (7.3.4.4.1)",
      titleTh: "อุณหภูมิ (7.3.4.4.1)",
      description: "Ambient and PV panel temperatures",
      descriptionTh: "อุณหภูมิแวดล้อมและแผง PV",
    },
    {
      title: "Solar Irradiation (7.3.4.4.7)",
      titleTh: "ความเข้มแสงอาทิตย์ (7.3.4.4.7)",
      description: "GHI from pyranometer sensors",
      descriptionTh: "GHI จากเซ็นเซอร์ pyranometer",
    },
    {
      title: "TMD Integration",
      titleTh: "การเชื่อมต่อ TMD",
      description: "Weather data from Thai Meteorological Department",
      descriptionTh: "ข้อมูลสภาพอากาศจากกรมอุตุนิยมวิทยา",
    },
  ],
  relatedSections: ["tor-7.5.1.2", "solar-forecast"],
  docsUrl: "/docs/tor-7.3.4.4",
};

// TOR Overview
const torOverview: HelpSection = {
  id: "tor-overview",
  title: "TOR Overview",
  titleTh: "ภาพรวม TOR",
  icon: BookOpen,
  description:
    "Terms of Reference (TOR) for PEA RE Forecast Platform. Defines 7 core forecasting functions with accuracy requirements, infrastructure specifications, and compliance standards.",
  descriptionTh:
    "ข้อกำหนดอ้างอิง (TOR) สำหรับแพลตฟอร์มพยากรณ์ RE ของ กฟภ. กำหนด 7 ฟังก์ชันพยากรณ์หลักพร้อมข้อกำหนดความแม่นยำ ข้อกำหนดโครงสร้างพื้นฐาน และมาตรฐานการปฏิบัติตาม",
  features: [
    {
      title: "7 Core Functions",
      titleTh: "7 ฟังก์ชันหลัก",
      description: "RE Forecast, Demand, Load, Imbalance, Voltage, DOE, Hosting Capacity",
      descriptionTh: "พยากรณ์ RE, ความต้องการ, โหลด, ความไม่สมดุล, แรงดัน, DOE, Hosting Capacity",
    },
    {
      title: "POC Scope",
      titleTh: "ขอบเขต POC",
      description: "Function 1 (RE Forecast) + Function 5 (Voltage) for POC testing",
      descriptionTh: "ฟังก์ชัน 1 (พยากรณ์ RE) + ฟังก์ชัน 5 (แรงดัน) สำหรับการทดสอบ POC",
    },
    {
      title: "Compliance",
      titleTh: "การปฏิบัติตาม",
      description: "All TOR 7.1 infrastructure and security requirements",
      descriptionTh: "ข้อกำหนดโครงสร้างพื้นฐานและความปลอดภัยทั้งหมดตาม TOR 7.1",
    },
  ],
  relatedSections: ["tor-7.1", "tor-7.5.1.2", "tor-7.5.1.5"],
  docsUrl: "/docs/tor",
};

// Actual Demand (TOR 7.5.1.2 sub-function)
const torActualDemand: HelpSection = {
  id: "tor-actual-demand",
  title: "TOR 7.5.1.2 - Actual Demand Forecast",
  titleTh: "TOR 7.5.1.2 - พยากรณ์ความต้องการจริง",
  icon: BarChart3,
  description:
    "Forecasts net demand at trading points. Formula: Actual Demand = Gross Load - Behind-the-meter RE + Battery flow. Supports prosumer net metering. Target: MAPE < 5%.",
  descriptionTh:
    "พยากรณ์ความต้องการสุทธิที่จุดซื้อขาย สูตร: ความต้องการจริง = โหลดรวม - RE หลังมิเตอร์ + กระแสแบตเตอรี่ รองรับ net metering ของ prosumer เป้าหมาย: MAPE < 5%",
  features: [
    {
      title: "Net Metering",
      titleTh: "Net Metering",
      description: "Accounts for prosumer solar and storage",
      descriptionTh: "คำนึงถึงโซลาร์และที่เก็บพลังงานของ prosumer",
    },
    {
      title: "Trading Point Focus",
      titleTh: "เน้นจุดซื้อขาย",
      description: "Settlement-ready demand values",
      descriptionTh: "ค่าความต้องการพร้อมสำหรับการชำระเงิน",
    },
    {
      title: "BTM Estimation",
      titleTh: "ประมาณการ BTM",
      description: "Behind-the-meter generation estimation",
      descriptionTh: "การประมาณการผลิตไฟฟ้าหลังมิเตอร์",
    },
  ],
  relatedSections: ["tor-7.5.1.2", "tor-7.5.1.3"],
  docsUrl: "/docs/tor-7.5.1.2-demand",
};

export const torHelp: HelpContentRegistry = {
  "tor-overview": torOverview,
  "tor-7.1": tor71,
  "tor-7.1.4": tor714,
  "tor-7.1.5": tor715,
  "tor-7.1.6": tor716,
  "tor-7.1.7": tor717,
  "tor-7.3.4.4": tor7344,
  "tor-7.5.1.2": tor7512,
  "tor-actual-demand": torActualDemand,
  "tor-7.5.1.3": tor7513,
  "tor-7.5.1.4": tor7514,
  "tor-7.5.1.5": tor7515,
  "tor-7.5.1.6": tor7516,
  "tor-7.5.1.7": tor7517,
};
