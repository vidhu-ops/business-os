import { PROCESS_STEPS } from "./audienceContent";

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

type Props = {
  signupCredits?: number;
};

export function IndustryBanner({ signupCredits = 30 }: Props) {
  return (
    <section className="mkt-industry-steps-band" aria-labelledby="home-use-steps-heading">
      <div className="mkt-industry-banner-head mkt-wrap">
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

      <div className="mkt-wrap mkt-home-use-steps">
        <h2 id="home-use-steps-heading" className="mkt-home-use-steps-title">
          How to use IIDATECH
        </h2>
        <ol className="mkt-home-use-steps-grid">
          {PROCESS_STEPS.map((item) => {
            const body =
              item.step === "01"
                ? `Sign up free and get ${signupCredits} credits to try research, plans, and tools.`
                : item.body;
            return (
              <li key={item.step} className="mkt-home-use-step-card">
                <span className="mkt-home-use-step-num">{item.step}</span>
                <div className="mkt-home-use-step-copy">
                  <strong>{item.title}</strong>
                  <p>{body}</p>
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
