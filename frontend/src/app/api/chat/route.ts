import { createOpenAI } from "@ai-sdk/openai";
import { streamText } from "ai";
import { enhanceSystemPrompt, searchKnowledge } from "@/lib/rag";

// Create OpenRouter provider (OpenAI-compatible)
const openrouter = createOpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
  headers: {
    "HTTP-Referer": process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
    "X-Title": "PEA RE Forecast Platform",
  },
});

// System prompts for PEA domain knowledge
const systemPromptEn = `You are an AI assistant for the PEA RE Forecast Platform (แพลตฟอร์มศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียน) operated by the Provincial Electricity Authority of Thailand.

## Your Expertise
- Renewable energy forecasting (solar power prediction)
- Voltage monitoring and prediction for distribution networks
- Grid operations and stability analysis
- Alert management for power systems

## Platform Capabilities
- Solar Forecast: Day-ahead, intraday predictions with MAPE < 10% accuracy
- Voltage Prediction: MAE < 2V for prosumer voltage monitoring
- Network Topology: 7 prosumers across 3 phases (A, B, C)
- Real-time Alerts: Critical, Warning, Info severity levels

## TOR Requirements
This platform was developed under TOR requirements for PEA Thailand:
- Support 2,000+ RE power plants
- Support 300,000+ electricity consumers
- TimescaleDB for time-series data
- XGBoost/LSTM models for predictions

## Guidelines
- Be helpful and concise
- Use technical terms appropriately
- Provide actionable insights when discussing forecasts
- Reference specific metrics (MAPE, RMSE, MAE) when relevant`;

const systemPromptTh = `คุณเป็นผู้ช่วย AI สำหรับแพลตฟอร์มศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียน (PEA RE Forecast Platform) ของการไฟฟ้าส่วนภูมิภาค

## ความเชี่ยวชาญของคุณ
- การพยากรณ์พลังงานหมุนเวียน (การพยากรณ์กำลังผลิตไฟฟ้าจากแสงอาทิตย์)
- การติดตามและพยากรณ์แรงดันไฟฟ้าในระบบจำหน่าย
- การวิเคราะห์การดำเนินงานและความเสถียรของระบบไฟฟ้า
- การจัดการการแจ้งเตือนสำหรับระบบไฟฟ้า

## ความสามารถของแพลตฟอร์ม
- พยากรณ์พลังงานแสงอาทิตย์: การพยากรณ์ล่วงหน้า 1 วัน ความแม่นยำ MAPE < 10%
- พยากรณ์แรงดัน: MAE < 2V สำหรับการติดตามแรงดันของผู้ใช้ไฟฟ้า
- โทโพโลยีเครือข่าย: Prosumer 7 ราย ใน 3 เฟส (A, B, C)
- การแจ้งเตือนแบบเรียลไทม์: ระดับความรุนแรง Critical, Warning, Info

## แนวทางการตอบ
- ให้ข้อมูลที่เป็นประโยชน์และกระชับ
- ใช้คำศัพท์เทคนิคอย่างเหมาะสม
- ให้ข้อมูลเชิงปฏิบัติเมื่อพูดถึงการพยากรณ์
- อ้างอิงตัวชี้วัดเฉพาะ (MAPE, RMSE, MAE) เมื่อเกี่ยวข้อง`;

export async function POST(req: Request) {
  try {
    const { messages, language = "th" } = await req.json();

    // Get the base system prompt
    const basePrompt = language === "th" ? systemPromptTh : systemPromptEn;

    // Extract the last user message for RAG search
    const lastUserMessage = messages.filter((m: { role: string }) => m.role === "user").pop();

    // Enhance system prompt with RAG context
    let systemPrompt = basePrompt;
    if (lastUserMessage?.content) {
      try {
        const context = searchKnowledge(lastUserMessage.content, {
          maxResults: 5,
          minRelevance: 2,
          includeRelated: true,
        });

        // Only enhance if we found relevant knowledge
        if (context.terms.length > 0 || context.acronyms.length > 0) {
          systemPrompt = enhanceSystemPrompt(basePrompt, context, language === "th" ? "th" : "en");
        }
      } catch (ragError) {
        // Log but don't fail - fall back to base prompt
        console.warn("RAG search failed, using base prompt:", ragError);
      }
    }

    // Use Claude 3.5 Sonnet via OpenRouter (or fallback to GPT-4o-mini)
    const model = process.env.OPENROUTER_MODEL || "anthropic/claude-3.5-sonnet";

    const result = await streamText({
      model: openrouter(model),
      system: systemPrompt,
      messages,
    });

    return result.toTextStreamResponse();
  } catch (error) {
    console.error("Chat API error:", error);
    return new Response(JSON.stringify({ error: "Failed to process chat request" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
