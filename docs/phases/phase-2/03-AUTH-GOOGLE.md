# Phase 2 — Google Sign-In

## Current state

- `POST /auth/google` accepts mock identity when `GOOGLE_OAUTH_MOCK_MODE=true`  
- Real verify path exists if `GOOGLE_CLIENT_ID` set and mock off (`google.oauth2.id_token`)  
- Frontend “Continue with Google” posts hard-coded mock payload  

## Target state

| Mode | Behavior |
|------|----------|
| Production | Mock **off**; `GOOGLE_CLIENT_ID` required if Google login enabled |
| Staging | Mock optional; or real client ID against Google test users |
| Local | Mock or real |

Feature flag:

```
GOOGLE_AUTH_ENABLED=true|false
GOOGLE_CLIENT_ID=....apps.googleusercontent.com
GOOGLE_OAUTH_MOCK_MODE=false   # must be false in production
```

If `GOOGLE_AUTH_ENABLED=false`, endpoint returns 404/501 and UI hides button.

## Frontend

1. Load Google Identity Services when `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set  
2. On credential → `POST /auth/google` with `{ id_token }` only (no client-supplied `google_id` trusted in non-mock)  
3. If no client ID → hide Google button (or show disabled “Configure Google”)  

## Backend rules (non-mock)

1. Verify `id_token` with Google; audience = `GOOGLE_CLIENT_ID`  
2. Take `sub`, `email`, `name`, `picture` **only from verified claims**  
3. Ignore client `google_id` / `email` / `name` overrides when mock is off  
4. Upsert user (existing `upsert_google_user`)  
5. Issue tokens + audit `auth.google.login`  

## Mock rules

- Allowed only when `GOOGLE_OAUTH_MOCK_MODE=true` **and** not production  
- May accept `id_token=mock-token` + optional fields for CI  

## Acceptance

- Tampered / expired token → 401  
- Correct token → 200 + user with `google_id` set  
- Production boot with mock on → hard fail (existing + ensure Google path covered)
