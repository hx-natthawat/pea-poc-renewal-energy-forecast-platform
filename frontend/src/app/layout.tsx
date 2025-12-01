import type { Metadata } from "next";
import { Prompt } from "next/font/google";
import "./globals.css";

const prompt = Prompt({
  subsets: ["latin", "thai"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
  variable: "--font-prompt",
});

export const metadata: Metadata = {
  title: "PEA RE Forecast Platform",
  description:
    "แพลตฟอร์มศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียนของ กฟภ. - Renewable Energy Forecast Platform for Provincial Electricity Authority of Thailand",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="th">
      <body className={prompt.className}>
        <div className="min-h-screen bg-[var(--pea-gray-50)]">{children}</div>
      </body>
    </html>
  );
}
