"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  AlertTriangle,
  ArrowRight,
  Camera,
  Check,
  FileText,
  Image as ImageIcon,
  MapPin,
  Train,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Label, Textarea } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/empty-state";
import { api } from "@/lib/api";

const CATEGORIES = [
  { id: "platform_cleanliness", label: "Cleanliness & Waste" },
  { id: "station_infrastructure", label: "Station Infrastructure" },
  { id: "lifts_escalators", label: "Lifts & Escalators" },
  { id: "safety_security", label: "Safety & Hazard" },
  { id: "train_coach", label: "Train & Coach" },
  { id: "facilities", label: "Ticket Counters & Fans" },
];

export default function ReportPage() {
  const router = useRouter();
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

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files);
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
    if (description.trim().length < 10) {
      toast.error("Please provide at least 10 characters in the problem description");
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.issues.create({
        station_id: stationId,
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

      toast.success("Problem reported successfully! Station Admin notified.");
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
        eyebrow="Citizen Reporting"
        title="Report a Problem"
        description="Submit a station or train grievance directly to Western Railway station managers."
      />

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Station Selector */}
        <Card className="p-6 space-y-4">
          <div className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-accent" />
            <h2 className="text-base font-semibold">1. Location & Station</h2>
          </div>

          <div className="space-y-2">
            <Label htmlFor="station">Station on Western Railway *</Label>
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

          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="space-y-1.5">
              <Label htmlFor="train">Train / Local (Optional)</Label>
              <Input
                id="train"
                placeholder="e.g. 90123 / Fast Local"
                value={trainNumber}
                onChange={(e) => setTrainNumber(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="coach">Coach / Platform (Optional)</Label>
              <Input
                id="coach"
                placeholder="e.g. Platform 2 / FC-2"
                value={coachNumber}
                onChange={(e) => setCoachNumber(e.target.value)}
              />
            </div>
          </div>
        </Card>

        {/* Problem Details */}
        <Card className="p-6 space-y-4">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-accent" />
            <h2 className="text-base font-semibold">2. Problem Details</h2>
          </div>

          <div className="space-y-2">
            <Label>Category</Label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
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
            <Label htmlFor="title">Summary / Short Title</Label>
            <Input
              id="title"
              placeholder="e.g. Escalator not working at Platform 1 North Exit"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={150}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="desc">Detailed Description *</Label>
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
                Urgent Safety Hazard?
              </span>
              Check this box if this problem poses an immediate danger to passenger safety (e.g. live wire, track obstruction, broken paver tile near train door).
            </label>
          </div>
        </Card>

        {/* Photo Upload */}
        <Card className="p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Camera className="h-5 w-5 text-accent" />
            <h2 className="text-base font-semibold">3. Evidence Photo (Optional)</h2>
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
                  Add Photo
                </span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handlePhotoSelect}
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
          className="w-full gap-2 text-base font-semibold shadow-lg shadow-accent/20"
        >
          {submitting ? "Submitting Grievance..." : "Submit Problem Report"}
          <ArrowRight className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}
