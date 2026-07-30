"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type FeaturedPartner = {
  id: string;
  company_name: string;
  logo_url?: string;
};

export function PartnersBanner() {
  const [partners, setPartners] = useState<FeaturedPartner[]>([]);

  useEffect(() => {
    api
      .listFeaturedPartners()
      .then((data) => setPartners(data.partners || []))
      .catch(() => setPartners([]));
  }, []);

  if (!partners.length) return null;

  const track = [...partners, ...partners];

  return (
    <section className="mkt-partner-banner" aria-label="Service provider partners">
      <div className="mkt-wrap mkt-partner-banner-head">
        <span className="mkt-industry-banner-label">Trusted service partners</span>
      </div>
      <div className="mkt-industry-marquee">
        <div className="mkt-industry-marquee-track">
          {track.map((partner, i) => (
            <span key={`${partner.id}-${i}`} className="mkt-partner-chip">
              {partner.logo_url ? (
                <img src={partner.logo_url} alt="" width={72} height={32} />
              ) : (
                <span className="mkt-partner-initials" aria-hidden>
                  {(partner.company_name || "?").slice(0, 2).toUpperCase()}
                </span>
              )}
              <span className="mkt-partner-name">{partner.company_name}</span>
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}