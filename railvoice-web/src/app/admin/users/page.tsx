"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { ManagedUser } from "@/lib/types";
import { resolvePersona } from "@/lib/roles";
import { cn, formatRelativeTime } from "@/lib/utils";

function StatusBadge({ status }: { status: string }) {
  const tones: Record<string, string> = {
    active: "bg-success/15 text-success",
    inactive: "bg-muted text-muted-foreground",
    locked: "bg-destructive/15 text-destructive",
    deleted: "bg-destructive/10 text-destructive",
  };
  return (
    <span
      className={cn(
        "rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
        tones[status] || "bg-muted text-muted-foreground"
      )}
    >
      {status}
    </span>
  );
}

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const authUser = useAuthStore((s) => s.user);
  const persona = authUser?.persona ?? resolvePersona(authUser?.roles);
  const isMain = persona === "main_admin";

  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [role, setRole] = useState("");
  const [page, setPage] = useState(1);
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [selected, setSelected] = useState<ManagedUser | null>(null);
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [roleCode, setRoleCode] = useState("passenger");
  const [stationId, setStationId] = useState("");
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createMobile, setCreateMobile] = useState("+91");
  const [createEmail, setCreateEmail] = useState("");
  const [createRole, setCreateRole] = useState("passenger");
  const [createStationId, setCreateStationId] = useState("");
  const [createGenPassword, setCreateGenPassword] = useState(true);
  const [createTempPassword, setCreateTempPassword] = useState<string | null>(null);

  const { data: stationsData } = useQuery({
    queryKey: ["stations"],
    queryFn: () => api.stations.list(),
  });
  const stations = stationsData?.data ?? [];

  const listParams = useMemo(
    () => ({
      q: q || undefined,
      status: status || undefined,
      role: role || undefined,
      page,
      page_size: 20,
      sort: "created_at",
      order: "desc",
      include_deleted: isMain ? includeDeleted : undefined,
    }),
    [q, status, role, page, includeDeleted, isMain]
  );

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-users", listParams],
    queryFn: () => api.admin.users.list(listParams),
    retry: false,
  });

  const { data: auditsData } = useQuery({
    queryKey: ["user-audits", selected?.id],
    queryFn: () => api.admin.users.audits(selected!.id),
    enabled: !!selected,
  });

  const items = data?.data.items ?? [];
  const pagination = data?.data.pagination;
  const audits = auditsData?.data.items ?? [];

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    if (selected) {
      queryClient.invalidateQueries({ queryKey: ["user-audits", selected.id] });
    }
  };

  const openUser = (u: ManagedUser) => {
    setSelected(u);
    setEditName(u.display_name);
    setEditEmail(u.email || "");
    setRoleCode(u.roles[0] === "super_admin" ? "super_admin" : u.roles[0] === "station_manager" ? "station_manager" : "passenger");
    setStationId(u.assigned_station_id || "");
    setTempPassword(null);
  };

  const run = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      toast.success(ok);
      invalidate();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Action failed");
    }
  };

  const saveProfile = () =>
    run(
      () =>
        api.admin.users.update(selected!.id, {
          display_name: editName,
          email: editEmail || undefined,
        }),
      "User updated"
    );

  const resetCreateForm = () => {
    setCreateName("");
    setCreateMobile("+91");
    setCreateEmail("");
    setCreateRole("passenger");
    setCreateStationId("");
    setCreateGenPassword(true);
    setCreateTempPassword(null);
  };

  const submitCreate = async () => {
    if (!createName.trim() || !/^\+91\d{10}$/.test(createMobile.trim())) {
      toast.error("Name and mobile (+91XXXXXXXXXX) are required");
      return;
    }
    if (createRole === "station_manager" && !createStationId) {
      toast.error("Select a station for Station Admin");
      return;
    }
    try {
      const res = await api.admin.users.create({
        mobile: createMobile.trim(),
        display_name: createName.trim(),
        email: createEmail.trim() || undefined,
        role_code: createRole,
        station_id: createStationId || null,
        generate_password: createGenPassword,
      });
      setCreateTempPassword(res.data.temporary_password);
      toast.success("User created");
      invalidate();
      openUser(res.data.user);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Create failed");
    }
  };

  const toggleCheck = (id: string) => {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Administration"
        title="User management"
        description={
          isMain
            ? "Full control over all registered users across the corridor."
            : "Manage users assigned to your station only."
        }
        action={
          isMain ? (
            <Button
              onClick={() => {
                resetCreateForm();
                setShowCreate((v) => !v);
              }}
            >
              {showCreate ? "Close form" : "Create user"}
            </Button>
          ) : undefined
        }
      />

      {isMain && showCreate && (
        <Card className="space-y-4 p-4 sm:p-5">
          <div>
            <h2 className="text-base font-semibold">Create user</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Provisions a registered account. They can still sign in with OTP on that mobile.
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <Label htmlFor="create-name">Display name</Label>
              <Input
                id="create-name"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="Full name"
              />
            </div>
            <div>
              <Label htmlFor="create-mobile">Mobile</Label>
              <Input
                id="create-mobile"
                value={createMobile}
                onChange={(e) => setCreateMobile(e.target.value)}
                placeholder="+9198XXXXXXXX"
              />
            </div>
            <div>
              <Label htmlFor="create-email">Email (optional)</Label>
              <Input
                id="create-email"
                type="email"
                value={createEmail}
                onChange={(e) => setCreateEmail(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="create-role">Role</Label>
              <Select
                id="create-role"
                value={createRole}
                onChange={(e) => setCreateRole(e.target.value)}
              >
                <option value="passenger">Passenger</option>
                <option value="station_manager">Station Admin</option>
                <option value="super_admin">Main Admin</option>
              </Select>
            </div>
            {(createRole === "station_manager" || createRole === "passenger") && (
              <div>
                <Label htmlFor="create-station">
                  {createRole === "station_manager" ? "Station (required)" : "Assigned station (optional)"}
                </Label>
                <Select
                  id="create-station"
                  value={createStationId}
                  onChange={(e) => setCreateStationId(e.target.value)}
                >
                  <option value="">Select station</option>
                  {stations.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.code})
                    </option>
                  ))}
                </Select>
              </div>
            )}
            <label className="flex items-center gap-2 self-end pb-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={createGenPassword}
                onChange={(e) => setCreateGenPassword(e.target.checked)}
              />
              Generate temporary password
            </label>
          </div>
          {createTempPassword && (
            <div className="rounded-xl border border-accent/30 bg-accent/5 px-3 py-2 text-sm">
              Temporary password:{" "}
              <span className="font-mono font-semibold">{createTempPassword}</span>
              <p className="mt-1 text-xs text-muted-foreground">
                Share once securely. OTP login still works with the mobile number.
              </p>
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => void submitCreate()}>Create user</Button>
            <Button
              variant="ghost"
              onClick={() => {
                resetCreateForm();
                setShowCreate(false);
              }}
            >
              Cancel
            </Button>
          </div>
        </Card>
      )}

      <Card className="space-y-4 p-4 sm:p-5">
        <div className="grid gap-3 md:grid-cols-4">
          <Input
            placeholder="Search name, email, mobile…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
          />
          <Select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="locked">Locked</option>
            {isMain && <option value="deleted">Deleted</option>}
          </Select>
          <Select
            value={role}
            onChange={(e) => {
              setRole(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All roles</option>
            <option value="passenger">Passenger</option>
            <option value="station_manager">Station Admin</option>
            {isMain && <option value="super_admin">Main Admin</option>}
          </Select>
          {isMain && (
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={includeDeleted}
                onChange={(e) => setIncludeDeleted(e.target.checked)}
              />
              Include deleted
            </label>
          )}
        </div>

        {checked.size > 0 && (
          <div className="flex flex-wrap gap-2 rounded-xl border border-card-border bg-muted/40 px-3 py-2">
            <span className="text-xs text-muted-foreground">{checked.size} selected</span>
            <Button
              size="sm"
              variant="outline"
              onClick={() =>
                run(
                  () => api.admin.users.bulkDeactivate([...checked]),
                  "Users deactivated"
                )
              }
            >
              Deactivate
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() =>
                run(
                  () => api.admin.users.bulkLock([...checked], "Bulk lock"),
                  "Users locked"
                )
              }
            >
              Lock
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setChecked(new Set())}>
              Clear
            </Button>
          </div>
        )}
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr className="border-b border-card-border bg-muted/40 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                  <th className="px-4 py-3"> </th>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Station</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Last login</th>
                </tr>
              </thead>
              <tbody>
                {isLoading && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-muted-foreground">
                      Loading users…
                    </td>
                  </tr>
                )}
                {error && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-destructive">
                      {(error as Error).message}
                    </td>
                  </tr>
                )}
                {!isLoading && items.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-muted-foreground">
                      No users match your filters.
                    </td>
                  </tr>
                )}
                {items.map((u) => (
                  <tr
                    key={u.id}
                    className={cn(
                      "cursor-pointer border-b border-card-border hover:bg-muted/30",
                      selected?.id === u.id && "bg-accent/5"
                    )}
                    onClick={() => openUser(u)}
                  >
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={checked.has(u.id)}
                        onChange={() => toggleCheck(u.id)}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium tracking-tight">{u.display_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {u.email || (u.mobile_last4 ? `••••${u.mobile_last4}` : "—")}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-medium">
                        {u.persona_label}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {u.assigned_station?.code || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={u.status} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {u.last_login_at ? formatRelativeTime(u.last_login_at) : "Never"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {pagination && pagination.total_pages > 1 && (
            <div className="flex items-center justify-between border-t border-card-border px-4 py-3 text-sm">
              <span className="text-muted-foreground">
                Page {pagination.page} of {pagination.total_pages} · {pagination.total_count} users
              </span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page >= pagination.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>

        <Card elevated className="space-y-4 p-5">
          {!selected ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              Select a user to view profile and take actions.
            </p>
          ) : (
            <>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  User profile
                </p>
                <h2 className="mt-1 text-display text-xl font-semibold tracking-tight">
                  {selected.display_name}
                </h2>
                <div className="mt-2 flex flex-wrap gap-2">
                  <StatusBadge status={selected.status} />
                  <span className="rounded-md bg-accent/10 px-2 py-0.5 text-xs font-medium text-accent">
                    {selected.persona_label}
                  </span>
                  {selected.assigned_station && (
                    <span className="rounded-md bg-muted px-2 py-0.5 font-mono text-xs">
                      {selected.assigned_station.code} · {selected.assigned_station.name}
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 rounded-xl bg-muted/40 p-3 text-center text-xs">
                <div>
                  <p className="text-muted-foreground">Issues</p>
                  <p className="mt-1 text-lg font-semibold">
                    {selected.activity_summary.issues_created}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Supports</p>
                  <p className="mt-1 text-lg font-semibold">
                    {selected.activity_summary.supports}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Comments</p>
                  <p className="mt-1 text-lg font-semibold">
                    {selected.activity_summary.comments}
                  </p>
                </div>
              </div>

              <div className="space-y-2 text-xs text-muted-foreground">
                <p>Registered · {selected.created_at ? formatRelativeTime(selected.created_at) : "—"}</p>
                <p>Last login · {selected.last_login_at ? formatRelativeTime(selected.last_login_at) : "Never"}</p>
              </div>

              <div className="space-y-3 border-t border-card-border pt-4">
                <div>
                  <Label htmlFor="editName">Display name</Label>
                  <Input
                    id="editName"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="editEmail">Email</Label>
                  <Input
                    id="editEmail"
                    value={editEmail}
                    onChange={(e) => setEditEmail(e.target.value)}
                  />
                </div>
                <Button variant="accent" onClick={() => void saveProfile()}>
                  Save profile
                </Button>
              </div>

              <div className="flex flex-wrap gap-2 border-t border-card-border pt-4">
                {selected.is_active ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      if (confirm("Deactivate this account?"))
                        void run(
                          () => api.admin.users.deactivate(selected.id),
                          "Account deactivated"
                        );
                    }}
                  >
                    Deactivate
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      void run(() => api.admin.users.activate(selected.id), "Account activated")
                    }
                  >
                    Activate
                  </Button>
                )}
                {selected.is_locked ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      void run(() => api.admin.users.unlock(selected.id), "Account unlocked")
                    }
                  >
                    Unlock
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      if (confirm("Lock this account?"))
                        void run(
                          () => api.admin.users.lock(selected.id, "Locked by administrator"),
                          "Account locked"
                        );
                    }}
                  >
                    Lock
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    if (!confirm("Reset password and invalidate sessions?")) return;
                    try {
                      const res = await api.admin.users.resetPassword(selected.id);
                      setTempPassword(res.data.temporary_password);
                      toast.success("Temporary password generated");
                      invalidate();
                    } catch (e) {
                      toast.error(e instanceof Error ? e.message : "Reset failed");
                    }
                  }}
                >
                  Reset password
                </Button>
                {isMain && !selected.deleted_at && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      if (confirm("Soft-delete this user?"))
                        void run(
                          () => api.admin.users.softDelete(selected.id),
                          "User deleted"
                        );
                    }}
                  >
                    Soft delete
                  </Button>
                )}
                {isMain && selected.deleted_at && (
                  <Button
                    size="sm"
                    variant="accent"
                    onClick={() =>
                      void run(() => api.admin.users.restore(selected.id), "User restored")
                    }
                  >
                    Restore
                  </Button>
                )}
              </div>

              {tempPassword && (
                <div className="rounded-xl border border-accent/30 bg-accent/5 px-3 py-2 text-sm">
                  Temporary password:{" "}
                  <span className="font-mono font-semibold">{tempPassword}</span>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Share once securely. User should change it after login.
                  </p>
                </div>
              )}

              {isMain && (
                <div className="space-y-3 border-t border-card-border pt-4">
                  <p className="text-sm font-semibold tracking-tight">Role & station</p>
                  <Select value={roleCode} onChange={(e) => setRoleCode(e.target.value)}>
                    <option value="passenger">Passenger</option>
                    <option value="station_manager">Station Admin</option>
                    <option value="super_admin">Main Admin</option>
                  </Select>
                  {roleCode === "station_manager" && (
                    <Select value={stationId} onChange={(e) => setStationId(e.target.value)}>
                      <option value="">Select station</option>
                      {stations.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.code} · {s.name}
                        </option>
                      ))}
                    </Select>
                  )}
                  <Button
                    size="sm"
                    variant="accent"
                    onClick={() => {
                      if (roleCode === "station_manager" && !stationId) {
                        toast.error("Select a station");
                        return;
                      }
                      if (!confirm("Change this user's role?")) return;
                      void run(
                        () =>
                          api.admin.users.assignRole(selected.id, {
                            role_code: roleCode,
                            station_id: roleCode === "station_manager" ? stationId : null,
                          }),
                        "Role updated"
                      );
                    }}
                  >
                    Apply role
                  </Button>
                  <div>
                    <Label>Assign station (passengers / staff)</Label>
                    <Select
                      value={stationId}
                      onChange={(e) => setStationId(e.target.value)}
                    >
                      <option value="">Unassigned</option>
                      {stations.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.code} · {s.name}
                        </option>
                      ))}
                    </Select>
                    <Button
                      className="mt-2"
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        void run(
                          () =>
                            api.admin.users.assignStation(
                              selected.id,
                              stationId || null
                            ),
                          "Station updated"
                        )
                      }
                    >
                      Save station
                    </Button>
                  </div>
                </div>
              )}

              <div className="border-t border-card-border pt-4">
                <p className="mb-2 text-sm font-semibold tracking-tight">Audit trail</p>
                <div className="max-h-48 space-y-2 overflow-y-auto text-xs">
                  {audits.length === 0 && (
                    <p className="text-muted-foreground">No admin actions yet.</p>
                  )}
                  {audits.map((a) => (
                    <div key={a.id} className="rounded-lg bg-muted/40 px-3 py-2">
                      <p className="font-medium">{a.action}</p>
                      <p className="text-muted-foreground">
                        {a.actor_name || "System"} ·{" "}
                        {a.created_at ? formatRelativeTime(a.created_at) : ""}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
