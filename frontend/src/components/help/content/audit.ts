import { Download, FileSearch, Shield } from "lucide-react";
import type { HelpContentRegistry, HelpSection } from "../types";

const auditLog: HelpSection = {
  id: "audit-log",
  title: "Audit Log",
  titleTh: "บันทึกการตรวจสอบ",
  icon: Shield,
  description:
    "Complete audit trail of all system activities as required by TOR 7.1.6. Tracks user actions, API access, and security events for compliance and forensics.",
  descriptionTh:
    "บันทึกการตรวจสอบที่ครบถ้วนของกิจกรรมระบบทั้งหมดตามที่ TOR 7.1.6 กำหนด ติดตามการดำเนินการของผู้ใช้ การเข้าถึง API และเหตุการณ์ด้านความปลอดภัยสำหรับการปฏิบัติตามกฎระเบียบและการสืบสวน",
  features: [
    {
      title: "Action Tracking",
      titleTh: "ติดตามการดำเนินการ",
      description: "Logs all user actions: login, view, create, update, delete",
      descriptionTh: "บันทึกการดำเนินการของผู้ใช้ทั้งหมด: เข้าสู่ระบบ, ดู, สร้าง, อัปเดต, ลบ",
    },
    {
      title: "User Identification",
      titleTh: "ระบุตัวตนผู้ใช้",
      description: "Records user email, IP address, and session ID",
      descriptionTh: "บันทึกอีเมลผู้ใช้, ที่อยู่ IP และ Session ID",
    },
    {
      title: "Request Details",
      titleTh: "รายละเอียดคำขอ",
      description: "Captures HTTP method, path, and response status",
      descriptionTh: "บันทึก HTTP method, path และสถานะการตอบกลับ",
    },
    {
      title: "Time Stamps",
      titleTh: "เวลาประทับ",
      description: "Precise timestamps in Thailand timezone (UTC+7)",
      descriptionTh: "เวลาประทับที่แม่นยำในเขตเวลาประเทศไทย (UTC+7)",
    },
  ],
  relatedSections: ["audit-filters", "audit-export"],
  docsUrl: "/docs/audit-compliance",
  tips: [
    {
      text: "Audit logs are retained for 5 years per TOR requirements",
      textTh: "บันทึกการตรวจสอบถูกเก็บรักษาเป็นเวลา 5 ปีตามข้อกำหนด TOR",
    },
    {
      text: "Use filters to find specific user actions or time periods",
      textTh: "ใช้ตัวกรองเพื่อค้นหาการดำเนินการของผู้ใช้หรือช่วงเวลาเฉพาะ",
    },
  ],
};

const auditFilters: HelpSection = {
  id: "audit-filters",
  title: "Audit Filters",
  titleTh: "ตัวกรองการตรวจสอบ",
  icon: FileSearch,
  description:
    "Filter and search through audit logs to find specific events, users, or time periods.",
  descriptionTh: "กรองและค้นหาบันทึกการตรวจสอบเพื่อค้นหาเหตุการณ์ ผู้ใช้ หรือช่วงเวลาเฉพาะ",
  features: [
    {
      title: "Date Range",
      titleTh: "ช่วงวันที่",
      description: "Filter logs by specific date range",
      descriptionTh: "กรองบันทึกตามช่วงวันที่เฉพาะ",
    },
    {
      title: "Action Type",
      titleTh: "ประเภทการดำเนินการ",
      description: "Filter by action: LOGIN, VIEW, CREATE, UPDATE, DELETE",
      descriptionTh: "กรองตามการดำเนินการ: LOGIN, VIEW, CREATE, UPDATE, DELETE",
    },
    {
      title: "User Filter",
      titleTh: "กรองผู้ใช้",
      description: "Search for specific user's activities",
      descriptionTh: "ค้นหากิจกรรมของผู้ใช้เฉพาะ",
    },
    {
      title: "Resource Filter",
      titleTh: "กรองทรัพยากร",
      description: "Filter by resource type (forecast, voltage, etc.)",
      descriptionTh: "กรองตามประเภททรัพยากร (พยากรณ์, แรงดัน ฯลฯ)",
    },
  ],
  relatedSections: ["audit-log"],
  tips: [
    {
      text: "Combine multiple filters for precise searches",
      textTh: "รวมตัวกรองหลายตัวเพื่อการค้นหาที่แม่นยำ",
    },
  ],
};

const auditExport: HelpSection = {
  id: "audit-export",
  title: "Audit Export",
  titleTh: "ส่งออกการตรวจสอบ",
  icon: Download,
  description:
    "Export audit logs for compliance reporting, security analysis, or legal requirements.",
  descriptionTh:
    "ส่งออกบันทึกการตรวจสอบสำหรับการรายงานการปฏิบัติตามกฎระเบียบ การวิเคราะห์ความปลอดภัย หรือข้อกำหนดทางกฎหมาย",
  features: [
    {
      title: "Export Formats",
      titleTh: "รูปแบบการส่งออก",
      description: "Export as CSV or JSON format",
      descriptionTh: "ส่งออกเป็นรูปแบบ CSV หรือ JSON",
    },
    {
      title: "Filter Application",
      titleTh: "การใช้ตัวกรอง",
      description: "Export only currently filtered data",
      descriptionTh: "ส่งออกเฉพาะข้อมูลที่กรองปัจจุบัน",
    },
    {
      title: "Compliance Ready",
      titleTh: "พร้อมสำหรับการปฏิบัติตาม",
      description: "Formatted for regulatory submission",
      descriptionTh: "จัดรูปแบบสำหรับการส่งตามกฎระเบียบ",
    },
  ],
  relatedSections: ["audit-log", "audit-filters"],
};

export const auditHelp: HelpContentRegistry = {
  "audit-log": auditLog,
  "audit-filters": auditFilters,
  "audit-export": auditExport,
};
