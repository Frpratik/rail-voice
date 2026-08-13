/** Product personas — Passenger, Station Admin, Main Admin */

export type Persona = "passenger" | "station_admin" | "main_admin";

const STATION_ADMIN_ROLES = new Set([
  "station_moderator",
  "station_manager",
  "divisional_officer",
]);

const MAIN_ADMIN_ROLES = new Set(["super_admin", "railway_admin"]);

export function resolvePersona(roles: string[] | undefined | null): Persona {
  const set = new Set(roles ?? []);
  if ([...MAIN_ADMIN_ROLES].some((r) => set.has(r))) return "main_admin";
  if ([...STATION_ADMIN_ROLES].some((r) => set.has(r))) return "station_admin";
  return "passenger";
}

export function personaLabel(persona: Persona): string {
  switch (persona) {
    case "main_admin":
      return "Main Admin";
    case "station_admin":
      return "Station Admin";
    default:
      return "Passenger";
  }
}

export function isOpsPersona(persona: Persona): boolean {
  return persona === "station_admin" || persona === "main_admin";
}

export function isOfficial(roles: string[] | undefined | null): boolean {
  const set = new Set(roles ?? []);
  return (
    [...MAIN_ADMIN_ROLES].some((r) => set.has(r)) ||
    [...STATION_ADMIN_ROLES].some((r) => set.has(r))
  );
}

export const DEMO_ACCOUNTS = [
  {
    persona: "passenger" as const,
    label: "Passenger",
    mobile: "+919111111111",
    description: "Raise and track station issues",
    home: "/",
  },
  {
    persona: "station_admin" as const,
    label: "Station Admin",
    mobile: "+919888888888",
    description: "Manage Bandra station queue",
    home: "/admin/dashboard",
  },
  {
    persona: "main_admin" as const,
    label: "Main Admin",
    mobile: "+919999999999",
    description: "Oversee all corridor stations",
    home: "/admin/dashboard",
  },
] as const;
