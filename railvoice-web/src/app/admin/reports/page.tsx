"use client";

import { FileSpreadsheet, FileText } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";
import { api } from "@/lib/api";

export default function AdminReportsPage() {
  const download = async (kind: "pdf" | "xlsx") => {
    try {
      if (kind === "pdf") await api.admin.downloadPdf();
      else await api.admin.downloadXlsx();
      toast.success(`${kind.toUpperCase()} download started`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Export failed");
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Exports"
        title="Reports"
        description="Download briefing packs and spreadsheet extracts of the public issue queue."
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Card elevated className="flex min-h-[200px] flex-col items-center justify-center gap-3 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <FileText className="h-5 w-5" />
          </div>
          <h3 className="font-semibold tracking-tight">PDF briefing pack</h3>
          <p className="max-w-xs text-sm text-muted-foreground">
            Priority-sorted issue snapshot for station and division reviews.
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
            Filterable rows for offline analysis and RailMadad handoff.
          </p>
          <Button variant="accent" onClick={() => download("xlsx")}>
            Download Excel
          </Button>
        </Card>
      </div>
    </div>
  );
}
