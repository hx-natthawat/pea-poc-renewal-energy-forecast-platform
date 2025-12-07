import { BarChart2, Scale, TrendingUp } from "lucide-react";
import type { HelpContentRegistry, HelpSection } from "../types";

const loadForecast: HelpSection = {
  id: "load-forecast",
  title: "Load Forecast",
  titleTh: "พยากรณ์โหลด",
  icon: TrendingUp,
  description:
    "Predicts electrical load (demand) at different grid levels: system, area, substation, and feeder. Supports grid operators in dispatch planning and resource allocation.",
  descriptionTh:
    "พยากรณ์โหลดไฟฟ้า (ความต้องการ) ในระดับกริดต่างๆ: ระบบ, พื้นที่, สถานีไฟฟ้าย่อย และสายป้อน สนับสนุนผู้ปฏิบัติงานกริดในการวางแผนจ่ายโหลดและจัดสรรทรัพยากร",
  features: [
    {
      title: "Level Selection",
      titleTh: "เลือกระดับ",
      description: "Choose between System, Area, Substation, or Feeder level forecasts",
      descriptionTh: "เลือกระหว่างการพยากรณ์ระดับ ระบบ, พื้นที่, สถานีไฟฟ้าย่อย หรือสายป้อน",
    },
    {
      title: "Peak Detection",
      titleTh: "ตรวจจับพีค",
      description: "Highlights expected peak load times",
      descriptionTh: "เน้นช่วงเวลาที่คาดว่าโหลดจะสูงสุด",
    },
    {
      title: "Capacity Margins",
      titleTh: "ส่วนต่างความจุ",
      description: "Shows available capacity vs forecasted demand",
      descriptionTh: "แสดงความจุที่มีอยู่เทียบกับความต้องการที่พยากรณ์",
    },
  ],
  relatedSections: ["demand-forecast", "imbalance-monitor"],
  docsUrl: "/docs/load-forecast",
  tips: [
    {
      text: "Peak loads typically occur between 18:00-21:00 in Thailand",
      textTh: "โหลดสูงสุดมักเกิดขึ้นระหว่าง 18:00-21:00 ในประเทศไทย",
    },
    {
      text: "Compare with solar generation to identify net load",
      textTh: "เปรียบเทียบกับการผลิตไฟฟ้าแสงอาทิตย์เพื่อระบุโหลดสุทธิ",
    },
  ],
};

const demandForecast: HelpSection = {
  id: "demand-forecast",
  title: "Demand Forecast",
  titleTh: "พยากรณ์ความต้องการ",
  icon: BarChart2,
  description:
    "Forecasts energy demand including net demand (after RE generation), gross demand, and RE contribution breakdown.",
  descriptionTh:
    "พยากรณ์ความต้องการพลังงานรวมถึงความต้องการสุทธิ (หลังการผลิต RE), ความต้องการรวม และการแยกส่วนการมีส่วนร่วมของ RE",
  features: [
    {
      title: "Demand Components",
      titleTh: "ส่วนประกอบความต้องการ",
      description: "View Net Demand, Gross Demand, or RE contribution",
      descriptionTh: "ดูความต้องการสุทธิ, ความต้องการรวม หรือการมีส่วนร่วมของ RE",
    },
    {
      title: "Day Selection",
      titleTh: "เลือกวัน",
      description: "Switch between today and tomorrow's forecast",
      descriptionTh: "สลับระหว่างการพยากรณ์วันนี้และวันพรุ่งนี้",
    },
    {
      title: "RE Impact",
      titleTh: "ผลกระทบ RE",
      description: "Shows how RE generation reduces net demand",
      descriptionTh: "แสดงว่าการผลิต RE ลดความต้องการสุทธิอย่างไร",
    },
  ],
  relatedSections: ["load-forecast", "solar-forecast"],
  tips: [
    {
      text: "Net demand = Gross demand - RE generation",
      textTh: "ความต้องการสุทธิ = ความต้องการรวม - การผลิต RE",
    },
  ],
};

const imbalanceMonitor: HelpSection = {
  id: "imbalance-monitor",
  title: "Imbalance Monitor",
  titleTh: "ตรวจสอบความไม่สมดุล",
  icon: Scale,
  description:
    "Monitors and predicts grid imbalance between generation and demand. Critical for maintaining grid frequency and stability.",
  descriptionTh:
    "ตรวจสอบและพยากรณ์ความไม่สมดุลของกริดระหว่างการผลิตและความต้องการ สำคัญสำหรับการรักษาความถี่และเสถียรภาพของกริด",
  features: [
    {
      title: "Imbalance Value",
      titleTh: "ค่าความไม่สมดุล",
      description: "Positive = excess generation, Negative = excess demand",
      descriptionTh: "บวก = การผลิตเกิน, ลบ = ความต้องการเกิน",
    },
    {
      title: "Severity Indicator",
      titleTh: "ตัวบ่งชี้ความรุนแรง",
      description: "Color-coded: Green (normal), Yellow (warning), Red (critical)",
      descriptionTh: "รหัสสี: เขียว (ปกติ), เหลือง (เตือน), แดง (วิกฤต)",
    },
    {
      title: "Trend Arrow",
      titleTh: "ลูกศรแนวโน้ม",
      description: "Shows if imbalance is increasing or decreasing",
      descriptionTh: "แสดงว่าความไม่สมดุลเพิ่มขึ้นหรือลดลง",
    },
  ],
  relatedSections: ["load-forecast", "demand-forecast"],
  tips: [
    {
      text: "Large imbalances can indicate need for dispatch adjustment",
      textTh: "ความไม่สมดุลขนาดใหญ่อาจบ่งบอกถึงความจำเป็นในการปรับการจ่ายโหลด",
    },
    {
      text: "Solar ramp rates in morning/evening can cause rapid imbalance changes",
      textTh:
        "อัตราการเปลี่ยนแปลงพลังงานแสงอาทิตย์ในช่วงเช้า/เย็นอาจทำให้เกิดการเปลี่ยนแปลงความไม่สมดุลอย่างรวดเร็ว",
    },
  ],
};

export const gridHelp: HelpContentRegistry = {
  "load-forecast": loadForecast,
  "demand-forecast": demandForecast,
  "imbalance-monitor": imbalanceMonitor,
};
