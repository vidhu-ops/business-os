// @ts-nocheck
/**
 * IIDATECH Report System Instructions
 *
 * Implements the comprehensive IIDATECH Report Generation system prompt.
 * All section generators must call buildSystemPreamble() to prepend the
 * industry-classification context before their section-specific prompt.
 *
 * Core principle: CONTEXTUAL ACCURACY — every metric, competitor, and
 * data point must match the exact industry and geography specified.
 */

// ─── Industry Classification ─────────────────────────────────────────────────

export type IndustryType = 'hardware' | 'saas' | 'services' | 'marketplace' | 'hybrid';

export interface IndustryClassification {
  type: IndustryType;
  label: string;
  metrics: string[];
  neverUseMetrics: string[];
  revenueModel: string;
  grossMarginRange: string;
  competitorType: string;
  competitorExamples: string;
  supplyChainType: string;
  valuationMethod: string;
}

/**
 * Classify the industry/business-model type from topic + industry strings.
 * Called once per report generation; result is reused across all sections.
 */
export function classifyIndustry(topic: string, industry: string): IndustryClassification {
  const combined = `${topic} ${industry}`.toLowerCase();

  // ── SaaS / Software ───────────────────────────────────────────────────────
  if (
    combined.match(
      /\b(saas|software|cloud|platform|app\b|digital product|crm|erp|hrm|devops|api|subscription software|b2b software|productivity tool|analytics tool|monitoring|cybersecurity|edtech platform|legaltech|proptech software|insurtech software)\b/
    )
  ) {
    return {
      type: 'saas',
      label: 'Software / SaaS',
      metrics: ['ARR', 'MRR', 'CAC', 'LTV', 'Churn Rate (%)', 'NRR (%)', 'ARPU', 'DAU/MAU', 'Seats'],
      neverUseMetrics: ['Units Sold', 'ASP per Unit', 'COGS per Unit', 'Inventory', 'Manufacturing Overhead'],
      revenueModel:
        'Revenue = (New ARR + Expansion ARR) − Churned ARR. ' +
        'Gross Margin ≈ 70–85% (hosting, infra, support costs). ' +
        'Unit economics: LTV:CAC target >3:1; CAC payback <18 months.',
      grossMarginRange: '70–85%',
      competitorType: 'Software companies, SaaS platforms, cloud service providers',
      competitorExamples:
        'For CRM SaaS: Salesforce, HubSpot, Pipedrive, Zoho CRM, Microsoft Dynamics. ' +
        'NEVER list hardware manufacturers or physical-product companies.',
      supplyChainType:
        'Cloud Infrastructure (AWS, GCP, Azure), CDN (Cloudflare, Fastly), ' +
        'Security (Okta, Auth0), Payment Processing (Stripe, Adyen), Support (Zendesk, Intercom)',
      valuationMethod:
        'ARR multiples: 5–15× (high growth/NRR) or 2–5× (mature). ' +
        'Rule of 40: Growth % + FCF Margin % ≥ 40. Comps: public SaaS (Salesforce, ServiceNow, Veeva).',
    };
  }

  // ── Marketplace / Platform ────────────────────────────────────────────────
  if (
    combined.match(
      /\b(marketplace|e-?commerce platform|ride.?shar|food delivery|freelance platform|gig economy|aggregator|two.?sided|peer.?to.?peer|p2p|booking platform|rental platform)\b/
    )
  ) {
    return {
      type: 'marketplace',
      label: 'Marketplace / Platform',
      metrics: ['GMV', 'Take Rate (%)', 'Active Buyers', 'Active Sellers', 'Active Users', 'Transaction Count', 'Repeat Purchase Rate', 'Liquidity Score'],
      neverUseMetrics: ['COGS per Unit', 'Manufacturing Overhead', 'ARR (unless subscription)', 'Inventory'],
      revenueModel:
        'GMV = Total transaction volume on platform. ' +
        'Revenue = GMV × Take Rate (typically 5–30% depending on category). ' +
        'Gross Margin ≈ 60–80% after payment processing and hosting.',
      grossMarginRange: '60–80%',
      competitorType: 'Marketplace platforms, two-sided networks, aggregators',
      competitorExamples:
        'For e-commerce: Amazon, Shopify, eBay, Etsy, Mercado Libre. ' +
        'For ride-sharing: Uber, Lyft, Grab, Ola. ' +
        'NEVER list logistics companies or payment processors as primary competitors.',
      supplyChainType:
        'Payment processors (Stripe, Adyen, Razorpay), logistics partners (FedEx, UPS, local 3PLs), ' +
        'cloud infra (AWS/GCP), fraud detection (Sift, Kount)',
      valuationMethod:
        'Revenue multiples: 3–10× (GMV growth and take rate driven). ' +
        'Also expressed as GMV multiple: 0.3–1.5×. ' +
        'Key: liquidity flywheel — critical mass of buyers AND sellers required.',
    };
  }

  // ── Professional Services ─────────────────────────────────────────────────
  if (
    combined.match(
      /\b(consulting|agency|professional services|staffing|recruitment|legal services|accounting|advisory|audit firm|healthcare services|clinic|hospital|therapy|coaching|training services|managed services)\b/
    )
  ) {
    return {
      type: 'services',
      label: 'Professional Services',
      metrics: ['Utilization Rate (%)', 'Billable Hours', 'Revenue per FTE', 'Project Value', 'Headcount', 'EBITDA Margin', 'Client Retention Rate'],
      neverUseMetrics: ['ARR', 'MRR', 'GMV', 'Units Sold', 'COGS per Unit', 'Inventory'],
      revenueModel:
        'Revenue = Billable Hours × Rate, OR Fixed-fee project revenue. ' +
        'Utilization >70–75% typically required for profitability. ' +
        'Gross Margin = Revenue minus direct delivery cost (30–50% typical).',
      grossMarginRange: '30–50%',
      competitorType: 'Service firms, agencies, professional service providers',
      competitorExamples:
        'For management consulting: McKinsey, BCG, Bain, Deloitte, PwC, KPMG, boutique firms. ' +
        'NEVER list software companies or product manufacturers as direct competitors.',
      supplyChainType:
        'Talent (LinkedIn, specialist recruiters), Knowledge management (Confluence, SharePoint), ' +
        'Project delivery (Jira, Asana, MS Project), CRM (Salesforce, HubSpot)',
      valuationMethod:
        'Revenue multiples: 0.5–2× (services), EBITDA multiples: 8–15×. ' +
        'Key driver: revenue per employee, utilization %, client concentration.',
    };
  }

  // ── Physical Products / Hardware / Manufacturing ───────────────────────────
  if (
    combined.match(
      /\b(manufactur|hardware|electric vehicle|ev\b|e-?bike|e-?scooter|two.?wheel|automobile|consumer electronic|appliance|device|component|food|beverage|cpg|fashion|apparel|textile|furniture|cosmetic|pharma|medical device|agricultural|mining|chemical|steel|cement|construction material)\b/
    )
  ) {
    return {
      type: 'hardware',
      label: 'Physical Products / Hardware / Manufacturing',
      metrics: ['Units Sold', 'ASP (Average Selling Price)', 'COGS per Unit', 'Gross Margin per Unit', 'Inventory Turns', 'Capacity Utilization (%)', 'Defect Rate (PPM)'],
      neverUseMetrics: ['ARR', 'MRR', 'CAC (SaaS-style)', 'NRR', 'Churn Rate', 'ARPU', 'Seats'],
      revenueModel:
        'Revenue = Units Sold × ASP. ' +
        'COGS = Materials + Labor + Manufacturing Overhead per unit. ' +
        'Gross Profit = Revenue − COGS. ' +
        'Working capital: HIGH — inventory requirements are substantial.',
      grossMarginRange: '20–45% (consumer hardware), 30–60% (premium hardware)',
      competitorType: 'Manufacturers, hardware companies, physical product companies in the same category',
      competitorExamples:
        'For Electric Two-Wheelers Asia-Pacific: Ola Electric, Ather Energy, Hero Electric, TVS iQube, Yadea, NIU. ' +
        'NEVER list Walmart, Target, or generic tech companies for hardware industries.',
      supplyChainType:
        'Battery Cells (CATL, LG Energy, Samsung SDI), Motors (Bosch, Nidec), ' +
        'Semiconductors (Infineon, NXP), Contract Manufacturers, ' +
        'Tires/Components (Michelin, CEAT, MRF), Logistics (3PLs, freight forwarders)',
      valuationMethod:
        'Revenue multiples: 1.5–3× (mature) to 3–8× (high-growth hardware). ' +
        'EBITDA multiples: 8–15×. DCF with realistic margin expansion. ' +
        'Public comps: Tesla, BYD, Ola Electric (post-IPO).',
    };
  }

  // ── Hybrid (default) ──────────────────────────────────────────────────────
  return {
    type: 'hybrid',
    label: 'Hybrid / Mixed Model',
    metrics: ['Revenue', 'Gross Margin (%)', 'Operating Margin (%)', 'Market Share (%)', 'Revenue Growth (%)', 'EBITDA'],
    neverUseMetrics: [],
    revenueModel:
      'Identify the PRIMARY revenue driver and apply the corresponding model. ' +
      'Show revenue breakdown by business line (hardware vs. software vs. services component).',
    grossMarginRange: 'Varies by revenue mix — blended margin reflects business line composition',
    competitorType: 'Companies operating the same hybrid model in the target market',
    competitorExamples:
      'Examples: Tesla (hardware + software + energy), Apple (devices + services + ecosystem). ' +
      'Identify primary competitors based on the dominant revenue stream.',
    supplyChainType:
      'Combination of physical and digital supply chain depending on product/service mix',
    valuationMethod:
      'Blended multiple based on revenue mix. ' +
      'Sum-of-parts if divisions are separable; otherwise use primary business model multiple.',
  };
}

