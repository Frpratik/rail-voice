"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { Train, MapPin, Ticket, ShieldCheck, Clock, CheckCircle2, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface PNRTelemetryWidgetProps {
  // If true, widget is in "lookup" mode for creating an issue
  isEditable?: boolean;
  
  // Initial or fixed values
  initialPnr?: string | null;
  trainNumber?: string | null;
  coachNumber?: string | null;
  berthNumber?: string | null;
  upcomingStationCode?: string | null;

  // Callback when PNR is successfully fetched in editable mode
  onPnrFound?: (data: {
    pnr_number: string;
    train_number: string;
    coach_number: string;
    berth_number: string;
    upcoming_station_code: string;
  }) => void;
}

export function PNRTelemetryWidget({
  isEditable = false,
  initialPnr,
  trainNumber,
  coachNumber,
  berthNumber,
  upcomingStationCode,
  onPnrFound,
}: PNRTelemetryWidgetProps) {
  const [pnrInput, setPnrInput] = useState(initialPnr || "");
  const [activePnr, setActivePnr] = useState(initialPnr || "");
  const [activeTrain, setActiveTrain] = useState(trainNumber || "");

  // Fetch live train status if we have a train number
  const { data: trainStatusData, isLoading: isLoadingTrain } = useQuery({
    queryKey: ["train-status", activeTrain],
    queryFn: () => api.telemetry.trainStatus(activeTrain!),
    enabled: !!activeTrain,
    refetchInterval: 60000, // refresh every minute
  });

  const pnrMutation = useMutation({
    mutationFn: (pnr: string) => api.telemetry.pnrLookup(pnr),
    onSuccess: (res) => {
      const data = res.data;
      setActivePnr(data.pnr_number);
      setActiveTrain(data.train_number);
      
      const passenger = data.passengers?.[0];
      const coach = passenger?.coach || "B4"; // Fallback to B4 if mock data doesn't have it
      const berth = passenger?.berth || "22";
      const upcoming = "ST"; // Mock upcoming station
      
      toast.success(`PNR Found: Train ${data.train_number} - ${data.train_name}`);
      
      if (onPnrFound) {
        onPnrFound({
          pnr_number: data.pnr_number,
          train_number: data.train_number,
          coach_number: coach,
          berth_number: berth,
          upcoming_station_code: upcoming,
        });
      }
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "PNR Lookup failed");
    },
  });

  const handleLookup = () => {
    if (pnrInput.trim().length !== 10) {
      toast.error("Please enter a valid 10-digit PNR number");
      return;
    }
    pnrMutation.mutate(pnrInput.trim());
  };

  const status = trainStatusData?.data;

  return (
    <Card className="overflow-hidden border-accent/20 shadow-md">
      {/* Header */}
      <div className="bg-gradient-to-r from-accent/10 to-accent/5 p-4 border-b border-accent/10 flex items-center justify-between">
        <div className="flex items-center gap-2 text-accent font-bold">
          <Train className="h-5 w-5" />
          <span>Live Train Telemetry</span>
        </div>
        {(activePnr || activeTrain) && (
          <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-green-600 bg-green-500/10 px-2 py-1 rounded-full">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            Live Bound
          </div>
        )}
      </div>

      <div className="p-4 space-y-5">
        {/* Lookup Field (only in editable mode if not yet found) */}
        {isEditable && (
          <div className="flex gap-2">
            <div className="flex-1">
              <Label htmlFor="pnr" className="sr-only">PNR Number</Label>
              <div className="relative">
                <Ticket className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="pnr"
                  placeholder="Enter 10-digit PNR"
                  className="pl-9 bg-muted/50 focus:bg-background transition-colors"
                  value={pnrInput}
                  onChange={(e) => setPnrInput(e.target.value.replace(/\D/g, "").slice(0, 10))}
                  disabled={pnrMutation.isPending}
                />
              </div>
            </div>
            <Button
              variant={activePnr ? "outline" : "accent"}
              onClick={handleLookup}
              disabled={pnrMutation.isPending || pnrInput.length !== 10}
              className="shrink-0"
            >
              {pnrMutation.isPending ? (
                <span className="animate-pulse">Locating...</span>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  {activePnr ? "Refresh" : "Verify PNR"}
                </>
              )}
            </Button>
          </div>
        )}

        {/* Train Details Grid */}
        {(activeTrain || trainNumber) && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-xl bg-muted/50 p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Train Number
              </p>
              <p className="font-bold text-foreground truncate">
                {activeTrain || trainNumber}
              </p>
            </div>
            
            <div className="rounded-xl bg-muted/50 p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Coach / Berth
              </p>
              <p className="font-bold text-foreground truncate">
                {(coachNumber || berthNumber) ? `${coachNumber || "-"} / ${berthNumber || "-"}` : "-"}
              </p>
            </div>

            <div className="col-span-2 rounded-xl bg-muted/50 p-3 flex flex-col justify-center border border-accent/10 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-2 opacity-10">
                <ShieldCheck className="h-10 w-10 text-accent" />
              </div>
              <div className="flex items-center gap-2 relative z-10">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <p className="text-sm font-bold text-foreground">OBHS Assigned</p>
              </div>
              <p className="text-[10px] text-muted-foreground mt-0.5 relative z-10">
                On-Board Housekeeping Staff notified
              </p>
            </div>
          </div>
        )}

        {/* Live Status Panel */}
        {(activeTrain || trainNumber) && (
          <div className="rounded-xl bg-accent/5 p-4 border border-accent/10">
            {isLoadingTrain ? (
              <div className="animate-pulse flex items-center justify-center h-12 text-sm text-muted-foreground font-medium">
                Syncing with NTES...
              </div>
            ) : status ? (
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-4">
                  <div className="flex-1 flex flex-col items-center">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                      Current Station
                    </p>
                    <p className="font-bold truncate text-foreground">{status.current_station}</p>
                  </div>
                  <div className="flex-1 flex items-center justify-center relative">
                    <div className="absolute w-full h-[2px] bg-accent/20 rounded-full" />
                    <Train className="h-5 w-5 text-accent relative z-10 bg-[#FAF9F6] dark:bg-background px-0.5" />
                  </div>
                  <div className="flex-1 flex flex-col items-center">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                      Upcoming Halt
                    </p>
                    <p className="font-bold truncate text-foreground">{status.upcoming_station || upcomingStationCode}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs font-medium pt-3 border-t border-accent/10">
                  <div className="flex items-center gap-1.5 text-orange-600 dark:text-orange-400">
                    <Clock className="h-3.5 w-3.5" />
                    <span>{status.delay_minutes > 0 ? `Delayed by ${status.delay_minutes} mins` : 'On Time'}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-muted-foreground">
                    <MapPin className="h-3.5 w-3.5" />
                    <span>GPS Active</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground text-center py-2">
                Live status currently unavailable
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
