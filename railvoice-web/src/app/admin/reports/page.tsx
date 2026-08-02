"use client";

import { useState } from "react";
import { FileSpreadsheet, FileText, Send } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";
import { Textarea } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { resolvePersona } from "@/lib/roles";

export default function AdminReportsPage() {
  const user = useAuthStore((s) => s.user);
  const persona = user?.persona ?? resolvePersona(user?.roles);
  const [remarks, setRemarks] = useState(
    "Station briefing pack ready for Main Admin review"
  );
  const [sending, setSending] = useState(false);

  const download = async (kind: "pdf" | "xlsx") => {
    try {
      if (kind === "pdf") await api.admin.downloadPdf();
      else await api.admin.downloadXlsx();
      toast.success(`${kind.toUpperCase()} download started`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Export failed");
    }
  };

  const notifyMain = async () => {
    setSending(true);
    try {
      const res = await api.admin.notifyMain(remarks);
      toast.success(
        `Sent to ${res.data.notified} Main Admin · ${res.data.open_issues} open issues`
      );
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not notify Main Admin");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Exports"
        title="Reports"
        description={
          persona === "station_admin"
            ? "Download your station pack, then notify Main Admin."
            : "Download corridor briefing packs and spreadsheet extracts."
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Card elevated className="flex min-h-[200px] flex-col items-center justify-center gap-3 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <FileText className="h-5 w-5" />
          </div>
          <h3 className="font-semibold tracking-tight">PDF briefing pack</h3>
          <p className="max-w-xs text-sm text-muted-foreground">
            Priority-sorted issue snapshot for station and corridor reviews.
          </p>
          <Button variant="accent" onClick={() => download("pdf")}>
            Download PDF
          </Button>
        </Card>

        <Card elevated className="flex min-h-[200px] flex-col items-center justify-center gap-3 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <FileSpreadsheet className="h-5 w-5" />
          </div>
          <h3 className="font-semibold tracking-tight">Excel extract</h3>
          <p className="max-w-xs text-sm text-muted-foreground">
            Filterable rows for offline analysis.
          </p>
          <Button variant="accent" onClick={() => download("xlsx")}>
            Download Excel
          </Button>
        </Card>
      </div>

      {persona === "station_admin" && (
        <Card elevated className="space-y-4 p-6">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/10 text-accent">
              <Send className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-semibold tracking-tight">Send to Main Admin</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Notifies the corridor Main Admin with your open-issue count and a short note.
              </p>
            </div>
          </div>
          <Textarea
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            placeholder="Brief note for Main Admin"
          />
          <Button
            variant="accent"
            disabled={sending || remarks.trim().length < 5}
            onClick={() => void notifyMain()}
          >
            Notify Main Admin
          </Button>
        </Card>
      )}
    </div>
  );
}
