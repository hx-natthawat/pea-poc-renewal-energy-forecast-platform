import type { Metadata } from "next";

import AuditLogViewer from "@/components/admin/AuditLogViewer";

export const metadata: Metadata = {
  title: "Audit Logs | PEA RE Forecast",
  description: "Security audit logs and access trail for PEA RE Forecast Platform (TOR 7.1.6)",
};

export default function AuditPage() {
  return <AuditLogViewer />;
}
