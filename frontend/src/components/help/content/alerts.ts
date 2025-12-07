import { Bell, MessageSquare, Settings } from "lucide-react";
import type { HelpContentRegistry, HelpSection } from "../types";

const alertDashboard: HelpSection = {
  id: "alert-dashboard",
  title: "Alert Dashboard",
  titleTh: "แดชบอร์ดการแจ้งเตือน",
  icon: Bell,
  description:
    "Centralized view of all system alerts including voltage violations, forecast accuracy drops, and system health issues. Supports multi-channel notifications (Email, LINE Notify).",
  descriptionTh:
    "มุมมองรวมของการแจ้งเตือนระบบทั้งหมด รวมถึงการละเมิดแรงดัน ความแม่นยำพยากรณ์ลดลง และปัญหาสุขภาพระบบ รองรับการแจ้งเตือนหลายช่องทาง (Email, LINE Notify)",
  features: [
    {
      title: "Alert Timeline",
      titleTh: "ไทม์ไลน์การแจ้งเตือน",
      description: "Chronological view of recent alerts with severity colors",
      descriptionTh: "มุมมองตามลำดับเวลาของการแจ้งเตือนล่าสุดพร้อมสีความรุนแรง",
    },
    {
      title: "Alert Categories",
      titleTh: "หมวดหมู่การแจ้งเตือน",
      description: "Filter by type: Voltage, Forecast, System, Security",
      descriptionTh: "กรองตามประเภท: แรงดัน, พยากรณ์, ระบบ, ความปลอดภัย",
    },
    {
      title: "Quick Actions",
      titleTh: "ดำเนินการด่วน",
      description: "Acknowledge, dismiss, or escalate alerts directly",
      descriptionTh: "รับทราบ, ปิด หรือส่งต่อการแจ้งเตือนโดยตรง",
    },
    {
      title: "Alert Statistics",
      titleTh: "สถิติการแจ้งเตือน",
      description: "View alert trends and patterns over time",
      descriptionTh: "ดูแนวโน้มและรูปแบบการแจ้งเตือนตลอดเวลา",
    },
  ],
  relatedSections: ["voltage-monitor", "model-performance"],
  docsUrl: "/docs/alerts",
  tips: [
    {
      text: "Critical alerts trigger immediate LINE notifications",
      textTh: "การแจ้งเตือนวิกฤตจะทริกเกอร์การแจ้งเตือน LINE ทันที",
    },
    {
      text: "Acknowledged alerts are moved to history after 24 hours",
      textTh: "การแจ้งเตือนที่รับทราบแล้วจะถูกย้ายไปยังประวัติหลังจาก 24 ชั่วโมง",
    },
  ],
};

const alertConfiguration: HelpSection = {
  id: "alert-configuration",
  title: "Alert Configuration",
  titleTh: "การกำหนดค่าการแจ้งเตือน",
  icon: Settings,
  description:
    "Configure alert thresholds, notification channels, and escalation rules for different alert types.",
  descriptionTh: "กำหนดค่าเกณฑ์การแจ้งเตือน ช่องทางการแจ้งเตือน และกฎการส่งต่อสำหรับประเภทการแจ้งเตือนต่างๆ",
  features: [
    {
      title: "Threshold Settings",
      titleTh: "การตั้งค่าเกณฑ์",
      description: "Set custom thresholds for voltage warnings and critical alerts",
      descriptionTh: "ตั้งค่าเกณฑ์ที่กำหนดเองสำหรับการเตือนแรงดันและการแจ้งเตือนวิกฤต",
    },
    {
      title: "Notification Channels",
      titleTh: "ช่องทางการแจ้งเตือน",
      description: "Configure Email and LINE Notify recipients",
      descriptionTh: "กำหนดค่าผู้รับ Email และ LINE Notify",
    },
    {
      title: "Escalation Rules",
      titleTh: "กฎการส่งต่อ",
      description: "Set up automatic escalation for unacknowledged alerts",
      descriptionTh: "ตั้งค่าการส่งต่ออัตโนมัติสำหรับการแจ้งเตือนที่ยังไม่ได้รับทราบ",
    },
  ],
  relatedSections: ["alert-dashboard"],
  tips: [
    {
      text: "Test notification channels before going live",
      textTh: "ทดสอบช่องทางการแจ้งเตือนก่อนใช้งานจริง",
    },
  ],
};

const notificationChannels: HelpSection = {
  id: "notification-channels",
  title: "Notification Channels",
  titleTh: "ช่องทางการแจ้งเตือน",
  icon: MessageSquare,
  description:
    "Multi-channel notification system supporting Email and LINE Notify for real-time alert delivery.",
  descriptionTh:
    "ระบบแจ้งเตือนหลายช่องทางรองรับ Email และ LINE Notify สำหรับการส่งการแจ้งเตือนแบบ real-time",
  features: [
    {
      title: "Email Notifications",
      titleTh: "การแจ้งเตือนทาง Email",
      description: "Send detailed alert reports to configured email addresses",
      descriptionTh: "ส่งรายงานการแจ้งเตือนโดยละเอียดไปยังที่อยู่อีเมลที่กำหนด",
    },
    {
      title: "LINE Notify",
      titleTh: "LINE Notify",
      description: "Instant mobile alerts via LINE messaging",
      descriptionTh: "การแจ้งเตือนมือถือทันทีผ่าน LINE messaging",
    },
    {
      title: "Severity Routing",
      titleTh: "การกำหนดเส้นทางตามความรุนแรง",
      description: "Different channels for different severity levels",
      descriptionTh: "ช่องทางต่างกันสำหรับระดับความรุนแรงที่แตกต่างกัน",
    },
  ],
  relatedSections: ["alert-dashboard", "alert-configuration"],
};

export const alertsHelp: HelpContentRegistry = {
  "alert-dashboard": alertDashboard,
  "alert-configuration": alertConfiguration,
  "notification-channels": notificationChannels,
};
