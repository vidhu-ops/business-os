import type { Metadata } from "next";
import Link from "next/link";
import { MarketingShell } from "@/components/marketing/MarketingShell";
import { SITE_EMAIL, SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "Terms for using the IIDATECH platform.",
  alternates: { canonical: `${SITE_URL}/terms` },
};

export default function TermsPage() {
  return (
    <MarketingShell>
      <article className="mkt-wrap mkt-section mkt-legal">
        <p className="mkt-eyebrow">Legal</p>
        <h1 className="mkt-page-title">Terms of Service</h1>
        <p className="mkt-sub">Last updated: August 2026</p>

        <div className="mkt-legal-body">
          <h2>Agreement</h2>
          <p>
            By accessing {SITE_URL} or creating an IIDATECH account, you agree to these Terms and our{" "}
            <Link href="/privacy">Privacy Policy</Link>. If you use IIDATECH for a company, you represent that you can
            bind that company.
          </p>

          <h2>The service</h2>
          <p>
            IIDATECH provides software tools for market research, business planning, mentorship, Employee OS execution,
            automation, and related features. Outputs are decision-support aids — not legal, financial, or investment
            advice. You remain responsible for decisions you make using the product.
          </p>

          <h2>Accounts and credits</h2>
          <p>
            You must provide accurate account information and keep credentials secure. Free credits and demo access are
            provided at our discretion and may change. Paid plans, when available, will be billed as described on the
            pricing page or in a separate order.
          </p>

          <h2>Acceptable use</h2>
          <ul>
            <li>Do not misuse the platform, scrape without permission, or attempt unauthorized access.</li>
            <li>Do not use IIDATECH to send spam or unlawful communications via connected integrations.</li>
            <li>External actions (email, CRM updates) require your approval where the product presents an approval step.</li>
          </ul>

          <h2>Your content and integrations</h2>
          <p>
            You retain rights to content you upload. You grant us a limited license to process that content to run the
            service. If you connect third-party services or supply API keys, you confirm you have the right to do so and
            that you will comply with those providers&apos; terms.
          </p>

          <h2>Cancellation</h2>
          <p>
            You may stop using IIDATECH at any time. On cancellation or deletion request, we handle data as described in
            the Privacy Policy. Fees already paid are generally non-refundable unless required by law or stated otherwise
            in writing.
          </p>

          <h2>Disclaimer and liability</h2>
          <p>
            The service is provided &quot;as is&quot; within the limits allowed by law. We are not liable for indirect or
            consequential damages arising from use of the platform. Our total liability for any claim is limited to the
            fees you paid us in the three months before the claim (or zero if you are on a free plan).
          </p>

          <h2>Contact</h2>
          <p>
            Questions: <a href={`mailto:${SITE_EMAIL}`}>{SITE_EMAIL}</a>.
          </p>
        </div>
      </article>
    </MarketingShell>
  );
}
