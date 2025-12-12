"use client";

import type { UIMessage } from "@ai-sdk/react";
import { Bot, User } from "lucide-react";

import { cn } from "@/lib/utils";

interface ChatMessageProps {
  message: UIMessage;
}

// Helper to extract text content from message parts
function getMessageContent(message: UIMessage): string {
  if (!message.parts || message.parts.length === 0) {
    return "";
  }

  return message.parts
    .filter((part) => part.type === "text")
    .map((part) => (part as { type: "text"; text: string }).text)
    .join("");
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const content = getMessageContent(message);

  if (!content) {
    return null;
  }

  return (
    <div className={cn("flex gap-3 p-3", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-[#c7911b]/10 text-[#c7911b]" : "bg-[#74045F]/10 text-[#74045F]"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Message bubble */}
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2.5",
          isUser
            ? "bg-[#74045F] text-white rounded-tr-sm"
            : "bg-gray-100 text-gray-900 rounded-tl-sm"
        )}
      >
        <p className="text-sm whitespace-pre-wrap leading-relaxed">{content}</p>
      </div>
    </div>
  );
}
