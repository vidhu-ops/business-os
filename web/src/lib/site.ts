export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") ||
  process.env.PUBLIC_APP_URL?.replace(/\/$/, "") ||
  "https://www.iidatech.biz";
export const SITE_EMAIL = "hello@iidatech.com";
export const SITE_PHONE = "+91 95454 03431";
export const SITE_PHONE_TEL = "tel:+919545403431";
export const SITE_WHATSAPP = "https://wa.me/919545403431";
