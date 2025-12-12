"use client";

import { Send, Square } from "lucide-react";
import type { FormEvent, KeyboardEvent } from "react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  input: string;
  setInput: (value: string) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
  isLoading: boolean;
  stop: () => void;
  language: "en" | "th";
}

export function ChatInput({
  input,
  setInput,
  handleSubmit,
  isLoading,
  stop,
  language,
}: ChatInputProps) {
  const placeholder = language === "th" ? "พิมพ์ข้อความ..." : "Type a message...";

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isLoading) {
        const form = e.currentTarget.form;
        if (form) {
          form.requestSubmit();
        }
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 p-3 border-t border-gray-200">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isLoading}
        rows={1}
        className={cn(
          "flex-1 resize-none rounded-xl border border-gray-200",
          "px-4 py-2.5 text-sm",
          "focus:outline-none focus:ring-2 focus:ring-[#74045F]/20 focus:border-[#74045F]",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "placeholder:text-gray-400",
          "max-h-32"
        )}
        style={{
          minHeight: "44px",
          height: "auto",
        }}
      />

      {isLoading ? (
        <button
          type="button"
          onClick={stop}
          className={cn(
            "flex-shrink-0 w-11 h-11 rounded-xl",
            "flex items-center justify-center",
            "bg-red-500 text-white",
            "hover:bg-red-600 active:bg-red-700",
            "transition-colors"
          )}
          aria-label="Stop generating"
        >
          <Square className="h-4 w-4 fill-current" />
        </button>
      ) : (
        <button
          type="submit"
          disabled={!input.trim()}
          className={cn(
            "flex-shrink-0 w-11 h-11 rounded-xl",
            "flex items-center justify-center",
            "bg-[#74045F] text-white",
            "hover:bg-[#5A0349] active:bg-[#4A0339]",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "transition-colors"
          )}
          aria-label="Send message"
        >
          <Send className="h-4 w-4" />
        </button>
      )}
    </form>
  );
}