// ─── System Preamble Builder ─────────────────────────────────────────────────

/**
 * Build the mandatory system-level preamble for any section prompt.
 * This is prepended to EVERY section-specific prompt to enforce:
 *  1. Industry classification & correct metrics
 *  2. Geography specificity
 *  3. Data quality & real-company requirements
 *  4. Honest/analytical tone
 */
export function buildSystemPreamble(
  topic: string,
  industry: string,
  location: string,
  currency: string,
  sectionName: string
): string {
  const cls = classifyIndustry(topic, industry);
  const currentDate = new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const reportDate = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

  return `
╔═══════════════════════════════════════════════════════════════╗
║          IIDATECH BUSINESS INTELLIGENCE REPORT ENGINE         ║
║                  SYSTEM INSTRUCTIONS v2.0                     ║
╚═══════════════════════════════════════════════════════════════╝

SECTION BEING GENERATED : ${sectionName}
Report Topic            : "${topic}"
Industry / Product      : ${industry || 'Infer from topic'}
Geography               : ${location}
Report Currency         : ${currency} — ALL financial figures in ${currency} with FULL numbers (no abbreviations)
Report Date             : ${reportDate}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 ▶  INDUSTRY CLASSIFICATION (ENFORCE THROUGHOUT ALL OUTPUT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on the topic "${topic}", this report covers a:
▶  ${cls.label.toUpperCase()} business

✅  REQUIRED METRICS FOR THIS BUSINESS TYPE:
${cls.metrics.map((m) => `    • ${m}`).join('\n')}

✅  REVENUE MODEL:
    ${cls.revenueModel}

✅  GROSS MARGIN BENCHMARK:
    ${cls.grossMarginRange}

✅  CORRECT COMPETITOR TYPE:
    ${cls.competitorType}

✅  COMPETITOR EXAMPLES (use as reference):
    ${cls.competitorExamples}

${cls.neverUseMetrics.length > 0 ? `❌  NEVER USE THESE METRICS (wrong business model):
${cls.neverUseMetrics.map((m) => `    • ${m}`).join('\n')}` : ''}

⚠️  METRIC ENFORCEMENT RULES:
${
  cls.type === 'hardware'
    ? `    • Use UNITS SOLD, ASP, COGS, Gross Margin per Unit, Inventory Turns
    • Do NOT say "ARR", "MRR", "churn rate", "NRR" — those are SaaS metrics; WRONG here
    • Do NOT reference "cloud adoption" or "API economy" for physical products
    • Supply chain includes specific PHYSICAL suppliers (battery makers, metal suppliers, etc.)
    • Competitors must be MANUFACTURERS or PHYSICAL product companies in this category`
    : cls.type === 'saas'
    ? `    • Use ARR, MRR, CAC, LTV, Churn, NRR, ARPU — NOT units or COGS per unit
    • Gross margin 70–85% is standard; flag anything below 60% as a concern
    • Technology focus: AI features, integrations, security, scalability, UX
    • Supply chain = cloud infra, payment processors, monitoring tools
    • Competitors must be SOFTWARE companies, NOT hardware or generic tech`
    : cls.type === 'marketplace'
    ? `    • Use GMV, Take Rate, Active Users, Buyer/Seller ratio, Transaction volume
    • Revenue = GMV × Take Rate (state the actual take rate %)
    • Cold-start and liquidity are THE critical risks — always address them
    • Competitors must be PLATFORM businesses in the same category`
    : cls.type === 'services'
    ? `    • Use Utilization Rate, Billable Hours, Revenue per FTE, Project Value
    • Profitability driven by utilization >70–75%
    • Scale is limited by headcount — be honest about this ceiling
    • Competitors must be SERVICE FIRMS, not software vendors`
    : `    • Identify the PRIMARY revenue driver; apply the matching metric framework
    • Show how the hybrid mix affects margins and valuation`
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 ▶  GEOGRAPHY SPECIFICITY (STRICTLY ENFORCED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALL data MUST be specific to: ${location}

✅  REQUIRED:
    • Market size in ${currency} for ${location} (NOT global totals unless stated as comparison)
    • Regulations from ${location} — exact law names, agencies, section numbers, penalties
    • Competitors that ACTUALLY OPERATE in ${location} (verifiable via Google)
    • Distribution channels available IN ${location}
    • Consumer preferences and cultural factors FOR ${location}
    • Infrastructure relevant to ${location} (internet penetration, logistics, EV charging, etc.)
    • Currency data in ${currency} for ${location} — localised figures

❌  FORBIDDEN:
    • Companies not active in ${location}
    • Presenting global figures as ${location} figures
    • Regulations from other countries or regions
    • Generic global data without ${location} breakdown
    • "Digital transformation" or "AI" buzzwords without specific ${location} context

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 ▶  DATA QUALITY STANDARDS (NON-NEGOTIABLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅  USE REAL DATA ONLY:
    • Actual company names (verifiable via Google, LinkedIn, Crunchbase)
    • Real market share figures (must sum to <100% — account for long-tail fragmentation)
    • Achievable growth rates (NOT fantasy 200%+ CAGR without extraordinary evidence)
    • Real revenues from public filings, or credible estimates labelled "(est.)"
    • Actual regulations (specific law names, section numbers, effective dates)
    • Real funding rounds with amounts and investors where publicly available

❌  FORBIDDEN:
    • Placeholder names: "Company A", "Market Leader 1", "Major Player", "XYZ Corp"
    • Generic buzzwords without data: "leveraging AI", "digital transformation", "ecosystem"
    • Wrong-industry competitors (Walmart for EV sector; random tech firms for food industry)
    • Inflated market sizes that fail sanity checks
    • Estimated revenues presented as confirmed without labelling

📚  DATA SOURCES — CITE APPROPRIATELY FOR ${cls.label}:
${
  cls.type === 'hardware'
    ? `    • IEA (International Energy Agency) for energy/EV products
    • BloombergNEF for electric vehicles and clean energy
    • SMEV, ACEA, SIAM for vehicle market data
    • Public company filings (Tesla, BYD, Ola Electric annual reports)
    • Government manufacturing and trade statistics for ${location}`
    : cls.type === 'saas'
    ? `    • Gartner, Forrester, IDC for IT and software markets
    • Bessemer Cloud Index, SaaS Capital benchmarks
    • Public company reports (Salesforce, Microsoft, ServiceNow)
    • G2, Capterra for competitive positioning`
    : `    • Euromonitor, Mintel, Nielsen for consumer goods
    • Crunchbase, PitchBook, CB Insights for funding and company data
    • Government economic data and trade statistics for ${location}
    • Industry trade associations and sector publications`
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 ▶  TONE & HONESTY STANDARDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅  BE BRUTALLY HONEST:
    • Include NEGATIVE projections when market reality warrants it
    • Challenge assumptions: Is TAM realistic? Are incumbents underestimated?
    • If the market is dominated, saturated, or a bad bet — say so explicitly
    • Include scenario analysis: Base Case (60% prob), Bull Case (25%), Bear Case (15%)
    • Industry-specific reality checks (e.g., "Can we compete with Chinese manufacturing scale?")

✅  PROFESSIONAL & ANALYTICAL:
    • Data-driven, not marketing fluff
    • Specific, quantified statements — not vague ("significant opportunity")
    • Cite sources inline using [1], [2] format

❌  FORBIDDEN TONE:
    • Cheerleading or overly optimistic projections without data
    • Generic business buzzwords: "synergy", "leverage", "paradigm shift"
    • Vague statements: "significant market opportunity" without a ${currency} figure
    • "lorem ipsum" or template filler text

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5 ▶  QUALITY CONTROL CHECKLIST (VERIFY BEFORE RETURNING)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before finalising the ${sectionName} section, verify:

  ✅ Industry Accuracy
     □ All competitors are from the correct industry (${cls.competitorType})
     □ Metrics match the ${cls.label} model — NOT another industry's metrics
     □ Technology/innovation focus is relevant to "${topic}"
     □ Supply chain references industry-specific suppliers

  ✅ Geographic Relevance
     □ Competitors operate in ${location}
     □ Market size reflects ${location} (not global)
     □ Regulations are ${location}-specific
     □ Currency is ${currency} throughout
     □ Cultural/consumer factors are geography-specific

  ✅ Data Realism
     □ Market shares sum to <100% (long tail accounts for remainder)
     □ Growth rates are achievable and explained
     □ Valuations use appropriate multiples: ${cls.valuationMethod}
     □ Financial projections show realistic path to profitability
     □ Unit economics are industry-standard

  ✅ Completeness & Consistency
     □ No generic placeholder text ("Company XYZ", "Product ABC")
     □ Same terminology and company names throughout
     □ Recommendations are actionable and ${location}-specific
     □ Risks are industry-relevant and quantified in ${currency}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOW GENERATE: ${sectionName.toUpperCase()}
Topic: "${topic}" | Type: ${cls.label} | Location: ${location} | Currency: ${currency}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`;
}

