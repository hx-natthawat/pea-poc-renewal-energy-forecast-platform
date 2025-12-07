"use client";

import { ChevronRight, ExternalLink, Globe, Lightbulb, X } from "lucide-react";
import { useCallback, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useHelpStore } from "@/stores/helpStore";
import { getHelpSection } from "./content";
import type { HelpFeature, HelpSection, HelpTip } from "./types";

export function HelpSidebar() {
  const { isOpen, activeSection, language, closeHelp, openHelp, setLanguage } = useHelpStore();

  const section = activeSection ? getHelpSection(activeSection) : null;

  // Handle ESC key to close
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        closeHelp();
      }
    },
    [isOpen, closeHelp]
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

  return (
    <>
      {/* Backdrop - visible on mobile and tablet */}
      <div
        className={cn(
          "fixed inset-0 bg-black/30 z-40 transition-opacity duration-300",
          // Hide backdrop on large screens (desktop)
          "xl:hidden",
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={closeHelp}
        aria-hidden="true"
      />

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed z-50 bg-white shadow-xl transition-transform duration-300 ease-in-out",
          // Mobile: bottom sheet (up to md)
          "bottom-0 left-0 right-0",
          "max-h-[80vh] rounded-t-2xl",
          // Tablet (md-lg): right sidebar, narrower
          "md:bottom-auto md:left-auto md:right-0 md:top-0",
          "md:h-full md:w-80 md:max-h-full md:rounded-none",
          "md:border-l md:border-gray-200",
          // Desktop (lg+): wider sidebar
          "lg:w-96",
          // XL: even wider for large screens
          "xl:w-[420px]",
          // Transform animations
          // Mobile: slide up from bottom
          isOpen ? "translate-y-0" : "translate-y-full",
          // Tablet/Desktop: slide in from right
          "md:translate-y-0",
          isOpen ? "md:translate-x-0" : "md:translate-x-full"
        )}
        aria-label="Help sidebar"
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200">
          {/* Mobile drag handle - only show on mobile (bottom sheet mode) */}
          <div className="flex justify-center py-2 md:hidden">
            <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
          </div>

          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              {section && (
                <>
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-pea-purple/10 text-pea-purple">
                    <section.icon className="h-5 w-5" />
                  </div>
                  <h2 className="font-semibold text-gray-900">
                    {getLocalizedText(section.title, section.titleTh)}
                  </h2>
                </>
              )}
              {!section && (
                <h2 className="font-semibold text-gray-900">
                  {getLocalizedText("Help", "ช่วยเหลือ")}
                </h2>
              )}
            </div>

            <div className="flex items-center gap-2">
              {/* Language toggle */}
              <button
                type="button"
                onClick={() => setLanguage(language === "th" ? "en" : "th")}
                className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-500 hover:text-gray-700 rounded border border-gray-200 hover:border-gray-300 transition-colors"
                aria-label={`Switch to ${language === "th" ? "English" : "Thai"}`}
              >
                <Globe className="h-3.5 w-3.5" />
                {language === "th" ? "EN" : "TH"}
              </button>

              {/* Close button */}
              <button
                type="button"
                onClick={closeHelp}
                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Close help sidebar"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto h-[calc(100%-4rem)] md:h-[calc(100%-3.5rem)] p-4 md:p-5 lg:p-6 space-y-6">
          {section ? (
            <HelpContent section={section} language={language} onNavigate={openHelp} />
          ) : (
            <div className="text-center text-gray-500 py-8">
              {getLocalizedText("Select a help topic", "เลือกหัวข้อช่วยเหลือ")}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

interface HelpContentProps {
  section: HelpSection;
  language: "en" | "th";
  onNavigate: (sectionId: string) => void;
}

function HelpContent({ section, language, onNavigate }: HelpContentProps) {
  const getLocalizedText = (en: string, th: string) => (language === "th" ? th : en);

  return (
    <>
      {/* Description */}
      <p className="text-sm text-gray-600 leading-relaxed">
        {getLocalizedText(section.description, section.descriptionTh)}
      </p>

      {/* Features */}
      {section.features.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            {getLocalizedText("Key Features", "คุณสมบัติหลัก")}
          </h3>
          <ul className="space-y-3">
            {section.features.map((feature: HelpFeature) => (
              <li key={feature.title} className="flex gap-3">
                <div className="flex-shrink-0 h-1.5 w-1.5 mt-2 rounded-full bg-pea-purple" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {getLocalizedText(feature.title, feature.titleTh)}
                  </p>
                  <p className="text-sm text-gray-500 mt-0.5">
                    {getLocalizedText(feature.description, feature.descriptionTh)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Tips */}
      {section.tips && section.tips.length > 0 && (
        <div className="bg-amber-50 rounded-lg p-4 border border-amber-100">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="h-4 w-4 text-amber-600" />
            <h3 className="text-xs font-semibold text-amber-800 uppercase tracking-wider">
              {getLocalizedText("Tips", "เคล็ดลับ")}
            </h3>
          </div>
          <ul className="space-y-2">
            {section.tips.map((tip: HelpTip) => (
              <li key={tip.text} className="text-sm text-amber-800">
                • {getLocalizedText(tip.text, tip.textTh)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Related sections */}
      {section.relatedSections && section.relatedSections.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            {getLocalizedText("Related Topics", "หัวข้อที่เกี่ยวข้อง")}
          </h3>
          <ul className="space-y-1">
            {section.relatedSections.map((relatedId: string) => {
              const related = getHelpSection(relatedId);
              if (!related) return null;
              return (
                <li key={relatedId}>
                  <button
                    type="button"
                    onClick={() => onNavigate(relatedId)}
                    className="w-full flex items-center justify-between px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors group"
                  >
                    <span className="flex items-center gap-2">
                      <related.icon className="h-4 w-4 text-gray-400 group-hover:text-pea-purple" />
                      {getLocalizedText(related.title, related.titleTh)}
                    </span>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-pea-purple" />
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Documentation link */}
      {section.docsUrl && (
        <div className="pt-4 border-t border-gray-200">
          <a
            href={section.docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full px-4 py-2.5 text-sm font-medium text-pea-purple bg-pea-purple/5 hover:bg-pea-purple/10 rounded-lg transition-colors"
          >
            <ExternalLink className="h-4 w-4" />
            {getLocalizedText("View Full Documentation", "ดูเอกสารฉบับเต็ม")}
          </a>
        </div>
      )}
    </>
  );
}
