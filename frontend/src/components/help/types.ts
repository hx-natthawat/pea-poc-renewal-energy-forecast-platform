import type { LucideIcon } from "lucide-react";

export interface HelpFeature {
  title: string;
  titleTh: string;
  description: string;
  descriptionTh: string;
}

export interface HelpTip {
  text: string;
  textTh: string;
}

export interface HelpSection {
  id: string;
  title: string;
  titleTh: string;
  icon: LucideIcon;
  description: string;
  descriptionTh: string;
  features: HelpFeature[];
  relatedSections?: string[];
  docsUrl?: string;
  tips?: HelpTip[];
}

export type HelpContentRegistry = Record<string, HelpSection>;
