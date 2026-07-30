const INDUSTRIES = [
  "FinTech",
  "Healthcare",
  "SaaS",
  "D2C & E-commerce",
  "Real Estate",
  "Manufacturing",
  "EdTech",
  "Logistics",
  "Food & Hospitality",
  "Agriculture",
  "Legal Services",
  "Retail",
  "Insurance",
  "Energy",
  "Media & Entertainment",
  "Construction",
  "Automotive",
  "Pharmaceuticals",
  "Travel & Tourism",
  "Professional Services",
];

export function IndustryBanner() {
  const track = [...INDUSTRIES, ...INDUSTRIES];

  return (
    <section className="mkt-industry-banner" aria-label="Industries we work with">
      <div className="mkt-wrap mkt-industry-banner-head">
        <span className="mkt-industry-banner-label">Industries we work with</span>
      </div>
      <div className="mkt-industry-marquee">
        <div className="mkt-industry-marquee-track">
          {track.map((name, i) => (
            <span key={`${name}-${i}`} className="mkt-industry-chip">
              {name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
