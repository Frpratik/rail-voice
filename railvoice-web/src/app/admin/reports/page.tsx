"use client";

import { useState } from "react";
import { FileSpreadsheet, FileText, Send, ShieldCheck } from "lucide-react";
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
    "Station grievance summary report ready for Western Railway Main Authority review."
  );
  const [sending, setSending] = useState(false);

  const download = async (kind: "pdf" | "xlsx") => {
    try {
      if (kind === "pdf") {
        await api.admin.exportPdf();
      } else {
        await api.admin.exportXlsx();
      }
      toast.success(`${kind.toUpperCase()} report download started`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Export failed");
    }
  };

  const notifyMain = async () => {
    setSending(true);
    try {
      const res = await api.admin.notifyMain(remarks);
      toast.success(
        `Official Report Dispatched to ${res.data.notified} WR Super Admins (${res.data.open_issues} open issues included).`
      );
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not notify Main Authority");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Reporting & Escalation"
        title="Official Reports & WR Escalation"
        description={
          persona === "station_admin"
            ? "Generate your station grievance report pack and escalate to Western Railway Main Authority."
            : "Generate Western Railway corridor grievance reports and audit extracts."
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Card elevated className="flex min-h-[220px] flex-col items-center justify-center gap-3 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10 text-accent">
            <FileText className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold tracking-tight">PDF Station Report Pack</h3>
          <p className="max-w-xs text-xs text-muted-foreground">
            Official printable PDF summary of verified station grievances and urgent safety hazards.
          </p>
          <Button variant="accent" onClick={() => download("pdf")}>
            Generate & Download PDF
          </Button>
        </Card>

        <Card elevated className="flex min-h-[220px] flex-col items-center justify-center gap-3 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <FileSpreadsheet className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold tracking-tight">Excel Audit Spreadsheet</h3>
          <p className="max-w-xs text-xs text-muted-foreground">
            Structured XLSX dataset of all grievances, upvote numbers, categories, and resolution logs.
          </p>
          <Button variant="outline" onClick={() => download("xlsx")}>
            Download Excel Spreadsheet
          </Button>
        </Card>
      </div>

      {/* Official Escalation to WR Super Admin */}
      <Card elevated className="space-y-4 p-6 border-accent/30 bg-card">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/10 text-accent">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold tracking-tight">
              Escalate Report to Western Railway Main Authority
            </h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Directly dispatches an official station report notification to the Western Railway Super Admin portal for immediate administrative visibility.
            </p>
          </div>
        </div>
        <Textarea
          value={remarks}
          onChange={(e) => setRemarks(e.target.value)}
          placeholder="Executive summary note for Western Railway Main Authority..."
          className="text-xs"
          rows={3}
        />
        <Button
          variant="accent"
          disabled={sending || remarks.trim().length < 5}
          onClick={() => void notifyMain()}
          className="gap-2"
        >
          <Send className="h-4 w-4" />
          {sending ? "Dispatching Report..." : "Dispatch Escalation Report to WR"}
        </Button>
      </Card>
    </div>
  );
}
