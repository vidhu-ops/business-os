import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Syne } from "next/font/google";
import { ThemeProvider } from "@/components/ThemeProvider";
import { IidaAssistantHost } from "@/components/iida/IidaAssistantHost";
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
  metadataBase: new URL("https://iidatech.biz"),
  title: {
    default: "IIDATECH | Business OS for Founders & B2B Companies",
    template: "%s | IIDATECH",
  },
  description:
    "IIDATECH helps founders and established B2B companies research markets, build business plans, mentor decisions, execute with Employee OS, and automate workflows — in one business ecosystem.",
  keywords: [
    "IIDATECH",
    "founder business OS",
    "B2B market research platform",
    "AI business plan",
    "Employee OS",
    "MSME automation India",
  ],
  openGraph: {
    type: "website",
    siteName: "IIDATECH",
    locale: "en_IN",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${jakarta.variable} ${syne.variable} h-full`} suppressHydrationWarning>
      <body className="min-h-full antialiased">
        <ThemeProvider>
          {children}
          <IidaAssistantHost />
        </ThemeProvider>
      </body>
    </html>
  );
}