// ─── Section-Specific Instruction Builders ───────────────────────────────────

/**
 * Section 01 — Executive Summary instructions
 */
export function buildExecutiveSummaryInstructions(
  topic: string,
  industry: string,
  location: string,
  currency: string
): string {
  const cls = classifyIndustry(topic, industry);
  return `
SECTION 01 — EXECUTIVE SUMMARY REQUIREMENTS (${cls.label.toUpperCase()}):

For a ${cls.label} business, the Executive Summary MUST include:
${
  cls.type === 'hardware'
    ? `  • Market size in UNITS + ${currency} revenue for ${location}
  • ASP trends (increasing with premiumisation OR decreasing with scale)
  • Key suppliers and supply chain risks specific to "${topic}"
  • Regulatory environment (safety standards, import duties, certifications in ${location})
  • Distribution channels (retail, online, dealers, OEM partnerships)`
    : cls.type === 'saas'
    ? `  • Market size in seats/users AND ARR/MRR for ${location}
  • Pricing tiers and packaging evolution in the market
  • Integration ecosystem importance and stickiness
  • Security/compliance requirements affecting adoption in ${location}
  • Customer acquisition channels (product-led vs sales-led) relevant to ${location}`
    : cls.type === 'marketplace'
    ? `  • GMV (Gross Merchandise Value) and revenue for ${location}
  • Take rate benchmarks vs competitors in this category
  • Active buyer/seller counts and liquidity metrics
  • Network effects maturity — how far from critical mass?
  • Trust and fraud management approach`
    : cls.type === 'services'
    ? `  • Market size in ${currency} and headcount for ${location}
  • Utilization rates and billing rates vs market benchmarks
  • Key talent supply/demand dynamics in ${location}
  • Client acquisition and retention rates typical in ${location}
  • Delivery model (onsite/offshore/hybrid) and margin implications`
    : `  • Combined market size across business lines for ${location}
  • Primary vs secondary revenue stream breakdown
  • Cross-selling and bundling opportunities
  • Margin profile by business line`
}

NEVER in Executive Summary:
  • Mix metrics from different business models
  • Use generic "digital transformation" for non-tech products
  • List wrong-industry competitors
  • Present global figures as ${location} figures without distinction
`;
}

