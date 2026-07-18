# 7. Frontend Application

**Package:** `railvoice-web`  
**Stack:** Next.js App Router, React 19, TypeScript, Tailwind CSS 4, TanStack Query, Zustand, Framer Motion  

**Live:** https://rail-voice.vercel.app

## 7.1 Routes

| Route | Purpose |
|-------|---------|
| `/` | Public issue feed |
| `/report` | Multi-step report + duplicate sheet + photos |
| `/issues/[id]` | Detail, support, photos, comments, timeline |
| `/stations/[code]` | Station-scoped issues |
| `/nearby` | Nearby / station discovery UX |
| `/login` | OTP + Google (mock) |
| `/profile` | Account, logout, ops console entry |
| `/notifications` | Notification list / mark read |
| `/admin/dashboard` | Ops KPIs |
| `/admin/issues` | Queue, status, assign, escalate |
| `/admin/reports` | PDF / Excel download |
| `/admin/analytics` | Analytics placeholder / AI summary hook |

Layouts: root shell (header, bottom nav); admin layout + sidebar.

## 7.2 State & data

| Concern | Implementation |
|---------|----------------|
| Auth | Zustand persist `railvoice-auth` + `localStorage` tokens |
| Server data | TanStack Query |
| API | `src/lib/api.ts` → `apiFetch` |
| Types | `src/lib/types.ts` |

### API base URL

```
development → http://localhost:8000/api/v1 (default)
production  → /api/v1 (same-origin; rewritten to Render)
```

Rewrites in `next.config.ts`:

- `/api/:path*` → `API_PROXY_TARGET` (default `https://rail-voice.onrender.com`)  
- `/media/:path*` → same  

## 7.3 Design system (Signal Inkwell)

Documented in `src/app/globals.css`:

- Accent orange (`#e8481a` / dark `#ff6a3d`)  
- Fonts: **Sora** (UI/display), **JetBrains Mono** (meta)  
- Cards: glass / surface utilities; mesh background; reduced-motion respect  
- Components under `src/components/ui` and feature folders  

## 7.4 Key UX flows

1. **Report** — Location → Details (+ photos) → Review → duplicate check → create/support  
2. **Issue detail** — Support, gallery upload, comment composer (signed-in), timeline  
3. **Login** — OTP steps or Continue with Google (dev mock)  
4. **Admin** — Select issue → remarks → status / assign / escalate  

## 7.5 Environment variables (web)

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | Browser API base (`/api/v1` or absolute) |
| `API_PROXY_TARGET` | Rewrite destination (Render URL) |

Example: `railvoice-web/.env.local.example`.

## 7.6 Build & run

```bash
cd railvoice-web
npm ci
npm run dev      # localhost:3000
npm run build
npm start
```

Docker: `railvoice-web/Dockerfile` (standalone output).
