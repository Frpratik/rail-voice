from __future__ import annotations

from typing import Any


class TrainTelemetryService:
    @staticmethod
    def lookup_pnr(pnr_number: str) -> dict[str, Any]:
        """Mock/Live Indian Railways PNR lookup service."""
        clean_pnr = pnr_number.strip()
        if len(clean_pnr) != 10 or not clean_pnr.isdigit():
            raise ValueError("PNR number must be exactly 10 digits")

        # Deterministic mock generation based on PNR digits
        seed = int(clean_pnr[-4:])
        trains = [
            ("12951", "Mumbai Rajdhani Express", "B4", "22", "ST", "Surat", 24),
            ("12953", "August Kranti Rajdhani", "A2", "14", "BRC", "Vadodara", 45),
            ("19015", "Saurashtra Express", "S3", "48", "VAPI", "Vapi", 12),
            ("12925", "Paschim Express", "B1", "09", "PLG", "Palghar", 18),
        ]
        train_info = trains[seed % len(trains)]

        return {
            "pnr_number": clean_pnr,
            "train_number": train_info[0],
            "train_name": train_info[1],
            "coach_number": train_info[2],
            "berth_number": train_info[3],
            "passenger_class": "3A",
            "boarding_station": "MMCT",
            "destination_station": "NDLS",
            "upcoming_station_code": train_info[4],
            "upcoming_station_name": train_info[5],
            "eta_minutes": train_info[6],
            "current_latitude": 19.0760 + (seed % 100) * 0.005,
            "current_longitude": 72.8777 + (seed % 100) * 0.005,
            "speed_kmh": 92.5,
            "obhs_assigned": True,
            "obhs_vendor_name": "Western Rail Clean Tech Pvt Ltd",
            "obhs_supervisor_mobile": "+91-9876543210",
        }

    @staticmethod
    def get_live_train_status(train_number: str) -> dict[str, Any]:
        """Fetch live train running status & GPS coordinates."""
        clean_train = train_number.strip()
        if len(clean_train) != 5 or not clean_train.isdigit():
            raise ValueError("Train number must be exactly 5 digits")

        return {
            "train_number": clean_train,
            "train_name": "Mumbai Express",
            "is_running_live": True,
            "current_latitude": 19.1197,
            "current_longitude": 72.8464,
            "speed_kmh": 84.0,
            "delay_minutes": 5,
            "last_passed_station": "ADH",
            "upcoming_station_code": "BVI",
            "upcoming_station_name": "Borivali",
            "eta_minutes": 14,
        }


telemetry_service = TrainTelemetryService()