/**
 * Section 02 — Market Analysis instructions
 */
export function buildMarketAnalysisInstructions(
  topic: string,
  industry: string,
  location: string,
  currency: string
): string {
  const cls = classifyIndustry(topic, industry);
  return `
SECTION 02 — MARKET ANALYSIS REQUIREMENTS (${cls.label.toUpperCase()}):

Market drivers MUST be adapted to the "${topic}" business type:
${
  cls.type === 'hardware'
    ? `  • Government regulations/mandates and subsidy programmes in ${location}
  • Input cost trends (raw materials, energy, labour costs) in ${location}
  • Technology cost decline trajectory (e.g., battery costs, component prices)
  • Infrastructure buildout relevant to product (charging, distribution, retail)
  • Urban/environmental policy concerns driving adoption
  • Import duties, tariffs, and local content requirements in ${location}`
    : cls.type === 'saas'
    ? `  • Cloud adoption rates and digital maturity in ${location}
  • Remote/hybrid work penetration and its impact on this category
  • API economy growth and integration requirements
  • Data privacy regulations (GDPR, PDPA, etc.) as barrier AND driver
  • Competitive intensity among existing SaaS providers in ${location}`
    : cls.type === 'marketplace'
    ? `  • Internet and smartphone penetration enabling the marketplace in ${location}
  • Trust and payment infrastructure maturity in ${location}
  • Existing fragmentation in the industry being aggregated
  • Regulatory environment for marketplace/platform businesses in ${location}
  • Logistics and fulfilment infrastructure for ${location}`
    : cls.type === 'services'
    ? `  • Demographic shifts driving demand for this service in ${location}
  • Labour market conditions (talent availability, wage inflation in ${location})
  • Technology augmentation reducing or changing delivery costs
  • Regulatory requirements mandating use of professional services
  • Outsourcing trends in ${location} among target client companies`
    : `  • Multi-dimensional drivers across physical and digital aspects of the business`
}

Required data sources for ${location}: Use REAL sources specific to "${topic}" industry —
IEA (energy/EV), BloombergNEF, Gartner/Forrester (tech), Euromonitor (consumer goods),
government statistical agencies for ${location}, industry trade associations.
`;
}

