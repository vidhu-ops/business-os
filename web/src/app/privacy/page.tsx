import type { Metadata } from "next";
import Link from "next/link";
import { MarketingShell } from "@/components/marketing/MarketingShell";
import { SITE_EMAIL, SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How IIDATECH collects, uses, and protects your data.",
  alternates: { canonical: `${SITE_URL}/privacy` },
};

export default function PrivacyPage() {
  return (
    <MarketingShell>
      <article className="mkt-wrap mkt-section mkt-legal">
        <p className="mkt-eyebrow">Legal</p>
        <h1 className="mkt-page-title">Privacy Policy</h1>
        <p className="mkt-sub">Last updated: August 2026</p>

        <div className="mkt-legal-body">
          <h2>Who we are</h2>
          <p>
            IIDATECH (&quot;we&quot;, &quot;us&quot;) provides a business operating platform at {SITE_URL}. Contact:{" "}
            <a href={`mailto:${SITE_EMAIL}`}>{SITE_EMAIL}</a>.
          </p>

          <h2>What we collect</h2>
          <ul>
            <li>Account details (name, email, company or project information you provide).</li>
            <li>Workspace content you create (research inputs, plans, chat messages, task data).</li>
            <li>Optional integrations you connect (for example Gmail, LinkedIn, HubSpot) and related tokens.</li>
            <li>Optional bring-your-own LLM API keys you choose to store for advanced Employee OS use.</li>
            <li>Basic usage and technical logs needed to operate and secure the service.</li>
          </ul>

          <h2>How we use data</h2>
          <p>
            We use your data to provide research, planning, Mentor, Employee OS, and automation features; to bill and
            support your account; and to improve product reliability. We do not sell your personal data.
          </p>

          <h2>Integrations and API keys</h2>
          <p>
            Free and demo use does not require your own LLM API keys. If you connect OAuth apps or store API keys, those
            credentials are used only to perform actions you request and approve. You can disconnect integrations and
            remove keys from your workspace settings.
          </p>

          <h2>Retention and deletion</h2>
          <p>
            We retain account and workspace data while your account is active. If you cancel or request deletion, we
            delete or anonymize personal data within a reasonable period unless law requires longer retention. Contact{" "}
            <a href={`mailto:${SITE_EMAIL}`}>{SITE_EMAIL}</a> to request access or deletion.
          </p>

          <h2>Security</h2>
          <p>
            We apply industry-standard safeguards (encrypted transport, access controls, least-privilege processing). No
            method of transmission or storage is perfectly secure; please use strong passwords and treat API keys as
            secrets.
          </p>

          <h2>Changes</h2>
          <p>
            We may update this policy. Material changes will be reflected on this page with an updated date. Continued
            use after changes means you accept the revised policy.
          </p>

          <p>
            See also our <Link href="/terms">Terms of Service</Link>.
          </p>
        </div>
      </article>
    </MarketingShell>
  );
}
