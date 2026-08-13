"use client";

import { useQuery } from "@tanstack/react-query";
import { Shield, UserCheck, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";
import { api } from "@/lib/api";

export default function AdminUsersPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-officers"],
    queryFn: () => api.admin.officers(),
    retry: false,
  });

  const officers = data?.data.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Personnel Directory"
        title="Operations & Station Admins"
        description="Authorized Western Railway staff, station managers, and divisional officers."
      />

      <Card className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px] text-left text-sm">
            <thead>
              <tr className="border-b border-card-border bg-muted/40 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                <th className="px-5 py-3.5">Official Name</th>
                <th className="px-5 py-3.5">Assigned Roles</th>
                <th className="px-5 py-3.5">Corridor Authority</th>
                <th className="px-5 py-3.5">Status</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={4} className="px-5 py-12 text-center text-muted-foreground">
                    Loading personnel directory…
                  </td>
                </tr>
              )}
              {!isLoading && officers.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-5 py-12 text-center text-muted-foreground">
                    No operations staff found.
                  </td>
                </tr>
              )}
              {officers.map((officer) => (
                <tr key={officer.id} className="border-b border-card-border">
                  <td className="px-5 py-4 font-semibold text-foreground flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent/10 text-accent">
                      <UserCheck className="h-4 w-4" />
                    </div>
                    {officer.display_name}
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex flex-wrap gap-1.5">
                      {officer.roles.map((r) => (
                        <Badge key={r} variant="outline" className="text-[11px]">
                          {r}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="px-5 py-4 text-xs text-muted-foreground">
                    Western Railway Mumbai Division
                  </td>
                  <td className="px-5 py-4">
                    <span className="rounded-full bg-success/15 px-2.5 py-0.5 text-[11px] font-semibold text-success">
                      Active
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