/**
 * Section 05 — Competitive Landscape instructions
 */
export function buildCompetitiveInstructions(
  topic: string,
  industry: string,
  location: string,
  currency: string
): string {
  const cls = classifyIndustry(topic, industry);
  return `
SECTION 05 — COMPETITIVE LANDSCAPE REQUIREMENTS (${cls.label.toUpperCase()}):

CRITICAL: Use ACTUAL industry competitors for "${topic}" in ${location}

Identify top 5–10 REAL companies:
  ${cls.competitorExamples}

For EACH competitor, include industry-relevant feature comparison:
${
  cls.type === 'hardware'
    ? `  • Performance specs (range, speed, capacity, power, etc.)
  • Price point in ${currency} and value positioning
  • After-sales service network breadth in ${location}
  • Battery/component warranty terms
  • Smart/connected features
  • Distribution reach in ${location}`
    : cls.type === 'saas'
    ? `  • Pricing tiers (with actual ${currency} amounts)
  • Integrations and ecosystem depth
  • Security certifications (SOC 2, ISO 27001, etc.)
  • Scalability and uptime SLA
  • Support quality and response times
  • Feature set comparison for key use cases`
    : cls.type === 'marketplace'
    ? `  • GMV and active user counts
  • Take rate / commission structure
  • Geographic coverage within ${location}
  • Buyer/seller trust mechanisms
  • Fulfilment and logistics capabilities
  • Mobile app ratings and user experience`
    : `  • Price positioning vs market
  • Quality/outcome track record
  • Geographic reach within ${location}
  • Key differentiating capabilities
  • Customer references and NPS`
}

Market shares MUST sum to <100% — account for long-tail fragmentation.
`;
}

/**
 * Section 08 — Financial Projections instructions
 */
export function buildFinancialInstructions(
  topic: string,
  industry: string,
  location: string,
  currency: string
): string {
  const cls = classifyIndustry(topic, industry);
  return `
SECTION 08 — FINANCIAL PROJECTIONS REQUIREMENTS (${cls.label.toUpperCase()}):

Revenue model for "${topic}" (${cls.label}):
${cls.revenueModel}

5-Year projections MUST include:
${
  cls.type === 'hardware'
    ? `  • Units Sold by year (conservative/base/aggressive scenarios)
  • ASP trajectory (explain if rising with premiumisation or declining with scale)
  • COGS breakdown: Materials, Labour, Manufacturing Overhead per unit
  • Gross Profit per unit and total
  • Working Capital requirements (HIGHLIGHT: high inventory = high WC need)
  • Capex requirements (factory, equipment, tooling) in ${currency}
  • Operating leverage story: how margin improves with scale`
    : cls.type === 'saas'
    ? `  • ARR growth path: New ARR + Expansion ARR − Churned ARR
  • Gross Margin expansion toward 70–85% benchmark
  • CAC by channel and payback period
  • LTV:CAC ratio trend (target >3:1)
  • Rule of 40 score for each year
  • Working Capital: deferred revenue is positive float — explain this advantage
  • Capex: primarily R&D and cloud infra (not factories)`
    : cls.type === 'marketplace'
    ? `  • GMV growth trajectory
  • Take Rate trend (typically 5–30% depending on category)
  • Revenue = GMV × Take Rate for each year
  • Gross Margin after payment processing (typically 60–80%)
  • Path to liquidity: when buyer/seller critical mass is reached
  • Marketing spend to drive supply and demand sides
  • Working Capital: payment settlement float`
    : cls.type === 'services'
    ? `  • Revenue = FTE count × Utilization % × Billing Rate
  • Headcount ramp plan with hiring costs in ${currency}
  • Utilization rate progression toward >75%
  • Average billing rate vs market benchmarks for ${location}
  • Capex: minimal (people business) — focus on working capital
  • Gross margin: Revenue minus direct delivery cost per project`
    : `  • Show revenue breakdown by primary business line
  • Use appropriate model for each component
  • Blended gross margin with business line attribution`
}

Valuation methodology (${cls.label}):
${cls.valuationMethod}

Required scenarios: Conservative (60% prob), Base Case (25%), Aggressive (15%).
All figures in ${currency} — NO abbreviations. Write full numbers.
`;
}

/**
 * Section 09 — SWOT Analysis instructions
 */
