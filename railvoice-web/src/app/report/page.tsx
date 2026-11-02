"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  AlertTriangle,
  ArrowRight,
  Camera,
  Phone,
  ThumbsUp,
  FileText,
  Image as ImageIcon,
  LocateFixed,
  MapPin,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Label, Select, Textarea } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { useT } from "@/lib/i18n";
import { compressImage, currentPosition } from "@/lib/image";

const CATEGORIES = [
  { id: "platform_cleanliness", label: "Cleanliness & Waste" },
  { id: "station_infrastructure", label: "Station Infrastructure" },
  { id: "lifts_escalators", label: "Lifts & Escalators" },
  { id: "accessibility", label: "Wheelchair & Access" },
  { id: "safety_security", label: "Safety & Hazard" },
  { id: "womens_safety", label: "Women's Safety" },
  { id: "train_coach", label: "Train & Coach" },
  { id: "overcrowding", label: "Overcrowding" },
  { id: "facilities", label: "Ticket Counters & Fans" },
];

const AREAS = [
  ...Array.from({ length: 10 }, (_, i) => `PF ${i + 1}`),
  "FOB",
  "Entrance",
  "Ticket",
  "Toilet",
  "Train",
];

const DRAFT_KEY = "railvoice-report-draft";

function useDebounced<T>(value: T, ms = 500): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}

