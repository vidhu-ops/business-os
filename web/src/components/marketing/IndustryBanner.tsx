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
  return (
    <section className="mkt-industry-banner" aria-label="Industries we work with">
      <div className="mkt-wrap mkt-industry-banner-head">
        <span className="mkt-industry-banner-label">Industries we work with</span>
      </div>
      <div className="mkt-industry-marquee">
        <div className="mkt-industry-marquee-track">
          {INDUSTRIES.map((name) => (
            <span key={name} className="mkt-industry-chip">
              {name}
            </span>
          ))}
          {INDUSTRIES.map((name) => (
            <span key={`dup-${name}`} className="mkt-industry-chip" aria-hidden="true">
              {name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
