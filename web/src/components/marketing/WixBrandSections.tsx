"use client";

import Link from "next/link";

const PANELS = [
  {
    id: "planning",
    title: "Planning and Content",
    body: "Plan and write down and speak the language of your brand and your thought process to your audience.",
    image: "/marketing/wix/panel-planning.jpg",
  },
  {
    id: "media",
    title: "Media Design",
    body: "We design media, posts, websites, apps, brochures, digital videos and many more things that can be designed.",
    image: "/marketing/wix/panel-media.jpg",
  },
  {
    id: "print",
    title: "Print Design",
    body: "Print design means anything that you can physically hold and use. We can make products, posters, just flyers and so on.",
    image: "/marketing/wix/panel-print.jpg",
  },
] as const;

export function WixBrandSections() {
  return (
    <>
      <section className="mkt-wix-glow" aria-label="It's Time to Glow">
        <div className="mkt-wrap mkt-wix-glow-inner">
          <div className="mkt-wix-collage" aria-hidden="true">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className="mkt-wix-collage-item is-fabric"
              src="/marketing/wix/collage-fabric.jpg"
              alt=""
              loading="lazy"
            />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className="mkt-wix-collage-item is-product"
              src="/marketing/wix/collage-product.jpg"
              alt=""
              loading="lazy"
            />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className="mkt-wix-collage-item is-portrait"
              src="/marketing/wix/collage-portrait.jpg"
              alt=""
              loading="lazy"
            />
          </div>
          <div className="mkt-wix-glow-actions">
            <a href="#contact" className="mkt-wix-info-pill">
              Info Menu
            </a>
            <Link href="/login?mode=register" className="mkt-wix-start-btn">
              START NOW
            </Link>
            <p className="mkt-wix-glow-kicker">It&apos;s Time to Glow</p>
          </div>
        </div>
      </section>

      <section className="mkt-wix-execute" aria-labelledby="wix-execute-heading">
        <div className="mkt-wrap mkt-wix-execute-head">
          <p className="mkt-wix-execute-eyebrow">LIKE SOMETHING YOU SEE?</p>
          <h2 id="wix-execute-heading" className="mkt-wix-execute-title">
            We also <span>EXECUTE IDEAS</span>
          </h2>
          <p className="mkt-wix-execute-sub">WEBSITES, SOCIAL MEDIA, AND PR FOR YOUR BRAND</p>
        </div>
        <div className="mkt-wix-panels">
          {PANELS.map((panel) => (
            <article key={panel.id} className="mkt-wix-panel">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img className="mkt-wix-panel-image" src={panel.image} alt="" loading="lazy" />
              <div className="mkt-wix-panel-scrim" />
              <div className="mkt-wix-panel-copy">
                <h3>{panel.title}</h3>
                <p>{panel.body}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
