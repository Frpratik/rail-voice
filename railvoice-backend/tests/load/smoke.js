# RailVoice load test skeleton (k6)
# Install: https://k6.io/docs/get-started/installation/
# Run: k6 run smoke.js

import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 20,
  duration: "30s",
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
  },
};

const BASE = __ENV.API_URL || "http://localhost:8000";

export default function () {
  const health = http.get(`${BASE}/health`);
  check(health, { "health ok": (r) => r.status === 200 });

  const stations = http.get(`${BASE}/api/v1/stations`);
  check(stations, { "stations ok": (r) => r.status === 200 });

  sleep(1);
}
