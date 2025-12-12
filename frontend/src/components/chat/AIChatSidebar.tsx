"use client";

import { useChat } from "@ai-sdk/react";
import { TextStreamChatTransport } from "ai";
import { Bot, Globe, Loader2, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { cn } from "@/lib/utils";
import { useChatStore } from "@/stores/chatStore";
import { ChatInput } from "./ChatInput";
import { ChatMessage } from "./ChatMessage";

export function AIChatSidebar() {
  const { isOpen, language, closeChat, setLanguage } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState("");

  // Create transport with language in body - memoize to prevent recreating on every render
  const transport = useMemo(
    () =>
      new TextStreamChatTransport({
        api: "/api/chat",
        body: { language },
      }),
    [language]
  );

  const { messages, sendMessage, status, stop, error } = useChat({
    id: "pea-ai-chat",
    transport,
  });

  const isLoading = status === "submitted" || status === "streaming";

  // Auto-scroll to bottom on new messages
  // biome-ignore lint/correctness/useExhaustiveDependencies: We want to scroll when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length]);

  // Handle ESC key to close
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        closeChat();
      }
    },
    [isOpen, closeChat]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Prevent body scroll when sidebar is open on mobile
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const getLocalizedText = (en: string, th: string) => (language === "th" ? th : en);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      sendMessage({ text: input });
      setInput("");
    }
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/20 z-40" onClick={closeChat} aria-hidden="true" />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed z-50 top-0 right-0 h-screen",
          "bg-white shadow-xl border-l border-gray-200",
          "flex flex-col",
          "transition-all duration-300 ease-in-out",
          isOpen ? "w-96 max-w-[90vw]" : "w-0"
        )}
        aria-label="AI Chat sidebar"
        aria-hidden={!isOpen}
      >
        {isOpen && (
          <>
            {/* Header */}
            <div className="shrink-0 bg-gradient-to-r from-pea-purple to-[#5A0349] text-white">
              <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20">
                    <Bot className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-sm">
                      {getLocalizedText("AI Assistant", "ผู้ช่วย AI")}
                    </h2>
                    <p className="text-xs text-white/70">
                      {getLocalizedText("PEA RE Forecast", "พยากรณ์ RE ของ กฟภ.")}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* Language toggle */}
                  <button
                    type="button"
                    onClick={() => setLanguage(language === "th" ? "en" : "th")}
                    className="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-white/10 hover:bg-white/20 transition-colors"
                    aria-label={`Switch to ${language === "th" ? "English" : "Thai"}`}
                  >
                    <Globe className="h-3 w-3" />
                    {language === "th" ? "EN" : "TH"}
                  </button>

                  {/* Close button */}
                  <button
                    type="button"
                    onClick={closeChat}
                    className="p-1.5 rounded hover:bg-white/20 transition-colors"
                    aria-label="Close chat"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Messages area */}
            <div className="flex-1 overflow-y-auto">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full p-6 text-center">
                  <div className="w-16 h-16 rounded-full bg-pea-purple/10 flex items-center justify-center mb-4">
                    <Bot className="h-8 w-8 text-pea-purple" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">
                    {getLocalizedText("How can I help you?", "ต้องการให้ช่วยอะไร?")}
                  </h3>
                  <p className="text-sm text-gray-500 max-w-xs">
                    {getLocalizedText(
                      "Ask me about solar forecasts, voltage predictions, or any platform features.",
                      "ถามเกี่ยวกับการพยากรณ์พลังงานแสงอาทิตย์ การพยากรณ์แรงดัน หรือฟีเจอร์ใดๆ ของแพลตฟอร์ม"
                    )}
                  </p>
                </div>
              ) : (
                <div className="py-2">
                  {messages.map((message) => (
                    <ChatMessage key={message.id} message={message} />
                  ))}
                  {isLoading && (
                    <div className="flex items-center gap-2 px-6 py-3 text-gray-500">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">
                        {getLocalizedText("Thinking...", "กำลังคิด...")}
                      </span>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Error display */}
            {error && (
              <div className="px-4 py-2 bg-red-50 border-t border-red-100">
                <p className="text-sm text-red-600">
                  {getLocalizedText(
                    "An error occurred. Please try again.",
                    "เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"
                  )}
                </p>
              </div>
            )}

            {/* Input area */}
            <ChatInput
              input={input}
              setInput={setInput}
              handleSubmit={handleSubmit}
              isLoading={isLoading}
              stop={stop}
              language={language}
            />
          </>
        )}
      </aside>
    </>
  );
}
