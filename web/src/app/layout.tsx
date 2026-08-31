import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Syne } from "next/font/google";
import { ThemeProvider } from "@/components/ThemeProvider";
import { AnalyticsBeacon } from "@/components/AnalyticsBeacon";
import { IidaAssistantHost } from "@/components/iida/IidaAssistantHost";
import { SITE_URL } from "@/lib/site";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
});

const syne = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
  weight: ["600", "700", "800"],
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "IIDATECH | Business OS for Founders & B2B",
    template: "%s | IIDATECH",
  },
  description:
    "IIDATECH helps founders and B2B companies with market research, business planning, business consultation, new business growth, Employee OS execution, and automation — one business OS.",
  keywords: [
    "IIDATECH",
    "market research for founders",
    "business research",
    "founder market research",
    "new business growth",
    "business consultation",
    "business planning software",
    "startup business plan",
    "MSME growth platform",
    "AI business consultation",
    "business OS India",
    "Employee OS",
    "B2B market research platform",
    "company growth audit",
  ],
  openGraph: {
    type: "website",
    siteName: "IIDATECH",
    locale: "en_IN",
    url: SITE_URL,
    images: [{ url: "/marketing/frames/research.png", width: 1200, height: 630, alt: "IIDATECH market research" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "IIDATECH | Business OS for Founders & B2B",
    description: "AI market research, business plans, Mentor, Employee OS, and automation — one workspace.",
    images: ["/marketing/frames/research.png"],
  },
  icons: {
    icon: "/favicon.ico",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${jakarta.variable} ${syne.variable} h-full`} suppressHydrationWarning>
      <body className="min-h-full antialiased">
        <ThemeProvider>
          {children}
          <AnalyticsBeacon />
          <IidaAssistantHost />
        </ThemeProvider>
      </body>
    </html>
  );
}
