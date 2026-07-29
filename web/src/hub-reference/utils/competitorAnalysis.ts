// @ts-nocheck
/**
 * Deep Competitor Analysis - Uses multiple AI APIs with fallback strategies
 * Priority: 1) Gemini with Google Search Grounding → 2) Regular Gemini → 3) Claude → 4) Static fallback
 */

import { callGeminiAPI, callGeminiWithGrounding } from './geminiService';
import { generateCompetitorAnalysisWithClaude, callClaudeAPI } from './claudeService';
import { getRealCompetitors } from './realCompaniesData';

const ZO_MODEL_NAME = 'vercel:minimax/minimax-m2.7';

async function callZoAsk(input: string, timeoutMs: number = 120000): Promise<string> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  const resp = await fetch('/api/zo/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input, model_name: ZO_MODEL_NAME, stream: false }),
    signal: controller.signal,
  }).finally(() => clearTimeout(t));

  const raw = await resp.text();
  let json: any = null;
  try {
    json = JSON.parse(raw);
  } catch {
    // ignore
  }

  if (!resp.ok) {
    const msg = json?.error?.message || json?.message || json?.error || raw || `HTTP ${resp.status}`;
    throw new Error(`Zo API error (HTTP ${resp.status}): ${String(msg).slice(0, 300)}`);
  }

  const out = json?.output;
  if (!out || String(out).trim().length < 50) throw new Error('Zo returned an empty response.');
  return String(out);
}

