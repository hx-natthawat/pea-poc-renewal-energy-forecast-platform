"use client";

import { create } from "zustand";

interface ChatState {
  isOpen: boolean;
  language: "en" | "th";

  // Actions
  openChat: () => void;
  closeChat: () => void;
  toggleChat: () => void;
  setLanguage: (lang: "en" | "th") => void;
}

export const useChatStore = create<ChatState>((set) => ({
  isOpen: false,
  language: "th", // Default to Thai for PEA

  openChat: () => {
    set({ isOpen: true });
  },

  closeChat: () => {
    set({ isOpen: false });
  },

  toggleChat: () => {
    set((state) => ({ isOpen: !state.isOpen }));
  },

  setLanguage: (lang: "en" | "th") => {
    set({ language: lang });
  },
}));
