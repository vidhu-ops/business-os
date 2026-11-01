# iidatech.com → Render (`business-os-2`)

Production site: **https://iidatech.com**. Do **not** attach **iidatech.biz** to this Render service.

Registrar in use: **name.com** (Manage DNS). Render custom domain modal should show **Verified** + certificate once these records exist.

## What Render expects (match the dashboard modal)

| Hostname | Record type at registrar | Target |
|----------|------------------------|--------|
| `www` | **CNAME** | `business-os-2.onrender.com` |
| `@` (apex) | **ANAME / ALIAS** (preferred at name.com) or **CNAME** if supported | `business-os-2.onrender.com` |

If your registrar only allows an **A** record on apex, Render may list **`216.24.57.1`** — use the value shown in your Render modal.

## name.com — add website records (keep email records)

Your DNS panel may already show **Resend** records (`resend._domainkey`, MX to `forge.rmta.net`, etc.). **Do not delete those** — they are for **admin@iidatech.com** / transactional email.

**Add** (in addition to Resend):

1. **Manage DNS** → **Add Record**
2. **CNAME** — Host: `www` → Answer: `business-os-2.onrender.com` → TTL 300 (or default)
3. **ANAME** or **ALIAS** — Host: `@` or leave apex → Answer: `business-os-2.onrender.com`  
   - If name.com only offers **A** for apex, use Render’s apex **A** target (`216.24.57.1`) from the modal.

Do **not** add a conflicting **A** record on `@` pointing somewhere else.

After saving, wait 15–60 minutes, then check:

```bash
dig +short CNAME www.iidatech.com
dig +short A iidatech.com
curl -I https://iidatech.com/api/health
```

Until apex/www resolve, the app still works at **https://business-os-2.onrender.com**.

## Render dashboard

1. Service **business-os-2** → **Settings** → **Custom Domains** → **`iidatech.com`** (+ **`www.iidatech.com`** if used).
2. Remove **iidatech.biz** from this service if it is still listed.
3. **Environment** (must match `render.yaml` after deploy):

| Variable | Value |
|----------|--------|
| `PUBLIC_APP_URL` | `https://iidatech.com` |
| `NEXT_PUBLIC_SITE_URL` | `https://iidatech.com` |
| `ADMIN_EMAIL` | `admin@iidatech.com` |
| `OAUTH_REDIRECT_URI` | `https://iidatech.com/api/v1/oauth/callback` |
| `JWT_SECRET`, API keys | Set in dashboard (secrets you updated) |

Redeploy after env changes.

## GoDaddy

If you move DNS to GoDaddy later, use the same **www** CNAME and apex ANAME/forwarding pattern as in Render’s modal.
