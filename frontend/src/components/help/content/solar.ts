import { BarChart3, Sun, TrendingUp } from "lucide-react";
import type { HelpContentRegistry, HelpSection } from "../types";

const solarForecast: HelpSection = {
  id: "solar-forecast",
  title: "Solar Forecast",
  titleTh: "พยากรณ์พลังงานแสงอาทิตย์",
  icon: Sun,
  description:
    "Displays predicted solar power output based on weather conditions, historical patterns, and ML model predictions. Our XGBoost model achieves MAPE < 10% accuracy as required by TOR.",
  descriptionTh:
    "แสดงกำลังผลิตไฟฟ้าพลังงานแสงอาทิตย์ที่คาดการณ์ไว้ ตามสภาพอากาศ รูปแบบในอดีต และการพยากรณ์ของโมเดล ML โมเดล XGBoost ของเรามีความแม่นยำ MAPE < 10% ตามที่ TOR กำหนด",
  features: [
    {
      title: "Day-Ahead Forecast",
      titleTh: "พยากรณ์ล่วงหน้า 1 วัน",
      description: "See tomorrow's expected solar generation with hourly resolution",
      descriptionTh: "ดูการผลิตไฟฟ้าแสงอาทิตย์ที่คาดว่าจะเกิดขึ้นในวันพรุ่งนี้แบบรายชั่วโมง",
    },
    {
      title: "Confidence Intervals",
      titleTh: "ช่วงความเชื่อมั่น",
      description: "Shaded areas show prediction uncertainty (80% and 95% confidence)",
      descriptionTh: "พื้นที่แรเงาแสดงความไม่แน่นอนของการพยากรณ์ (ความเชื่อมั่น 80% และ 95%)",
    },
    {
      title: "Actual vs Predicted",
      titleTh: "ค่าจริง vs ค่าพยากรณ์",
      description: "Compare real-time actuals (solid line) against forecasted values (dashed line)",
      descriptionTh: "เปรียบเทียบค่าจริงแบบ real-time (เส้นทึบ) กับค่าที่พยากรณ์ไว้ (เส้นประ)",
    },
    {
      title: "Time Range Selection",
      titleTh: "เลือกช่วงเวลา",
      description: "Switch between 6h, 12h, 24h, and 7-day views",
      descriptionTh: "สลับระหว่างมุมมอง 6 ชั่วโมง, 12 ชั่วโมง, 24 ชั่วโมง และ 7 วัน",
    },
  ],
  relatedSections: ["model-performance", "forecast-comparison", "day-ahead-report"],
  docsUrl: "/docs/solar-forecast",
  tips: [
    {
      text: "Hover over data points to see exact values and timestamps",
      textTh: "วางเมาส์เหนือจุดข้อมูลเพื่อดูค่าและเวลาที่แน่นอน",
    },
    {
      text: "Use the export button to download forecast data as CSV",
      textTh: "ใช้ปุ่มส่งออกเพื่อดาวน์โหลดข้อมูลพยากรณ์เป็น CSV",
    },
    {
      text: "Peak solar hours are typically 10:00 - 14:00",
      textTh: "ช่วงพีคของพลังงานแสงอาทิตย์โดยทั่วไปคือ 10:00 - 14:00",
    },
  ],
};

const forecastComparison: HelpSection = {
  id: "forecast-comparison",
  title: "Forecast Comparison",
  titleTh: "เปรียบเทียบการพยากรณ์",
  icon: BarChart3,
  description:
    "Compare predictions from different ML models side by side. Useful for evaluating model performance and selecting the best forecast.",
  descriptionTh:
    "เปรียบเทียบการพยากรณ์จากโมเดล ML ต่างๆ แบบเคียงข้างกัน มีประโยชน์สำหรับการประเมินประสิทธิภาพโมเดลและเลือกการพยากรณ์ที่ดีที่สุด",
  features: [
    {
      title: "Model Selection",
      titleTh: "เลือกโมเดล",
      description: "Choose which models to display (XGBoost, LSTM, Ensemble)",
      descriptionTh: "เลือกโมเดลที่จะแสดง (XGBoost, LSTM, Ensemble)",
    },
    {
      title: "Error Metrics",
      titleTh: "ตัวชี้วัดความผิดพลาด",
      description: "View MAPE, RMSE, and MAE for each model",
      descriptionTh: "ดู MAPE, RMSE และ MAE สำหรับแต่ละโมเดล",
    },
    {
      title: "Time Alignment",
      titleTh: "การจัดเรียงเวลา",
      description: "All models are synchronized to the same time axis",
      descriptionTh: "โมเดลทั้งหมดถูกซิงค์กับแกนเวลาเดียวกัน",
    },
  ],
  relatedSections: ["solar-forecast", "model-performance"],
};

const modelPerformance: HelpSection = {
  id: "model-performance",
  title: "Model Performance",
  titleTh: "ประสิทธิภาพโมเดล",
  icon: TrendingUp,
  description:
    "Track ML model accuracy metrics over time. Monitors for drift and triggers retraining when performance degrades.",
  descriptionTh:
    "ติดตามตัวชี้วัดความแม่นยำของโมเดล ML ตลอดเวลา ตรวจสอบการเบี่ยงเบนและทริกเกอร์การฝึกซ้ำเมื่อประสิทธิภาพลดลง",
  features: [
    {
      title: "Accuracy Metrics",
      titleTh: "ตัวชี้วัดความแม่นยำ",
      description: "MAPE (target < 10%), RMSE, R-squared values",
      descriptionTh: "MAPE (เป้าหมาย < 10%), RMSE, ค่า R-squared",
    },
    {
      title: "Drift Detection",
      titleTh: "ตรวจจับการเบี่ยงเบน",
      description: "Alerts when model accuracy drops below threshold",
      descriptionTh: "แจ้งเตือนเมื่อความแม่นยำของโมเดลต่ำกว่าเกณฑ์",
    },
    {
      title: "Training History",
      titleTh: "ประวัติการฝึก",
      description: "View when models were last trained and deployed",
      descriptionTh: "ดูว่าโมเดลถูกฝึกและปรับใช้ครั้งสุดท้ายเมื่อใด",
    },
  ],
  relatedSections: ["solar-forecast", "forecast-comparison"],
  tips: [
    {
      text: "Green status means the model meets TOR accuracy requirements",
      textTh: "สถานะสีเขียวหมายความว่าโมเดลผ่านเกณฑ์ความแม่นยำตาม TOR",
    },
  ],
};

export const solarHelp: HelpContentRegistry = {
  "solar-forecast": solarForecast,
  "forecast-comparison": forecastComparison,
  "model-performance": modelPerformance,
};
