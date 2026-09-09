"use client";

import Link from "next/link";
import { BarChart3, Database, LineChart, MessageSquare, Sparkles } from "lucide-react";

const DETAIL_CARDS = [
  {
    letter: "A",
    title: "DATA PROVISION",
    body: "You can input all the data that you have related to your idea in the given form. Just a few clicks and we help you formulate it into tangible words and a real business idea.",
    Icon: Database,
  },
  {
    letter: "B",
    title: "DATA VISUALIZATION",
    body: "Get a simple report from our agent, or we will email and call you to confirm understanding — then prepare a data package with everything you need to turn the idea into a business.",
    Icon: LineChart,
  },
  {
    letter: "C",
    title: "CUSTOM SOLUTIONS",
    body: "Beyond overall research, we help you build a commercial brand with plan and execution in place — and connect you to partners who can help you grow.",
    Icon: Sparkles,
  },
  {
    letter: "D",
    title: "SUPPORTING MASSIVE DATA SETS",
    body: "We give you a market assessment and provide market inputs with solutions to boost your already existing business and new ones.",
    Icon: BarChart3,
  },
  {
    letter: "E",
    title: "CHAT WITH YOUR DATA",
    body: "We give you insights and a growth report on your business and help you plan it out.",
    Icon: MessageSquare,
  },
] as const;

export function WixDetailCards() {
  return (
    <section className="mkt-wix-details" aria-labelledby="wix-details-heading">
      <div className="mkt-wrap mkt-wix-details-inner">
        <div className="mkt-wix-details-head">
          <h2 id="wix-details-heading" className="mkt-wix-details-title">
            Want more details?
          </h2>
          <p className="mkt-wix-details-lead">
            From data input to growth chat — five ways IIDATECH turns your idea into a working plan.
          </p>
          <div className="mkt-wix-details-actions">
            <Link href="/login?mode=register" className="mkt-wix-start-btn">
              START NOW
            </Link>
          </div>
        </div>

        <div className="mkt-wix-details-grid">
          {DETAIL_CARDS.map((card) => {
            const Icon = card.Icon;
            return (
              <article
                key={card.letter}
                className={"mkt-wix-detail-card is-" + card.letter.toLowerCase()}
              >
                <span className="mkt-wix-detail-letter" aria-hidden="true">
                  {card.letter}
                </span>
                <div className="mkt-wix-detail-copy">
                  <h3>{card.title}</h3>
                  <p>{card.body}</p>
                  <span className="mkt-wix-detail-icon" aria-hidden="true">
                    <Icon size={18} strokeWidth={2.2} />
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}