export function buildSWOTInstructions(
  topic: string,
  industry: string,
  location: string,
  currency: string
): string {
  const cls = classifyIndustry(topic, industry);
  return `
SECTION 09 — SWOT ANALYSIS REQUIREMENTS (${cls.label.toUpperCase()}):

Industry-specific SWOT factors for "${topic}" (${cls.label}) in ${location}:

${
  cls.type === 'hardware'
    ? `STRENGTHS (hardware-specific): Battery/component technology, manufacturing scale, supply chain control, brand reputation, government certifications, distribution network depth in ${location}
WEAKNESSES (hardware-specific): High capex requirements, supply chain dependency (component bottlenecks), product recall risk, range/performance limitations, inventory obsolescence risk
OPPORTUNITIES (hardware-specific): Fleet/enterprise sales channel, export markets beyond ${location}, platform/software layer opportunity, battery swapping or servicing model, V2G or adjacent energy play
THREATS (hardware-specific): Chinese manufacturing scale and cost advantage, government subsidy phase-out, commodity price volatility (lithium, copper, steel), safety incidents causing recall, infrastructure gap slowing adoption`
    : cls.type === 'saas'
    ? `STRENGTHS (SaaS-specific): Recurring revenue predictability, near-zero marginal cost at scale, customer stickiness (switching cost), data moat, integration ecosystem lock-in
WEAKNESSES (SaaS-specific): Churn risk (especially SMB segment), intense competition from incumbents, customer concentration risk, feature commoditisation speed
OPPORTUNITIES (SaaS-specific): International expansion from ${location}, vertical industry solutions (defensible niches), AI feature embedding to increase ARPU, platform/API play to build ecosystem
THREATS (SaaS-specific): Incumbents (Microsoft, Google, Salesforce) building the same feature, data privacy regulations (GDPR, AI Act) increasing compliance cost, economic downturn triggering SaaS budget cuts`
    : cls.type === 'marketplace'
    ? `STRENGTHS (marketplace-specific): Network effects creating defensible moat, data advantage from transaction history, brand trust in ${location}, liquidity across buyer/seller base
WEAKNESSES (marketplace-specific): Cold-start problem without critical mass, disintermediation risk (bypass the platform), fraud and quality control at scale, dependency on both supply AND demand sides
OPPORTUNITIES (marketplace-specific): Adjacent category expansion, geographic expansion within ${location}, financial services layer (BNPL, insurance, working capital), B2B pivot or vertical deepening
THREATS (marketplace-specific): Large platform entrants (Amazon, Google) entering category, regulatory scrutiny (antitrust, financial services licensing), app store dependency (Apple, Google 30% cut)`
    : cls.type === 'services'
    ? `STRENGTHS (services-specific): Client relationship depth, domain expertise, reputation and brand in ${location}, talent density, recurring project revenue from repeat clients
WEAKNESSES (services-specific): People-dependent scalability ceiling, key-person risk (principal dependency), utilization volatility (feast/famine cycles), commoditisation by offshore providers
OPPORTUNITIES (services-specific): Productisation of services for recurring revenue, geographic expansion, vertical specialisation for defensible positioning, technology-augmented delivery to improve margins
THREATS (services-specific): Offshore competition undercutting on price, AI automation reducing billable hours, client economic downturn cutting discretionary spend, talent attrition to competitor firms`
    : `SWOT factors must reflect the primary business model of "${topic}" in ${location}`
}

NEVER use generic business buzzwords without industry context.
Each SWOT point must be specific, quantified in ${currency} where possible, and tied to "${topic}" in ${location}.
`;
}

/**
 * Section 10 — Risk Assessment instructions
 */
export function buildRiskInstructions(
  topic: string,
  industry: string,
  location: string,
  currency: string
): string {
  const cls = classifyIndustry(topic, industry);
  return `
SECTION 10 — RISK ASSESSMENT REQUIREMENTS (${cls.label.toUpperCase()}):

Industry-critical risks for "${topic}" (${cls.label}) in ${location}:

${
  cls.type === 'hardware'
    ? `MUST INCLUDE these hardware-specific risk categories:
  • Supply chain disruption: specific components (chips, batteries, lithium, cobalt, steel)
  • Product quality/safety incidents (recalls, liability claims, regulatory action)
  • Inventory obsolescence (technology generation gap risk)
  • Tariffs and trade policy changes affecting ${location} imports/exports
  • Manufacturing capacity constraints during demand spikes
  • Commodity price volatility (lithium, copper, rare earth metals)
  • Government subsidy reduction or elimination in ${location}`
    : cls.type === 'saas'
    ? `MUST INCLUDE these SaaS-specific risk categories:
  • Data breaches / security incidents (IBM 2025 avg: ${currency} 4.9M per breach)
  • Platform downtime (uptime SLA violations, reputational damage)
  • Key customer churn (customer concentration >20% revenue with single client)
  • Competitive feature parity from incumbents (Salesforce, Microsoft, Google building same feature)
  • Pricing pressure from commoditisation or open-source alternatives
  • Regulatory: data localisation laws, GDPR enforcement, AI Act compliance for ${location}
  • Talent loss in key engineering/product roles`
    : cls.type === 'marketplace'
    ? `MUST INCLUDE these marketplace-specific risk categories:
  • Disintermediation (buyers/sellers transacting directly, bypassing the platform)
  • Fraud and trust failures at scale (fake listings, non-delivery, payment fraud)
  • Regulatory action (antitrust, financial services licensing, gig worker classification)
  • App store platform risk (Apple/Google policy changes or commission increases)
  • Liquidity collapse if key supply or demand segment exits
  • Single-category concentration (revenue cliff if one category declines)`
    : cls.type === 'services'
    ? `MUST INCLUDE these services-specific risk categories:
  • Key person dependency (founder or key principal departure)
  • Client concentration (top 3 clients >50% revenue)
  • Delivery quality failures and reputational damage
  • Talent attrition to competitors or client in-housing
  • Scope creep and project cost overruns on fixed-fee engagements
  • Offshore/AI disruption compressing billing rates`
    : `MUST COVER risks across Market, Financial, Operational, Regulatory, and Competitive dimensions for "${topic}"`
}

For EACH risk, provide:
  • Severity: 1–10 scale
  • Probability: High (>60%) / Medium (30–60%) / Low (<30%)
  • Financial impact: ${currency} amount at risk
  • Mitigation strategy specific to ${location}
  • Monitoring metrics (KPIs to track)
`;
}

/**
 * Section 12 — Supply Chain instructions
 */
