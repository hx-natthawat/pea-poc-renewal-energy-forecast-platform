import type { HelpContentRegistry } from "../types";
import { alertsHelp } from "./alerts";
import { auditHelp } from "./audit";
import { gridHelp } from "./grid";
import { historyHelp } from "./history";
import { overviewHelp } from "./overview";
import { solarHelp } from "./solar";
import { voltageHelp } from "./voltage";

export const helpContent: HelpContentRegistry = {
  ...overviewHelp,
  ...solarHelp,
  ...voltageHelp,
  ...gridHelp,
  ...alertsHelp,
  ...historyHelp,
  ...auditHelp,
};

export function getHelpSection(sectionId: string) {
  return helpContent[sectionId] || null;
}

export function getAllSectionIds(): string[] {
  return Object.keys(helpContent);
}
