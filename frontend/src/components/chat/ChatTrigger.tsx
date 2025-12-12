"use client";

import { MessageCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useChatStore } from "@/stores/chatStore";

export function ChatTrigger() {
  const { isOpen, toggleChat } = useChatStore();

  return (
    <button
      type="button"
      onClick={toggleChat}
      className={cn(
        "fixed z-40 bottom-6 right-6",
        "w-14 h-14 rounded-full shadow-lg",
        "flex items-center justify-center",
        "bg-[#74045F] text-white",
        "hover:bg-[#5A0349] active:bg-[#4A0339]",
        "transition-all duration-300 ease-in-out",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-[#74045F] focus-visible:ring-offset-2",
        // Move up on mobile to avoid bottom nav
        "max-md:bottom-20"
      )}
      aria-label={isOpen ? "Close AI assistant" : "Open AI assistant"}
      aria-expanded={isOpen}
      aria-haspopup="dialog"
    >
      <div className={cn("transition-transform duration-300", isOpen ? "rotate-0" : "rotate-0")}>
        {isOpen ? <X className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
      </div>
      {/* Pulse animation when closed */}
      {!isOpen && (
        <span className="absolute inset-0 rounded-full bg-[#74045F] animate-ping opacity-20" />
      )}
    </button>
  );
}
