import type { ReactNode } from "react";
import { SITE_PHONE_TEL, SITE_WHATSAPP } from "@/lib/site";

export type HomePricingCardConfig = {
  badge: string;
  title: string;
  price: ReactNode;
  summary: string;
  perks: string[];
  checkHref: string;
  checkExternal?: boolean;
  featured?: boolean;
};

export function buildHomePricingCards(signupCredits: number): HomePricingCardConfig[] {
  return [
    {
      badge: "Available now",
      title: "Free",
      price: (
        <>
          <span className="mkt-price-currency">&#8377;</span>0<small>to begin</small>
        </>
      ),
      summary: `Explore Research, Plan, Mentor, and Employee OS with ${signupCredits} signup credits.`,
      perks: [
        `${signupCredits} credits on signup`,
        "Research, Plan, Mentor, and Employee OS",
        "Demo workspace",
        "No credit card required",
      ],
      checkHref: "/login?mode=register",
      featured: true,
    },
    {
      badge: "Self-serve",
      title: "Starter",
      price: (
        <>
          <span>₹4,999</span>
          <small>/ month</small>
        </>
      ),
      summary: "Unlimited research and business plans when you are ready to scale.",
      perks: [
        "Unlimited research and business plans in app",
        "Employee OS with AI agents",
        "OAuth integrations",
        "Branded PDF exports",
        "Priority email support",
      ],
      checkHref: "/pricing",
    },
    {
      badge: "Talk to us",
      title: "Growth & Enterprise",
      price: <span className="mkt-price-coming">Custom scope</span>,
      summary: "Higher limits, automation builders, security review, and invoice billing.",
      perks: [
        "Advanced research and automation",
        "Team-ready workspace features",
        "Dedicated onboarding",
        "Security review & SLA options",
        "Invoice billing",
      ],
      checkHref: SITE_WHATSAPP,
      checkExternal: true,
    },
  ];
}

export function buildHomePricingTeaserCards(signupCredits: number): HomePricingCardConfig[] {
  return [
    {
      badge: "Start here",
      title: "Free",
      price: (
        <>
          <span className="mkt-price-amount">
            <span className="mkt-price-currency">&#8377;</span>0
          </span>
          <small>to start</small>
        </>
      ),
      summary: `Demo workspace plus ${signupCredits} credits for research, plans, Mentor, and Employee OS.`,
      perks: [
        `${signupCredits} signup credits`,
        "Demo workspace with sample outputs",
        "Research, Plan, Mentor, Employee OS",
        "No credit card to start",
      ],
      checkHref: "/login?mode=register",
      featured: true,
    },
    {
      badge: "Popular",
      title: "Paid plans",
      price: (
        <>
          <span className="mkt-price-from">From</span>
          <span className="mkt-price-amount">
            <span className="mkt-price-currency">&#8377;</span>4,999
          </span>
          <small>/ month</small>
        </>
      ),
      summary: "Higher limits when outputs earn their keep.",
      perks: [
        "Unlimited core research and plans (Starter)",
        "OAuth integrations",
        "Automation builders on Growth+",
        "Priority support",
      ],
      checkHref: "/pricing",
    },
    {
      badge: "Enterprise",
      title: "Enterprise",
      price: <span className="mkt-price-amount mkt-price-amount-text">Custom</span>,
      summary: "For teams that need security review and dedicated delivery.",
      perks: [
        "Custom scope & SLA",
        "Security review",
        "Dedicated onboarding",
        "Invoice billing",
      ],
      checkHref: SITE_PHONE_TEL,
      checkExternal: true,
    },
  ];
}
