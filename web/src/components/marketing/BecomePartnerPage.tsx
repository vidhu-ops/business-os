import { HumanScene } from "./illustrations";
import { PartnerForm } from "./PartnerForm";

const BENEFITS = [
  {
    title: "Get discovered",
    body: "Founders using IIDATECH research and action plans see vendor recommendations. Your listing can appear when you match their needs.",
  },
  {
    title: "No listing fee",
    body: "Apply free. Upload your logo and registration docs. We verify details before featuring you on the homepage.",
  },
  {
    title: "Founder-first network",
    body: "Join MSMEs, consultants, and agencies serving founders across metros and tier-2 cities.",
  },
];

export function BecomePartnerPage() {
  return (
    <>
      <section className="mkt-wrap mkt-page-hero">
        <p className="mkt-eyebrow">Partners</p>
        <h1 className="mkt-page-title">Become a service provider or partner.</h1>
        <p className="mkt-lead mkt-page-lead">
          List your business on IIDATECH. Tell us what you offer and we add you to our partner network for founders who need you.
        </p>
      </section>

      <section className="mkt-wrap mkt-section-tight">
        <div className="mkt-split">
          <div className="mkt-split-copy">
            <span className="mkt-label">Why partner</span>
            <h2 className="mkt-h2">Reach founders at the moment they need help.</h2>
            <div className="partner-benefits">
              {BENEFITS.map((b) => (
                <article key={b.title} className="partner-benefit-card">
                  <h3>{b.title}</h3>
                  <p>{b.body}</p>
                </article>
              ))}
            </div>
          </div>
          <HumanScene variant="team" />
        </div>
      </section>

      <section className="mkt-wrap mkt-section mkt-section-last">
        <div className="mkt-section-head">
          <span className="mkt-label">Apply</span>
          <h2 className="mkt-h2">Partner application</h2>
          <p className="mkt-sub">Upload your logo and company registration. We review applications and add approved partners to the homepage banner.</p>
        </div>
        <PartnerForm />
      </section>
    </>
  );
}