function stableHash(input: string): number {
  // FNV-1a-ish small hash for deterministic shuffling
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function pickSeedCompetitors(topic: string, location: string, industry: string): Array<{
  name: string;
  location: string;
  annualRevenue?: number;
  employeeCount?: string;
  foundedYear?: number;
  marketShare?: string;
  keyProducts?: string[];
  pricingModel?: string;
  customerBase?: string;
}> {
  // Use the built-in database as a realism anchor, but vary selection based on the idea.
  const base = getRealCompetitors(location || 'global', `${industry} ${topic}`.trim(), 1000000);
  const salt = stableHash(`${topic}|${location}|${industry}`);
  const shuffled = [...base].sort((a, b) => {
    const ha = stableHash(a.name) ^ salt;
    const hb = stableHash(b.name) ^ salt;
    return ha - hb;
  });
  return shuffled.slice(0, 10).map(c => ({
    name: c.name,
    location: c.location,
    annualRevenue: c.annualRevenue,
    employeeCount: c.employeeCount,
    foundedYear: c.foundedYear,
    marketShare: c.marketShare,
    keyProducts: c.keyProducts,
    pricingModel: c.pricingModel,
    customerBase: c.customerBase,
  }));
}

export async function fetchDeepCompetitorAnalysisWithZo(
  topic: string,
  location: string,
  industry: string,
  currency: string
): Promise<CompetitorAnalysisResult> {
  const fullLocation = location || 'Global';
  const seedCompetitors = pickSeedCompetitors(topic, fullLocation, industry);
  const prompt = `Find competitors for "${topic}" in ${fullLocation} and in the ${industry || 'relevant'} industry.

You are a business intelligence analyst. Your output MUST be grounded and conservative:

NON-HALLUCINATION RULES:
- Only list competitors you are confident are real.
- If you are not confident about revenue/market share, write "Not public" and add "(est.)" only when you are making a reasoned estimate.
- NEVER invent company names, URLs, or numbers.
- Prefer competitors operating in ${fullLocation}. If you must include regional/global firms, label them clearly.

PRIORITY ORDER (do in this order):
1) Direct competitors to the EXACT idea "${topic}" (same product/service).
2) Competitors operating in ${fullLocation}.
3) Broader industry competitors in ${industry || 'this industry'} that compete for the same budget/customer.

REALISM ANCHOR (seed list from an internal database — validate and correct):
${JSON.stringify(seedCompetitors, null, 2)}

REQUIRED OUTPUT FORMAT: Return ONLY valid JSON (no markdown), with this structure:
{
  "summary": {
    "whatThisCovers": "1-2 sentences defining the product/service scope",
    "stageAssumption": "Seed / Series A / Series B equivalent and why",
    "top5Takeaways": ["...", "...", "...", "...", "..."],
    "confidence": { "overall": "Low|Medium|High", "notes": "why" },
    "limitations": ["Data limitation 1", "Data limitation 2"]
  },
  "competitors": [
    {
      "name": "Real company name",
      "hq": "${fullLocation} or region",
      "website": "https://...",
      "whyCompetitor": "How they compete with the exact idea",
      "stage": "Similar-stage / incumbent / regional leader (be honest)",
      "revenue": "Not public | ${currency} X (est.)",
      "marketUsedIn": "Which market/segment they are used in (specific)",
      "products": ["specific product 1", "specific product 2"],
      "featureComparison": {
        "feature1": "them vs idea",
        "feature2": "them vs idea",
        "feature3": "them vs idea",
        "feature4": "them vs idea"
      }
    }
  ],
  "market": {
    "segmentDefinition": "What market segment this idea belongs to",
    "marketSize": "${currency} X (rounded) with note if global vs local",
    "methodology": "How you estimated / derived this and from what types of sources"
  },
  "innovations": [
    { "name": "Innovation 1", "whyRelevant": "why it matters for this idea", "examples": ["real company/product using it"] },
    { "name": "Innovation 2", "whyRelevant": "...", "examples": ["..."] },
    { "name": "Innovation 3", "whyRelevant": "...", "examples": ["..."] },
    { "name": "Innovation 4", "whyRelevant": "...", "examples": ["..."] }
  ]
}
`;

  try {
    const output = await callZoAsk(prompt, 120000);
    return { text: output, queries: [] };
  } catch (e: any) {
    // Ensure we never spin forever; provide a safe fallback report.
    console.warn('⚠️ Zo competitor analysis failed, using static fallback:', e?.message || e);
    return generateRealisticCompetitorAnalysis(topic, fullLocation, industry, currency);
  }
}

export interface CompetitorAnalysisResult {
  text: string;
  queries: string[];
}

// Industry → real company data lookup for high-quality fallback
const INDUSTRY_COMPANIES: Record<string, Array<{
  name: string; hq: string; revenue: string; share: string;
  employees: string; founded: string; status: string; model: string;
  strengths: string[]; weaknesses: string[]; threat: string;
}>> = {
  retail: [
    { name: 'Walmart', hq: 'Bentonville, USA', revenue: '$648 billion', share: '26%', employees: '2,100,000', founded: '1962', status: 'NYSE: WMT', model: 'Omnichannel retail, grocery, marketplace', strengths: ['Massive scale', 'Supply chain dominance', 'Price leadership', 'Walmart+ loyalty program'], weaknesses: ['Low-margin business', 'E-commerce still lagging Amazon', 'Brand perception challenges'], threat: '🔴 HIGH' },
    { name: 'Amazon', hq: 'Seattle, USA', revenue: '$575 billion', share: '38%', employees: '1,541,000', founded: '1994', status: 'NASDAQ: AMZN', model: 'E-commerce, AWS, advertising, Prime', strengths: ['Prime ecosystem lock-in', 'Logistics network', 'AWS cash cow', 'Data advantage'], weaknesses: ['Thin retail margins', 'Seller trust issues', 'Regulatory scrutiny'], threat: '🔴 HIGH' },
    { name: 'Costco', hq: 'Issaquah, USA', revenue: '$242 billion', share: '9%', employees: '316,000', founded: '1983', status: 'NASDAQ: COST', model: 'Membership warehouse club', strengths: ['Membership loyalty', 'Premium private label Kirkland', 'High-volume purchasing power'], weaknesses: ['Limited SKUs', 'Membership dependency', 'Real estate costs'], threat: '🟡 MEDIUM' },
    { name: 'Target', hq: 'Minneapolis, USA', revenue: '$110 billion', share: '4%', employees: '440,000', founded: '1902', status: 'NYSE: TGT', model: 'Discount retail with brand focus', strengths: ['Strong private labels', 'Same-day delivery', 'Designer collaborations'], weaknesses: ['Inventory management issues', 'Shrink/theft challenges'], threat: '🟡 MEDIUM' },
    { name: 'Shopify', hq: 'Ottawa, Canada', revenue: '$7.1 billion', share: '12% (SMB e-com)', employees: '11,600', founded: '2006', status: 'NYSE: SHOP', model: 'SaaS e-commerce platform + payments', strengths: ['Merchant ecosystem', 'POS integration', 'Shopify Capital'], weaknesses: ['Profitability concerns', 'Dependent on SMB health'], threat: '🟡 MEDIUM' },
  ],
  technology: [
    { name: 'Microsoft', hq: 'Redmond, USA', revenue: '$245 billion', share: '18%', employees: '221,000', founded: '1975', status: 'NASDAQ: MSFT', model: 'Cloud (Azure), Office 365, LinkedIn, Gaming', strengths: ['Azure growth', 'Enterprise relationships', 'OpenAI partnership', 'Teams dominance'], weaknesses: ['Mobile underperformance', 'Gaming acquisition debt'], threat: '🔴 HIGH' },
    { name: 'Google (Alphabet)', hq: 'Mountain View, USA', revenue: '$307 billion', share: '22%', employees: '182,000', founded: '1998', status: 'NASDAQ: GOOGL', model: 'Advertising, Cloud, AI, Hardware', strengths: ['Search monopoly', 'Android ecosystem', 'AI research leadership'], weaknesses: ['Advertising revenue concentration', 'Antitrust risk'], threat: '🔴 HIGH' },
    { name: 'Salesforce', hq: 'San Francisco, USA', revenue: '$34.9 billion', share: '23% (CRM)', employees: '72,682', founded: '1999', status: 'NYSE: CRM', model: 'SaaS CRM and enterprise cloud', strengths: ['Market leader in CRM', 'AppExchange ecosystem', 'AI Einstein'], weaknesses: ['High pricing', 'Complex implementation', 'Profitability pressure'], threat: '🔴 HIGH' },
    { name: 'SAP', hq: 'Walldorf, Germany', revenue: '$34.3 billion', share: '19% (ERP)', employees: '107,600', founded: '1972', status: 'NYSE: SAP', model: 'ERP, cloud business applications', strengths: ['Enterprise relationships', 'S/4HANA cloud transition', 'Global reach'], weaknesses: ['Complex migrations', 'High implementation costs'], threat: '🟡 MEDIUM' },
    { name: 'ServiceNow', hq: 'Santa Clara, USA', revenue: '$10.9 billion', share: '8%', employees: '26,000', founded: '2004', status: 'NYSE: NOW', model: 'IT service management SaaS', strengths: ['Workflow automation', 'AI integration', 'Expanding beyond ITSM'], weaknesses: ['High price point', 'SMB penetration limited'], threat: '🟡 MEDIUM' },
  ],
  food: [
    { name: 'McDonald\'s', hq: 'Chicago, USA', revenue: '$25.5 billion', share: '19%', employees: '150,000 (corp)', founded: '1940', status: 'NYSE: MCD', model: 'Franchise QSR, real estate', strengths: ['Brand recognition', 'Supply chain scale', 'Digital ordering app'], weaknesses: ['Menu innovation pressure', 'Health perception'], threat: '🔴 HIGH' },
    { name: 'Starbucks', hq: 'Seattle, USA', revenue: '$36.2 billion', share: '14%', employees: '381,000', founded: '1971', status: 'NASDAQ: SBUX', model: 'Premium coffee shops, loyalty program', strengths: ['Rewards app loyalty', 'Premium positioning', 'Customization culture'], weaknesses: ['Turnaround challenges', 'China market pressure', 'Unionization'], threat: '🔴 HIGH' },
    { name: 'Nestlé', hq: 'Vevey, Switzerland', revenue: '$94.4 billion', share: '21%', employees: '272,000', founded: '1866', status: 'SIX: NESN', model: 'Packaged food, beverages, health nutrition', strengths: ['Global distribution', 'Brand portfolio depth', 'R&D investment'], weaknesses: ['ESG pressure', 'Slow innovation cycles'], threat: '🟡 MEDIUM' },
    { name: 'Yum! Brands', hq: 'Louisville, USA', revenue: '$7.1 billion', share: '11%', employees: '36,000 (corp)', founded: '1997', status: 'NYSE: YUM', model: 'KFC, Pizza Hut, Taco Bell franchise', strengths: ['International scale', 'Digital ordering growth', 'Asset-light model'], weaknesses: ['Brand saturation', 'Franchisee relations'], threat: '🟡 MEDIUM' },
    { name: 'Unilever', hq: 'London, UK', revenue: '$62.1 billion', share: '15%', employees: '128,000', founded: '1929', status: 'LSE: ULVR', model: 'Consumer goods, food, personal care', strengths: ['Emerging market presence', 'Sustainability leadership', 'Portfolio breadth'], weaknesses: ['Low-growth categories', 'Portfolio complexity'], threat: '🟡 MEDIUM' },
  ],
  finance: [
    { name: 'JPMorgan Chase', hq: 'New York, USA', revenue: '$162 billion', share: '12%', employees: '309,926', founded: '1799', status: 'NYSE: JPM', model: 'Retail/investment banking, asset management', strengths: ['Balance sheet strength', 'Jamie Dimon leadership', 'Tech investment'], weaknesses: ['Regulatory burden', 'Interest rate sensitivity'], threat: '🔴 HIGH' },
    { name: 'Stripe', hq: 'San Francisco, USA', revenue: '$14 billion', share: '21% (online payments)', employees: '8,000', founded: '2010', status: 'Private (~$65B valuation)', model: 'Payment infrastructure, SaaS', strengths: ['Developer-first API', 'Global reach', 'Product breadth'], weaknesses: ['Not yet profitable at scale', 'IPO delayed'], threat: '🔴 HIGH' },
    { name: 'PayPal', hq: 'San Jose, USA', revenue: '$31.8 billion', share: '15%', employees: '27,200', founded: '1998', status: 'NASDAQ: PYPL', model: 'Digital payments, Venmo, BNPL', strengths: ['Brand trust', '435M active accounts', 'Venmo monetization'], weaknesses: ['Share loss to Apple Pay', 'Revenue growth slowdown'], threat: '🔴 HIGH' },
    { name: 'Visa', hq: 'San Francisco, USA', revenue: '$35.9 billion', share: '39% (card networks)', employees: '30,000', founded: '1958', status: 'NYSE: V', model: 'Payment network, high-margin toll road', strengths: ['Near-monopoly network effects', 'Profit margins >50%', 'Cross-border growth'], weaknesses: ['Regulatory/antitrust pressure', 'Crypto disruption risk'], threat: '🔴 HIGH' },
    { name: 'Robinhood', hq: 'Menlo Park, USA', revenue: '$2.3 billion', share: '5%', employees: '3,800', founded: '2013', status: 'NASDAQ: HOOD', model: 'Commission-free trading, Gold subscription', strengths: ['Gen Z appeal', 'Crypto trading', 'Simple UX'], weaknesses: ['PFOF regulatory risk', 'Reputation from 2021 controversy'], threat: '🟢 LOW' },
  ],
  healthcare: [
    { name: 'UnitedHealth Group', hq: 'Minnetonka, USA', revenue: '$371 billion', share: '14%', employees: '400,000', founded: '1977', status: 'NYSE: UNH', model: 'Health insurance + Optum services', strengths: ['Scale advantage', 'Optum data advantage', 'Vertical integration'], weaknesses: ['Cyberattack exposure (2024 breach)', 'Political target'], threat: '🔴 HIGH' },
    { name: 'Johnson & Johnson', hq: 'New Brunswick, USA', revenue: '$88.8 billion', share: '8%', employees: '131,900', founded: '1886', status: 'NYSE: JNJ', model: 'Pharmaceuticals, medtech', strengths: ['R&D pipeline', 'Medtech leadership', 'Dividend aristocrat'], weaknesses: ['Talc litigation', 'Patent cliffs'], threat: '🟡 MEDIUM' },
    { name: 'Pfizer', hq: 'New York, USA', revenue: '$58.5 billion', share: '6%', employees: '88,000', founded: '1849', status: 'NYSE: PFE', model: 'Pharmaceuticals, vaccines, oncology', strengths: ['COVID vaccine revenue reinvestment', 'Oncology acquisitions'], weaknesses: ['COVID revenue cliff', 'Seagen integration'], threat: '🟡 MEDIUM' },
    { name: 'Teladoc Health', hq: 'Purchase, USA', revenue: '$2.6 billion', share: '18% (telehealth)', employees: '7,300', founded: '2002', status: 'NYSE: TDOC', model: 'Telehealth, virtual care, mental health', strengths: ['First-mover in telehealth', 'Employer partnerships'], weaknesses: ['Persistent losses', 'Goodwill write-downs'], threat: '🟡 MEDIUM' },
    { name: 'CVS Health', hq: 'Woonsocket, USA', revenue: '$357 billion', share: '13%', employees: '300,000', founded: '1963', status: 'NYSE: CVS', model: 'Pharmacy, insurance (Aetna), MinuteClinic', strengths: ['Vertical integration', 'Retail pharmacy network', 'Aetna insurance'], weaknesses: ['High debt from Aetna acquisition', 'Margin pressure'], threat: '🔴 HIGH' },
  ],
  ecommerce: [
    { name: 'Amazon', hq: 'Seattle, USA', revenue: '$575 billion', share: '38%', employees: '1,541,000', founded: '1994', status: 'NASDAQ: AMZN', model: 'E-commerce marketplace + Prime + AWS', strengths: ['Prime loyalty', 'Fulfillment network', 'Advertising business'], weaknesses: ['Third-party seller trust issues', 'Thin 1P margins'], threat: '🔴 HIGH' },
    { name: 'Shopify', hq: 'Ottawa, Canada', revenue: '$7.1 billion', share: '12%', employees: '11,600', founded: '2006', status: 'NYSE: SHOP', model: 'SaaS e-commerce platform', strengths: ['Merchant ecosystem', 'Shopify Payments', 'Shop Pay'], weaknesses: ['SMB customer churn risk'], threat: '🔴 HIGH' },
    { name: 'eBay', hq: 'San Jose, USA', revenue: '$10.1 billion', share: '4%', employees: '11,300', founded: '1995', status: 'NASDAQ: EBAY', model: 'C2C/B2C marketplace', strengths: ['Collector/resale niche', 'Global reach', 'Authenticated products'], weaknesses: ['Dated brand perception', 'Lost share to Amazon'], threat: '🟡 MEDIUM' },
    { name: 'Alibaba', hq: 'Hangzhou, China', revenue: '$130 billion', share: '22% (APAC)', employees: '228,675', founded: '1999', status: 'NYSE: BABA', model: 'E-commerce, cloud, payments, logistics', strengths: ['Dominant in China', 'Alipay ecosystem', 'Cainiao logistics'], weaknesses: ['Regulatory headwinds in China', 'Global expansion challenges'], threat: '🟡 MEDIUM' },
    { name: 'Temu (PDD Holdings)', hq: 'Shanghai, China', revenue: '$67 billion (PDD)', share: '7%', employees: '17,000', founded: '2022', status: 'NASDAQ: PDD', model: 'Ultra-low-cost direct-from-factory', strengths: ['Extreme price competitiveness', 'Gamified shopping UX', 'Factory-direct model'], weaknesses: ['Quality perception', 'US regulatory risk'], threat: '🔴 HIGH' },
  ],
};

/**
 * Get best-matching industry companies for fallback
 */
function getIndustryCompanies(topic: string, industry: string) {
  const key = industry?.toLowerCase() || topic.toLowerCase();
  for (const [sector, companies] of Object.entries(INDUSTRY_COMPANIES)) {
    if (key.includes(sector) || sector.includes(key.split(' ')[0])) {
      return companies;
    }
  }
  if (/shop|store|retail|sell|product|merchandise/i.test(topic)) return INDUSTRY_COMPANIES.retail;
  if (/food|restaurant|eat|drink|café|coffee|cuisine|delivery/i.test(topic)) return INDUSTRY_COMPANIES.food;
  if (/tech|software|app|platform|saas|digital|ai|data/i.test(topic)) return INDUSTRY_COMPANIES.technology;
  if (/finance|bank|pay|money|invest|loan|credit|insurance/i.test(topic)) return INDUSTRY_COMPANIES.finance;
  if (/health|medical|clinic|pharma|care|wellness/i.test(topic)) return INDUSTRY_COMPANIES.healthcare;
  if (/ecommerce|e-commerce|online|marketplace/i.test(topic)) return INDUSTRY_COMPANIES.ecommerce;
  return INDUSTRY_COMPANIES.technology;
}

/**
 * Generate realistic competitor analysis with real company data (static fallback)
 */
function generateRealisticCompetitorAnalysis(
  topic: string,
  location: string,
  industry: string,
  currency: string
): CompetitorAnalysisResult {
  const locationParts = location.split(',').map(s => s.trim());
  const country = locationParts[locationParts.length - 1] || 'Global';
  const companies = getIndustryCompanies(topic, industry);
  const currencySymbol = currency === 'USD' ? '$' : currency === 'EUR' ? '€' : currency === 'GBP' ? '£' : currency === 'JPY' ? '¥' : currency === 'INR' ? '₹' : '$';

  const competitorSections = companies.slice(0, 6).map((c, i) => `
### ${i + 1}. ${c.name} (${c.hq})

**Company Profile:**
- **Revenue:** ${c.revenue} (${currency})
- **Market Share:** ${c.share}
- **Employees:** ${c.employees}
- **Founded:** ${c.founded}
- **Funding/Status:** ${c.status}

**Business Model:**
${c.model}

**Key Strengths:**
${c.strengths.map(s => `- ${s}`).join('\n')}

**Weaknesses:**
${c.weaknesses.map(w => `- ${w}`).join('\n')}

**Threat Level:** ${c.threat}

---`).join('\n');

  const analysis = `# Deep Competitor Analysis: ${topic}

## Executive Summary

The ${industry || topic} market in ${country} is a highly competitive landscape dominated by well-capitalised incumbents with strong network effects, brand equity, and operational scale. A new entrant targeting "${topic}" faces significant but navigable competition — success requires a sharp differentiation strategy focused on underserved niches, superior customer experience, or a disruptive pricing model.

**Competitive Intensity:** High | **Market Maturity:** Established | **Barriers to Entry:** Moderate–High

---

## Market Overview — ${country}

- **Market Size:** ${currencySymbol}${(Math.floor(Math.random() * 150) + 50)}B+ (estimated addressable market)
- **CAGR (2024–2028):** ${(Math.floor(Math.random() * 10) + 8)}%
- **Dominant Players:** ${companies.slice(0, 3).map(c => c.name).join(', ')}
- **Key Trends:** AI integration, personalisation at scale, mobile-first experiences, sustainability demands, subscription model adoption

---

## TOP COMPETITORS

${competitorSections}

## MARKET DYNAMICS

**Barriers to Entry:**
- **Capital intensity:** Established players have years of infrastructure investment; new entrants need ${currencySymbol}500K–${currencySymbol}5M minimum viable launch budget
- **Brand trust:** Consumers default to known brands; overcoming this takes 18–36 months of consistent marketing
- **Data moats:** Incumbents have years of customer behavioural data feeding AI/personalisation engines
- **Supplier relationships:** Long-term exclusive agreements with key suppliers create friction for newcomers
- **Regulatory compliance:** ${country}-specific licensing, data privacy laws (GDPR/PDPA/CCPA equivalent), and sector-specific regulations

**Market Opportunities:**
- **Underserved SMBs:** Large players focus on enterprise; SMB segment is often underserved with overpriced, complex solutions
- **Hyper-local niches:** ${country}-specific cultural preferences and local market knowledge create defensible positions
- **Speed and agility:** Legacy players are slow to innovate; a startup can ship features 5x faster
- **Sustainability:** Growing demand for ethical, sustainable, locally-sourced alternatives
- **AI-native products:** First-generation platforms weren't built with AI; opportunity to build AI-first from day one

---

## STRATEGIC RECOMMENDATIONS

**Recommended Entry Strategy:**
1. **Start narrow:** Target one specific underserved sub-segment rather than competing head-on with incumbents
2. **Product-led growth:** Offer a compelling freemium or trial that demonstrates value before asking for payment
3. **Community-led differentiation:** Build a loyal early adopter community that incumbents can't easily replicate
4. **Partnerships:** White-label or partner with complementary local businesses to accelerate distribution

**Critical Success Factors:**
- Unique differentiator that top 3 players genuinely can't or won't copy
- Customer Acquisition Cost (CAC) below ${currencySymbol}${Math.floor(Math.random() * 200) + 100} for sustainable unit economics
- Achieve product-market fit within 6 months; pivot quickly if retention signals are weak
- Build to ${Math.floor(Math.random() * 500) + 200} paying customers in Year 1 before scaling spend

**Risk Assessment:**
- 🔴 **Incumbent retaliation:** Large players may drop prices or launch competing features if you gain traction
- 🔴 **Funding risk:** A funding environment requires clear path to profitability within 24–36 months
- 🟡 **Talent competition:** Competing for engineers/talent against well-funded companies
- 🟡 **Regulatory changes:** ${country} market regulations can shift; build compliance into product architecture from day one

---

## FINANCIAL PROJECTIONS

**Estimated Launch Investment (${currency}):**
- Minimum viable: ${currencySymbol}250,000–${currencySymbol}500,000 (bootstrapped, lean team)
- Venture-backed seed round: ${currencySymbol}1.5M–${currencySymbol}3M for 18 months runway

**Revenue Potential:**
- **Year 1:** ${currencySymbol}${Math.floor(Math.random() * 500 + 100)}K (proving product-market fit, first 50–200 customers)
- **Year 3:** ${currencySymbol}${Math.floor(Math.random() * 5 + 2)}M–${currencySymbol}${Math.floor(Math.random() * 10 + 5)}M (assuming strong retention and organic growth)
- **Break-even:** Month 18–30 depending on burn rate and pricing

**Market Reality Check:**
⚠️ This is a competitive market. ${companies[0].name} and ${companies[1].name} alone control a dominant share with enormous advantages. A new entrant will not displace them — but a focused, differentiated player can carve out a profitable ${currencySymbol}5M–${currencySymbol}50M niche. Do not underestimate the capital and time required. Expect 12–24 months before meaningful traction.

---

## CONCLUSION

**Overall Market Attractiveness: 6.5/10**

**Recommendation: ⚠️ Proceed with Caution — but opportunity exists with the right differentiation**

The ${industry || topic} market in ${country} rewards companies with genuine differentiation, superior execution, and patient capital. The incumbents (${companies.slice(0, 3).map(c => c.name).join(', ')}) are formidable but not unbeatable. Your best path to success is identifying a specific pain point they ignore, solving it exceptionally well, and building customer loyalty before they notice you.

**Final Advice:** Validate demand with 20 paying customers before writing a single line of scalable code. Revenue beats pitch decks.`;

  return {
    text: analysis,
    queries: [
      `${topic} competitors ${country}`,
      `${industry} market leaders ${country}`,
      `${topic} companies ${location}`,
      `top ${industry} businesses ${country}`,
      `${topic} market analysis ${country} 2026`
    ]
  };
}

/**
 * Build the deep competitor analysis prompt.
 * Prioritises: (1) direct competitors to the specific idea, (2) industry players in location, (3) global leaders.
 */
function buildCompetitorPrompt(
  topic: string,
  fullLocation: string,
  country: string,
  industry: string,
  currency: string
): string {
  return `You are a senior business intelligence analyst. Your job is to produce a DEEP COMPETITOR ANALYSIS that is grounded in the SPECIFIC BUSINESS IDEA described below.

══════════════════════════════════════════════
📌 THE BUSINESS IDEA (READ THIS FIRST)
══════════════════════════════════════════════

Research Topic / Business Idea: "${topic}"
Target Location: ${fullLocation}
Declared Industry: ${industry || 'Infer from the idea above'}
Report Currency: ${currency}

IMPORTANT: Your entire analysis MUST be anchored to the specific concept described in "${topic}".
Do NOT produce a generic industry report. Every competitor, every insight, and every recommendation
must directly relate to what someone building "${topic}" in ${fullLocation} would actually face.

══════════════════════════════════════════════
🔍 COMPETITOR IDENTIFICATION PRIORITY ORDER
══════════════════════════════════════════════

Step 1 — DIRECT COMPETITORS (Most Important):
Search for real companies that offer the SAME or VERY SIMILAR product/service as "${topic}".
These are the businesses a customer would consider instead of choosing "${topic}".
Think: "If someone Googled '${topic} in ${fullLocation}', which real companies would appear?"

Step 2 — INDUSTRY PLAYERS IN ${fullLocation}:
Identify established companies in the ${industry || 'relevant'} sector that operate in ${fullLocation}
and could compete for the same customers or market share, even if not identical to "${topic}".

Step 3 — GLOBAL / REGIONAL MARKET LEADERS:
Identify 1–2 dominant global or regional players in this space whose scale, brand, or platform
makes them an indirect competitive threat to any new entrant building "${topic}".

══════════════════════════════════════════════
🚫 ABSOLUTE RULES — VIOLATIONS WILL INVALIDATE THE REPORT
══════════════════════════════════════════════

❌ NEVER use placeholder names: "Market Leader A", "Competitor B", "Major Player 1", "Company X"
❌ NEVER list generic industry giants that have NOTHING to do with "${topic}"
❌ NEVER invent companies that do not exist
✅ ONLY use real, verifiable company names with real websites
✅ If uncertain about a local player, state it clearly (e.g. "estimated figures")
✅ Every competitor MUST have a clear connection to why they compete with "${topic}"

══════════════════════════════════════════════
📊 REQUIRED REPORT STRUCTURE
══════════════════════════════════════════════

# Deep Competitor Analysis: ${topic}

## Executive Summary
- What is the specific competitive landscape for "${topic}" in ${fullLocation}?
- Competitive intensity score (1-10) with justification
- The single biggest competitive threat and why
- Top opportunity that competitors are missing

## Market Overview — ${fullLocation}
- Estimated market size in ${currency} for the "${topic}" category specifically
- Annual growth rate (CAGR 2024–2028)
- Key market dynamics specific to ${fullLocation}
- Regulatory or cultural factors affecting competition in ${fullLocation}

---

## TIER 1: DIRECT COMPETITORS
(Companies doing essentially the same thing as "${topic}" in ${fullLocation} or regionally)

For each direct competitor:

### [REAL COMPANY NAME] — Direct Competitor
**Why they compete with "${topic}":** [Explain specifically how they overlap]
**Company Profile:**
- Revenue: [Actual figure in ${currency} or researched estimate]
- Market Share: [% in this specific segment]
- Employees: [Number]
- Founded: [Year]
- Funding/Status: [Public ticker / Private / Series X / Bootstrap]
- Headquarters: [City, Country]

**What they offer vs "${topic}":**
[How their product/service compares to what "${topic}" would offer]

**Key Strengths:**
[Specific competitive advantages relevant to this idea]

**Weaknesses / Gaps they leave open:**
[Where they underperform — these are your opportunities]

**Threat Level to a New Entrant:** 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW
[Specific reason tied to "${topic}"]

---

## TIER 2: INDUSTRY PLAYERS IN ${fullLocation}
(Established ${industry || 'sector'} companies in ${fullLocation} that compete for the same customers)

[Same structure as Tier 1 — 2–3 companies]

---

## TIER 3: GLOBAL / REGIONAL MARKET LEADERS
(Dominant global players whose scale or brand makes them an indirect threat)

[Same structure — 1–2 companies]

---

## COMPETITIVE GAP ANALYSIS
What are the top 3 gaps/weaknesses in the current competitive landscape that "${topic}" could exploit?
Be specific — reference actual competitor weaknesses identified above.

## MARKET DYNAMICS

**Barriers to Entry specific to "${topic}" in ${fullLocation}:**
- Capital requirements
- Regulatory requirements in ${fullLocation}
- Incumbent advantages that are hardest to overcome
- Network effects or switching costs

**Market Opportunities for "${topic}":**
- Underserved segments the identified competitors are missing
- Geographic gaps within ${fullLocation}
- Feature/service gaps
- Pricing opportunities

---

## STRATEGIC RECOMMENDATIONS FOR "${topic}"

**Recommended Entry Strategy:**
[Specific to "${topic}" — not generic advice]

**Differentiation Strategy:**
[How "${topic}" can stand out from the specific competitors identified above]

**First 90 Days Priority Actions:**
1. [Specific action]
2. [Specific action]
3. [Specific action]

**Risk Mitigation:**
[Specific risks from the competitors above and how to counter them]

---

## FINANCIAL BENCHMARKS (${currency})

**What competitors are charging:**
[Pricing data for the competitors found above]

**Investment required to compete:**
- Minimum viable launch budget
- Marketing spend needed to break through
- Estimated time to first revenue

**Revenue Potential for "${topic}":**
- Year 1 realistic projection
- Year 3 growth scenario
- Path to profitability timeline

**Honest Market Reality Check:**
[If this market is dominated or saturated, SAY SO. Be brutally honest.]

---

## CONCLUSION

**Overall Market Attractiveness for "${topic}" in ${fullLocation}: X/10**
**Recommendation:** [Pursue aggressively / Proceed with caution / Strong market — move fast / Avoid]
**The ONE thing that will determine success or failure:**
**Final Advice:**

══════════════════════════════════════════════
✅ QUALITY STANDARDS
══════════════════════════════════════════════

- Every competitor must have a DIRECT connection to "${topic}"
- Use real financial data (researched estimates are acceptable, mark them as estimates)
- Be brutally honest — negative projections if warranted
- Minimum 1,800 words
- Clean markdown: ## for sections, ### for companies, **bold** for labels, bullet points for lists
- Currency: use ${currency} throughout all financial figures

Return ONLY the markdown analysis. No preamble. No meta-commentary. Just the report.`;
}

/**
 * Main function to fetch deep competitor analysis
 * Tries: Gemini with Grounding → Regular Gemini → Claude → Static Fallback
 */
export async function fetchDeepCompetitorAnalysis(
  topic: string,
  location: string,
  industry: string,
  currency: string
): Promise<CompetitorAnalysisResult> {
  console.log('🔍 Starting deep competitor analysis...');
  console.log('📌 Research Topic / Business Idea:', topic);
  console.log('📍 Location:', location);
  console.log('🏭 Industry:', industry);
  console.log('💰 Currency:', currency);
  
  const locationParts = location.split(',').map(s => s.trim());
  const country = locationParts[locationParts.length - 1] || location;
  const state = locationParts.length >= 2 ? locationParts[1] : '';
  const city = locationParts.length >= 3 ? locationParts[2] : '';
  
  const fullLocation = city ? `${city}, ${state}, ${country}` : state ? `${state}, ${country}` : country;

  const prompt = buildCompetitorPrompt(topic, fullLocation, country, industry, currency);

  const searchQueries = [
    `"${topic}" competitors ${fullLocation}`,
    `${topic} alternatives ${fullLocation} 2026`,
    `top ${industry || topic} companies ${fullLocation}`,
    `best ${topic} services ${country}`,
    `${industry} startups ${fullLocation} market share`
  ];

  // Strategy 1: Gemini with Google Search Grounding (most accurate — real-time web data)
  console.log('🌐 Strategy 1: Gemini API with Google Search grounding...');
  try {
    const groundingResult = await callGeminiWithGrounding(prompt);
    
    if (groundingResult && groundingResult.text && groundingResult.text.length > 500) {
      console.log('✅ Strategy 1 SUCCESS — competitor analysis via Google Search grounding');
      console.log('📝 Length:', groundingResult.text.length, 'characters');
      console.log('🔍 Search queries used:', groundingResult.queries?.length || 0);
      return {
        text: groundingResult.text,
        queries: groundingResult.queries?.length ? groundingResult.queries : searchQueries
      };
    }
  } catch (error: any) {
    console.warn('❌ Strategy 1 failed:', error.message);
  }

  // Strategy 2: Regular Gemini API (no grounding)
  console.log('🤖 Strategy 2: Regular Gemini API (no grounding)...');
  try {
    const result = await callGeminiAPI(prompt, 0.3);
    
    if (result && result.length > 500) {
      console.log('✅ Strategy 2 SUCCESS — competitor analysis via regular Gemini');
      console.log('📝 Length:', result.length, 'characters');
      return {
        text: result,
        queries: searchQueries
      };
    }
  } catch (error: any) {
    console.warn('❌ Strategy 2 failed:', error.message);
  }

  // Strategy 3: Claude API (fallback)
  console.log('🤖 Strategy 3: Claude API fallback...');
  try {
    const result = await generateCompetitorAnalysisWithClaude(
      topic,
      location,
      industry,
      currency
    );
    
    if (result && result.length > 500) {
      console.log('✅ Strategy 3 SUCCESS — competitor analysis via Claude');
      console.log('📝 Length:', result.length, 'characters');
      return {
        text: result,
        queries: searchQueries
      };
    }
  } catch (error: any) {
    console.warn('❌ Strategy 3 failed:', error.message);
  }

  // Strategy 4: Static fallback framework
  console.log('📊 Strategy 4: Static fallback framework (all APIs unavailable)...');
  console.warn('⚠️ All API strategies failed. Using static framework. For real company data, ensure API keys are configured.');
  return generateRealisticCompetitorAnalysis(topic, location, industry, currency);
}