export default function ReportPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const t = useT();
  const user = useAuthStore((s) => s.user);
  const anonymousSessionId = useAuthStore((s) => s.anonymousSessionId);
  const setAnonymous = useAuthStore((s) => s.setAnonymous);
  const [locating, setLocating] = useState(false);
  const [differentProblem, setDifferentProblem] = useState(false);
  const [stationId, setStationId] = useState("");
  const [categoryCode, setCategoryCode] = useState("platform_cleanliness");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isEmergency, setIsEmergency] = useState(false);
  const [trainNumber, setTrainNumber] = useState("");
  const [coachNumber, setCoachNumber] = useState("");
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const { data: stationsData, isLoading: stationsLoading } = useQuery({
    queryKey: ["stations"],
    queryFn: () => api.stations.list({ zone_code: "WR" }),
  });
  const stations = stationsData?.data ?? [];

  // Bring back an unfinished report: signal on a platform comes and goes.
  useEffect(() => {
    let saved: { stationId?: string; categoryCode?: string; title?: string; description?: string } | null =
      null;
    try {
      saved = JSON.parse(localStorage.getItem(DRAFT_KEY) ?? "null");
    } catch {
      return;
    }
    if (!saved?.description) return;
    const draft = saved;
    queueMicrotask(() => {
      setStationId(draft.stationId ?? "");
      setCategoryCode(draft.categoryCode ?? "platform_cleanliness");
      setTitle(draft.title ?? "");
      setDescription(draft.description ?? "");
      toast.info(t("report.draft"));
    });
    // Only on first load.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!description.trim()) return;
    try {
      localStorage.setItem(
        DRAFT_KEY,
        JSON.stringify({ stationId, categoryCode, title, description })
      );
    } catch {
      /* Private mode: nothing to restore later, and that's fine. */
    }
  }, [stationId, categoryCode, title, description]);

  const detectStation = async () => {
    setLocating(true);
    const position = await currentPosition();
    if (!position) {
      setLocating(false);
      toast.error("Couldn't get your location. Check your browser's location permission.");
      return;
    }
    try {
      const res = await api.stations.nearest(position.coords.latitude, position.coords.longitude);
      const nearest = res.data.items[0];
      if (nearest) {
        setStationId(nearest.id);
        toast.success(`${nearest.name} (${nearest.distance_km} km away)`);
      }
    } catch {
      toast.error("Couldn't find the nearest station.");
    } finally {
      setLocating(false);
    }
  };

  const reportAnonymously = async () => {
    try {
      const res = await api.auth.anonymous();
      setAnonymous(res.data.anonymous_session_id);
    } catch {
      toast.error("Couldn't start. Please try again.");
    }
  };

  const debouncedText = useDebounced(`${title} ${description}`.trim());
  const { data: similarData } = useQuery({
    queryKey: ["similar", stationId, categoryCode, debouncedText],
    queryFn: () =>
      api.issues.similar({
        station_id: stationId,
        category_code: categoryCode,
        q: debouncedText,
      }),
    enabled: !!stationId && debouncedText.length >= 10,
  });
  const similar = similarData?.data.items ?? [];

  const supportMutation = useMutation({
    mutationFn: (id: string) => api.issues.support(id),
    onSuccess: (_, id) => {
      toast.success("Thanks, you've backed that report instead.");
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      router.push(`/issues/${id}`);
    },
    onError: (e: Error, id) => {
      if (/already/i.test(e.message)) {
        // They already back it (e.g. it's their own report): just open it.
        toast.info("You've already backed this report.");
        router.push(`/issues/${id}`);
        return;
      }
      toast.error(e.message);
    },
  });

  const showEmergencyNotice = isEmergency || categoryCode === "safety_security";

  const handlePhotoSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = await Promise.all(Array.from(e.target.files).map((f) => compressImage(f)));
      setPhotoFiles((prev) => [...prev, ...selected].slice(0, 3));
    }
  };

  const removePhoto = (index: number) => {
    setPhotoFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stationId) {
      toast.error("Please select the railway station");
      return;
    }
    if (similar.length > 0 && !differentProblem) {
      toast.error("Please check the similar reports below first");
      return;
    }
    if (description.trim().length < 10) {
      toast.error("Please provide at least 10 characters in the problem description");
      return;
    }

    if (!user && !anonymousSessionId) {
      toast.error("Sign in, or choose to report without signing in");
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.issues.create({
        station_id: stationId,
        category_code: categoryCode,
        title: title.trim() || undefined,
        description: description.trim(),
        is_emergency: isEmergency,
        train_number: trainNumber.trim() || undefined,
        coach_number: coachNumber.trim() || undefined,
      });

      const issueId = res.data.issue.id;

      // Upload photos if attached
      if (photoFiles.length > 0) {
        for (const file of photoFiles) {
          try {
            await api.issues.uploadPhoto(issueId, file);
          } catch {
            // Non-blocking if photo upload fails
          }
        }
      }

      try {
        localStorage.removeItem(DRAFT_KEY);
      } catch {
        /* Nothing was saved in private mode. */
      }
      toast.success("Problem reported. Station staff have been notified.");
      router.push(`/issues/${issueId}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to submit grievance");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <PageHeader
        eyebrow="Passenger report"
        title={t("report.title")}
        description="Your report goes straight to the staff at that station."
      />

      {!user && !anonymousSessionId && (
        <Card className="flex flex-wrap items-center justify-between gap-3 border-2 border-accent p-4">
          <p className="text-sm">
            Sign in to track your report and get updates, or send it anonymously.
          </p>
          <div className="flex flex-wrap gap-2">
            <Link href="/login?next=/report">
              <Button size="sm" variant="accent">
                {t("nav.signIn")}
              </Button>
            </Link>
            <Button size="sm" variant="outline" onClick={() => void reportAnonymously()}>
              {t("report.anon")}
            </Button>
          </div>
        </Card>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Station Selector */}
        <Card className="p-4 sm:p-6 space-y-4">
          <div className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-accent" />
            <h2 className="text-base font-semibold">1. Location & Station</h2>
          </div>

          <div className="space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <Label htmlFor="station" className="mb-0">
                {t("report.station")} *
              </Label>
              <button
                type="button"
                onClick={() => void detectStation()}
                disabled={locating}
                className="label-caps inline-flex items-center gap-1.5 text-xs text-accent hover:underline disabled:opacity-50"
              >
                <LocateFixed className="h-3.5 w-3.5" />
                {t("report.useLocation")}
              </button>
            </div>
            <select
              id="station"
              value={stationId}
              onChange={(e) => setStationId(e.target.value)}
              disabled={stationsLoading}
              className="w-full h-11 rounded-xl border border-card-border bg-background px-3.5 text-sm font-medium text-foreground transition-colors focus:border-accent focus:outline-none"
              required
            >
              <option value="">Select a Station (Churchgate → Virar)</option>
              {stations.map((st) => (
                <option key={st.id} value={st.id}>
                  {st.name} ({st.code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 gap-3 pt-2 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="train">{t("report.train")}</Label>
              <Input
                id="train"
                placeholder="e.g. 90123 / Fast Local"
                value={trainNumber}
                onChange={(e) => setTrainNumber(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="coach">{t("report.platform")}</Label>
              <Select id="coach" value={coachNumber} onChange={(e) => setCoachNumber(e.target.value)}>
                <option value="">—</option>
                {AREAS.map((area) => (
                  <option key={area} value={area}>
                    {area}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        </Card>

        {/* Problem Details */}
        <Card className="p-4 sm:p-6 space-y-4">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-accent" />
            <h2 className="text-base font-semibold">2. Problem Details</h2>
          </div>

          <div className="space-y-2">
            <Label>{t("report.category")}</Label>
            <div className="grid grid-cols-1 min-[360px]:grid-cols-2 sm:grid-cols-3 gap-2">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setCategoryCode(cat.id)}
                  className={`rounded-xl border p-2.5 text-left text-xs font-medium transition-all ${
                    categoryCode === cat.id
                      ? "border-accent bg-accent/10 text-foreground font-semibold"
                      : "border-card-border bg-background text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="title">{t("report.summary")}</Label>
            <Input
              id="title"
              placeholder="e.g. Escalator not working at Platform 1 North Exit"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={150}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="desc">{t("report.details")} *</Label>
            <Textarea
              id="desc"
              rows={4}
              placeholder="Describe the exact location, safety hazard, or maintenance needed so duty staff can act immediately..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
            />
          </div>

          {/* Emergency Toggle */}
          <div className="flex items-start gap-3 rounded-2xl border border-destructive/30 bg-destructive/5 p-4">
            <input
              type="checkbox"
              id="emergency"
              checked={isEmergency}
              onChange={(e) => setIsEmergency(e.target.checked)}
              className="mt-1 h-4 w-4 rounded border-destructive/40 text-destructive focus:ring-destructive"
            />
            <label htmlFor="emergency" className="cursor-pointer text-xs leading-relaxed text-foreground">
              <span className="font-bold text-destructive block flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" />
                {t("report.urgent")}
              </span>
              Check this box if this problem poses an immediate danger to passenger safety (e.g. live wire, track obstruction, broken paver tile near train door).
            </label>
          </div>
        </Card>

        {showEmergencyNotice && (
          <div
            role="alert"
            className="flex items-start gap-3 border-2 border-destructive bg-destructive/10 p-4 text-sm"
          >
            <Phone className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
            <p className="leading-relaxed">
              <strong className="text-display block text-lg text-destructive">
                {t("report.danger")}
              </strong>
              Railway helpline <strong>139</strong> · RPF security <strong>182</strong> · Emergency{" "}
              <strong>112</strong>. This form is read by station staff during working hours and is
              not an emergency service.
            </p>
          </div>
        )}

        {similar.length > 0 && (
          <Card className="space-y-4 border-2 border-accent p-4 sm:p-6">
            <div>
              <h2 className="text-display text-2xl">Already reported?</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Other passengers have reported something similar at this station. Backing an
                existing report moves it up the queue faster than a duplicate.
              </p>
            </div>
            <ul className="space-y-3">
              {similar.map((item) => (
                <li key={item.id} className="border border-card-border bg-background p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <Link
                      href={`/issues/${item.id}`}
                      target="_blank"
                      className="text-display text-lg hover:underline"
                    >
                      {item.title ?? item.description.slice(0, 80)}
                    </Link>
                    <StatusBadge status={item.status} />
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                    {item.description}
                  </p>
                  <div className="mt-3 flex items-center justify-between gap-3">
                    <span className="font-board text-xs text-muted-foreground">
                      {item.issue_number} · {item.support_count} backing
                    </span>
                    <Button
                      type="button"
                      size="sm"
                      variant="accent"
                      className="gap-1.5"
                      disabled={supportMutation.isPending}
                      onClick={() => supportMutation.mutate(item.id)}
                    >
                      <ThumbsUp className="h-3.5 w-3.5" />
                      Back this instead
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
            <label className="flex cursor-pointer items-start gap-3 text-sm">
              <input
                type="checkbox"
                checked={differentProblem}
                onChange={(e) => setDifferentProblem(e.target.checked)}
                className="mt-1 h-4 w-4"
              />
              <span>None of these is my problem. I still want to submit a new report.</span>
            </label>
          </Card>
        )}

        {/* Photo Upload */}
        <Card className="p-4 sm:p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Camera className="h-5 w-5 text-accent" />
            <h2 className="text-base font-semibold">{t("report.photos")}</h2>
          </div>

          <div className="flex flex-wrap gap-3">
            {photoFiles.map((file, i) => (
              <div
                key={i}
                className="relative h-24 w-24 rounded-2xl border border-card-border bg-muted/40 overflow-hidden flex items-center justify-center"
              >
                <img
                  src={URL.createObjectURL(file)}
                  alt="preview"
                  className="h-full w-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => removePhoto(i)}
                  className="absolute right-1.5 top-1.5 rounded-full bg-black/70 p-1 text-white hover:bg-black"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}

            {photoFiles.length < 3 && (
              <label className="flex h-24 w-24 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-card-border bg-background transition-colors hover:border-accent hover:bg-accent/5">
                <ImageIcon className="h-5 w-5 text-muted-foreground" />
                <span className="mt-1 text-[10px] font-medium text-muted-foreground">
                  {t("report.addPhoto")}
                </span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => void handlePhotoSelect(e)}
                  className="hidden"
                />
              </label>
            )}
          </div>
        </Card>

        <Button
          type="submit"
          variant="accent"
          size="lg"
          disabled={submitting}
          className="w-full gap-2 text-base font-semibold"
        >
          {submitting ? t("report.submitting") : t("report.submit")}
          <ArrowRight className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}
