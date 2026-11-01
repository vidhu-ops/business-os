/** Public site URL — production custom domain iidatech.com (see docs/DNS_IIDATECH_COM.md). */
export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL ||
  process.env.PUBLIC_APP_URL ||
  process.env.RENDER_EXTERNAL_URL ||
  "https://iidatech.com"
).replace(/\/$/, "");

/** Primary contact and admin sign-in email (must match Render `ADMIN_EMAIL`). */
export const SITE_ADMIN_EMAIL = "admin@iidatech.com";
export const SITE_EMAIL = SITE_ADMIN_EMAIL;
export const SITE_PHONE = "+91 95454 03431";
export const SITE_PHONE_TEL = "tel:+919545403431";
export const SITE_WHATSAPP = "https://wa.me/919545403431";
