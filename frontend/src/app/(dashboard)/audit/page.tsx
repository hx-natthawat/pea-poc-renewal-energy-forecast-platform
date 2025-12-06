import type { Metadata } from "next";
import AuditLogViewer from "@/components/admin/AuditLogViewer";

export const metadata: Metadata = {
  title: "Audit Logs | PEA RE Forecast",
  description: "Security audit logs and access trail for PEA RE Forecast Platform (TOR 7.1.6)",
};

export default function AuditPage() {
  return (
    <main className="min-h-screen bg-gray-50 py-6">
      <div className="container mx-auto px-4">
        <AuditLogViewer />
      </div>
    </main>
  );
}