export function buildSupplyChainInstructions(
  topic: string,
  industry: string,
  location: string,
  currency: string
): string {
  const cls = classifyIndustry(topic, industry);
  return `
SECTION 12 — SUPPLY CHAIN REQUIREMENTS (${cls.label.toUpperCase()}):

Industry-specific suppliers for "${topic}" (${cls.label}):

Base your supplier list on this category:
${cls.supplyChainType}

For EACH supplier/category, include:
  • Criticality: Critical / High / Medium
  • Annual spend estimate in ${currency}
  • Lead time (days / weeks)
  • Reliability score (%)
  • Geographic risk (concentration in one country/region)
  • Backup/alternative supplier options

${
  cls.type === 'hardware'
    ? `Additional hardware supply chain requirements:
  • Identify the top 3 most critical components and their single-source risk
  • Map geographic concentration (e.g., 90% of lithium from Chile/Australia)
  • Include relevant trade tariffs affecting imports into ${location}
  • Address localisation/local content requirements in ${location}`
    : cls.type === 'saas'
    ? `Additional SaaS supply chain requirements:
  • Cloud provider concentration risk (single-cloud vs multi-cloud)
  • API dependency risk (third-party APIs that are business-critical)
  • Key SaaS vendor contract terms and renewal risk
  • Data residency requirements for ${location} (local hosting mandates)`
    : `Additional supply chain considerations specific to "${topic}" in ${location}:`
}

Real supplier names ONLY — no placeholder names.
`;
}

/**
 * Section 15 — Strategic Recommendations instructions
 */
export function buildStrategicRecommendationsInstructions(
  topic: string,
  industry: string,
  location: string,
  currency: string
): string {
  const cls = classifyIndustry(topic, industry);
  return `
SECTION 15 — STRATEGIC RECOMMENDATIONS REQUIREMENTS (${cls.label.toUpperCase()}):

Each recommendation MUST include (per IIDATECH framework):
  • Objective: What business goal does this serve?
  • Rationale: Why now? What's the opportunity or risk?
  • Investment Required: ${currency} amount and FTE resources
  • Expected Outcome: Quantified impact (revenue ${currency}, margin %, market share %)
  • Timeline: Immediate (0–6 months), Near-term (6–18 months), Long-term (18 months+)
  • Owner: Which function/role leads this
  • KPIs: How to measure success
  • Priority: Critical / High / Medium

Industry-specific prioritisation for "${topic}" (${cls.label}) in ${location}:
${
  cls.type === 'hardware'
    ? `  CRITICAL: Supply chain resilience and local sourcing in ${location}
  CRITICAL: Product certification and compliance (safety standards for ${location})
  HIGH: Distribution network expansion to underserved regions in ${location}
  HIGH: After-sales service network to reduce churn and improve satisfaction
  MEDIUM: Smart/connected features to differentiate and add software revenue layer`
    : cls.type === 'saas'
    ? `  CRITICAL: NRR improvement (expansion > churn) — target NRR >110%
  CRITICAL: Reduce CAC payback below 18 months through channel mix optimisation
  HIGH: Vertical industry solution for defensible positioning in ${location}
  HIGH: Security certifications (SOC 2, ISO 27001) to unlock enterprise market
  MEDIUM: AI copilot/agent features to increase ARPU and reduce churn`
    : cls.type === 'marketplace'
    ? `  CRITICAL: Solve liquidity (reach critical mass of buyers AND sellers in ${location})
  CRITICAL: Trust and safety framework to prevent fraud from destroying brand
  HIGH: Geographic concentration in 2–3 key cities before scaling nationally
  HIGH: Take rate optimisation without driving disintermediation
  MEDIUM: Adjacent services (logistics, payments, insurance) to increase GMV`
    : cls.type === 'services'
    ? `  CRITICAL: Reduce client concentration risk (no client >20% revenue)
  CRITICAL: Increase utilization rate to >75% through pipeline management
  HIGH: Productise one repeatable service offering for recurring revenue
  HIGH: Key person retention programme with equity or profit-sharing
  MEDIUM: Technology augmentation to improve margin without headcount growth`
    : `  Prioritise recommendations that address the PRIMARY constraints of "${topic}" in ${location}`
}

VENDORS: For each recommendation, list 3–5 REAL vendors/service providers in ${location} that can help implement it.
`;
}

/**
 * Section 16 — Investment Readiness instructions
 */
export function buildInvestmentReadinessInstructions(
  topic: string,
  industry: string,
  location: string,
  currency: string
): string {
  const cls = classifyIndustry(topic, industry);
  return `
SECTION 16 — INVESTMENT READINESS REQUIREMENTS (${cls.label.toUpperCase()}):

Valuation methodology for "${topic}" (${cls.label}):
${cls.valuationMethod}

ROI Scenarios MUST include:
  • Realistic exit multiples (based on recent comparable transactions in ${location} or globally)
  • Time to exit: typically 5–7 years for VC-backed
  • Dilution assumptions across funding rounds
  • Follow-on funding requirements (how many rounds to exit?)
  • IRR (Internal Rate of Return) calculation
  • MOIC (Multiple on Invested Capital) target

${
  cls.type === 'hardware'
    ? `Hardware-specific investment notes:
  • Capital intensity is HIGH — investors expect justified Capex plan
  • Working capital requirements are significant — model quarterly WC cycle
  • Revenue multiple 1.5–3× (mature) to 3–8× (high growth) — justify with growth rate
  • Public comps in ${location} or global for comparable valuation anchors`
    : cls.type === 'saas'
    ? `SaaS-specific investment notes:
  • ARR multiple 5–15× based on growth rate, NRR, and gross margin
  • Rule of 40 score must be ≥40 for premium valuation
  • Churn rate has outsized impact on LTV and valuation — model sensitivity
  • Path to profitability must be credible — model Rule of 40 improvement`
    : cls.type === 'marketplace'
    ? `Marketplace-specific investment notes:
  • GMV multiple: 0.3–1.5× (revenue multiple 3–10×)
  • Investors focus on: GMV growth rate, take rate sustainability, disintermediation risk
  • Critical threshold: when does the liquidity flywheel become self-sustaining?
  • Comps: Airbnb, Etsy, Fiverr, DoorDash (sector-appropriate)`
    : cls.type === 'services'
    ? `Services-specific investment notes:
  • Lower revenue multiples (0.5–2×) than software — be realistic
  • PE/strategic acquirers more relevant than VC for pure services
  • EBITDA multiples 8–15× are standard for professional services
  • Key value drivers: client relationships, brand, domain expertise, talent`
    : `Investment notes: Use appropriate multiples for the PRIMARY business model of "${topic}"`
}

Be BRUTALLY HONEST about deal attractiveness — if the IRR is below 20% or MOIC below 3×, say so.
`;
}

