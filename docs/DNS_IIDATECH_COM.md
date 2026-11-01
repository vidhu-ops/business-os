# iidatech.com → Render (`business-os-2`)

Production uses **https://iidatech.com** only. Do **not** point **iidatech.biz** at this service (reserved for other use).

## Step 1 — Render (do this first)

1. Open [Render Dashboard](https://dashboard.render.com/) → service **business-os-2**.
2. **Settings** → **Custom Domains** → **Add custom domain**.
3. Enter **`iidatech.com`** (and **`www.iidatech.com`** if you want both).
4. Render shows DNS instructions and a target hostname (usually **`business-os-2.onrender.com`**).
5. Wait until Render shows **Verified** and TLS certificate **Issued** (can take a few minutes after DNS propagates).

Remove **iidatech.biz** from this service’s custom domains if it is still listed.

## Step 2 — GoDaddy DNS

In GoDaddy → **My Products** → **iidatech.com** → **DNS** → **Manage DNS**:

| Type | Name | Value | TTL |
|------|------|--------|-----|
| **CNAME** | `www` | `business-os-2.onrender.com` | 1 hour (or default) |

**Root domain (`@` / apex):** GoDaddy does not allow a plain CNAME on `@` in all plans. Use one of:

- **Recommended:** GoDaddy **Domain Forwarding** — forward `http://iidatech.com` and `https://iidatech.com` to `https://www.iidatech.com` (301, forward only).
- **Or:** If GoDaddy offers **CNAME flattening / ANAME** for `@`, point `@` to `business-os-2.onrender.com` (same target Render shows).
- **Or:** Use Render’s listed **A records** for apex if Render displays IP addresses when you add the apex domain.

Delete old **A** / **CNAME** records that pointed **iidatech.com** or **iidatech.biz** elsewhere (wrong hosts break TLS).

Propagation often takes **15 minutes–48 hours**. Test:

```bash
curl -I https://iidatech.com/api/health
curl -I https://www.iidatech.com/api/health
```

## Step 3 — Render environment

Set (or sync from `render.yaml`):

| Variable | Value |
|----------|--------|
| `PUBLIC_APP_URL` | `https://iidatech.com` |
| `NEXT_PUBLIC_SITE_URL` | `https://iidatech.com` |
| `OAUTH_REDIRECT_URI` | `https://iidatech.com/api/v1/oauth/callback` |
| `CANVA_REDIRECT_URI` | `https://iidatech.com/api/v1/oauth/callback` |

Redeploy after changing env vars.

## name.com

If DNS is at name.com instead of GoDaddy, use the same targets:

```
ANAME/ALIAS  @    -> business-os-2.onrender.com
CNAME        www  -> business-os-2.onrender.com
```
