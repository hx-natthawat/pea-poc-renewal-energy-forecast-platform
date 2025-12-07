"use client";

import { create } from "zustand";

interface HelpState {
  isOpen: boolean;
  activeSection: string | null;
  language: "en" | "th";

  // Actions
  openHelp: (sectionId: string) => void;
  closeHelp: () => void;
  toggleHelp: (sectionId: string) => void;
  setLanguage: (lang: "en" | "th") => void;
}

export const useHelpStore = create<HelpState>((set, get) => ({
  isOpen: false,
  activeSection: null,
  language: "th", // Default to Thai for PEA

  openHelp: (sectionId: string) => {
    set({ isOpen: true, activeSection: sectionId });
  },

  closeHelp: () => {
    set({ isOpen: false });
  },

  toggleHelp: (sectionId: string) => {
    const { isOpen, activeSection } = get();
    if (isOpen && activeSection === sectionId) {
      set({ isOpen: false });
    } else {
      set({ isOpen: true, activeSection: sectionId });
    }
  },

  setLanguage: (lang: "en" | "th") => {
    set({ language: lang });
  },
}));