/**
 * Section 18 — Critical Analysis instructions
 */
export function buildCriticalAnalysisInstructions(
  topic: string,
  industry: string,
  location: string,
  currency: string
): string {
  const cls = classifyIndustry(topic, industry);
  return `
SECTION 18 — CRITICAL ANALYSIS REQUIREMENTS (${cls.label.toUpperCase()}):

HONEST ASSESSMENT FRAMEWORK — Challenge ALL key assumptions for "${topic}":

MUST ADDRESS these reality checks (${cls.label}-specific):
${
  cls.type === 'hardware'
    ? `  • "Can we compete with Chinese manufacturing scale and cost advantage in ${location}?"
  • "What happens when government subsidies end or are reduced in ${location}?"
  • "Is charging/service infrastructure growing fast enough to support demand?"
  • "Battery/component cost decline — are we dependent on factors outside our control?"
  • "Profitability reality: most hardware startups burn cash at scale. What's different here?"
  • "What is our realistic COGS trajectory and when do we reach positive unit economics?"`
    : cls.type === 'saas'
    ? `  • "Why won't incumbents (Microsoft, Google, Salesforce, sector leader) build this feature?"
  • "What if CAC keeps rising and organic acquisition dries up in ${location}?"
  • "Is this a feature or a company? Could we be acqui-hired instead of IPO?"
  • "Why won't customers churn when economic headwinds hit and budgets are cut?"
  • "Can we realistically reach Rule of 40 within our funding runway?"`
    : cls.type === 'marketplace'
    ? `  • "Can we solve the cold-start problem in ${location} without burning our runway?"
  • "What prevents buyers and sellers from going direct and bypassing us?"
  • "What happens when a large platform (Amazon, Google) enters this category?"
  • "Is our take rate sustainable or will competitive pressure compress it to zero?"
  • "How long until the liquidity flywheel becomes self-sustaining in ${location}?"`
    : cls.type === 'services'
    ? `  • "Can we scale revenue meaningfully without proportional headcount growth?"
  • "What happens if our top 2 clients leave in the same quarter?"
  • "Can we compete with offshore providers who charge 40–60% less in ${location}?"
  • "How do we protect billing rates as AI automates parts of our delivery?"
  • "Is our business genuinely acquirable or too people-dependent to exit cleanly?"`
    : `  • Challenge the primary assumptions of "${topic}" in ${location} with brutal honesty`
}

Scenario Analysis (REQUIRED):
  • Base Case (60% probability): Revenue, margin, market share, exit valuation, IRR, MOIC
  • Bull Case (25% probability): Upside assumptions and what drives them
  • Bear Case (15% probability): What goes wrong, the financial impact, and survival path

TAM Realism Check: Is the stated TAM realistic or inflated? What's the SOM (Serviceable Obtainable Market)?
`;
}

// ─── Convenience Export ───────────────────────────────────────────────────────

/**
 * One-shot builder: returns system preamble + section-specific instructions
 * for the most commonly customised sections.
 */
export function buildFullSectionPromptPrefix(
  topic: string,
  industry: string,
  location: string,
  currency: string,
  section:
    | 'executiveSummary'
    | 'marketAnalysis'
    | 'competitiveAnalysis'
    | 'financialProjections'
    | 'swotAnalysis'
    | 'riskAssessment'
    | 'supplyChain'
    | 'strategicRecommendations'
    | 'investmentReadiness'
    | 'criticalAnalysis'
    | 'generic'
): string {
  const sectionLabels: Record<string, string> = {
    executiveSummary: '01. Executive Summary & Strategic Overview',
    marketAnalysis: '02. Global Market Size & Growth Dynamics',
    competitiveAnalysis: '05. Competitive Landscape: Deep Analysis',
    financialProjections: '08. Quarterly Financial Projections',
    swotAnalysis: '09. SWOT Analysis: Internal & External Factors',
    riskAssessment: '10. Risk Assessment & Mitigation Strategy',
    supplyChain: '12. Supply Chain Logistics & Efficiency',
    strategicRecommendations: '15. Strategic Recommendations & Action Plan',
    investmentReadiness: '16. Investment Readiness & ROI Projections',
    criticalAnalysis: '18. Final Critical Analysis & Synthesis',
    generic: 'Report Section',
  };

  const sectionInstructionBuilders: Record<string, () => string> = {
    executiveSummary: () => buildExecutiveSummaryInstructions(topic, industry, location, currency),
    marketAnalysis: () => buildMarketAnalysisInstructions(topic, industry, location, currency),
    competitiveAnalysis: () => buildCompetitiveInstructions(topic, industry, location, currency),
    financialProjections: () => buildFinancialInstructions(topic, industry, location, currency),
    swotAnalysis: () => buildSWOTInstructions(topic, industry, location, currency),
    riskAssessment: () => buildRiskInstructions(topic, industry, location, currency),
    supplyChain: () => buildSupplyChainInstructions(topic, industry, location, currency),
    strategicRecommendations: () => buildStrategicRecommendationsInstructions(topic, industry, location, currency),
    investmentReadiness: () => buildInvestmentReadinessInstructions(topic, industry, location, currency),
    criticalAnalysis: () => buildCriticalAnalysisInstructions(topic, industry, location, currency),
    generic: () => '',
  };

  const preamble = buildSystemPreamble(topic, industry, location, currency, sectionLabels[section] ?? section);
  const sectionInstructions = (sectionInstructionBuilders[section] ?? (() => ''))();

  return preamble + sectionInstructions;
}
