// @ts-nocheck
/**
 * Claude API Service
 *
 * Primary uses:
 *  1. Deep Competitor Analysis fallback (when Gemini is unavailable or errors)
 *  2. Individual report section generation (fallback to Gemini grounding failures)
 *  3. Full report section generation using the IIDATECH system prompt
 *
 * All prompts use the IIDATECH industry-classification system to ensure:
 *  - Correct metrics for hardware vs SaaS vs services vs marketplace
 *  - Geography-specific data for the selected location
 *  - Brutally honest projections including negative scenarios
 */

import { getClaudeKey } from './apiKeys';
import { buildFullSectionPromptPrefix, buildSystemPreamble, classifyIndustry } from './reportSystemInstructions';

const CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages';
// Use claude-opus-4-5 for best quality on competitor research; falls back gracefully
const CLAUDE_MODEL = 'claude-sonnet-4-6';

interface ClaudeResponse {
  id: string;
  type: string;
  role: string;
  content: Array<{
    type: string;
    text: string;
  }>;
  model: string;
  stop_reason: string;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

/**
 * Low-level Claude API call
 */
export async function callClaudeAPI(prompt: string): Promise<string | null> {
  const CLAUDE_API_KEY = getClaudeKey();

  try {
    console.log('🤖 Calling Claude API (model:', CLAUDE_MODEL, ')...');

    const requestBody = {
      model: CLAUDE_MODEL,
      max_tokens: 8000,
      temperature: 0.2,
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ]
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 second timeout

    const isBrowser = typeof window !== 'undefined';
    const url = isBrowser ? '/api/claude' : CLAUDE_API_URL;

    if (!CLAUDE_API_KEY && !isBrowser) {
      throw new Error('Claude API key not configured.');
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // When calling /api/claude, this is only sent to the local dev server
        ...(CLAUDE_API_KEY ? { 'x-api-key': CLAUDE_API_KEY } : {}),
        'anthropic-version': '2023-06-01',
        ...(isBrowser ? {} : { 'anthropic-dangerous-direct-browser-access': 'true' })
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      let message = errorText;
      try {
        const parsed = JSON.parse(errorText);
        message = parsed?.error?.message || parsed?.message || errorText;
      } catch {
        // keep raw text
      }
      console.error('❌ Claude API error:', response.status, String(message).substring(0, 500));
      throw new Error(`Claude API error (HTTP ${response.status}): ${String(message).slice(0, 300)}`);
    }

    const data: ClaudeResponse = await response.json();
    const text = data.content[0]?.text;

    if (!text) {
      throw new Error('Empty response from Claude API.');
    }

    console.log('✅ Claude API successful!');
    console.log('📝 Generated', data.usage.output_tokens, 'tokens');
    return text;

  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new Error('Claude API timeout after 90 seconds.');
    } else {
      const msg = error?.message ? String(error.message) : 'Claude API call failed.';
      console.error('❌ Claude API call failed:', msg);
      throw new Error(msg);
    }
  }
}

/**
 * Generate deep competitor analysis using Claude.
 * Prompt is anchored to the SPECIFIC business idea/topic first,
 * then broadens to industry players in the location, then global leaders.
 */
export async function generateCompetitorAnalysisWithClaude(
  topic: string,
  location: string,
  industry: string,
  currency: string
): Promise<string | null> {
  const locationParts = location.split(',').map(s => s.trim());
  const country = locationParts[locationParts.length - 1] || location;
  const state = locationParts.length >= 2 ? locationParts[1] : '';
  const city = locationParts.length >= 3 ? locationParts[2] : '';
  
  const fullLocation = city ? `${city}, ${state}, ${country}` : state ? `${state}, ${country}` : country;

  const prompt = `You are a senior business intelligence analyst specialising in competitive strategy. 
You have been given a SPECIFIC business idea and asked to find its real competitors.

══════════════════════════════════════════════
📌 THE BUSINESS IDEA (THIS IS YOUR ANCHOR — READ CAREFULLY)
══════════════════════════════════════════════

Research Topic / Business Idea: "${topic}"
Target Location: ${fullLocation}
Declared Industry Sector: ${industry || 'Infer from the business idea above'}
Report Currency: ${currency}

Your ENTIRE analysis must be built around this specific idea: "${topic}"
Every company you mention must be a genuine competitor to EXACTLY this concept.
Do NOT produce a generic industry overview. Produce a competitor map for THIS idea.

══════════════════════════════════════════════
🔍 HOW TO FIND THE RIGHT COMPETITORS
══════════════════════════════════════════════

STEP 1 — THINK ABOUT THE SPECIFIC IDEA:
Ask yourself: "What exactly is '${topic}'? What product or service does it provide?
Who are its customers? What problem does it solve?"

STEP 2 — FIND DIRECT COMPETITORS FIRST:
Which real, named companies are already doing the SAME THING as "${topic}" in ${fullLocation}?
These are the businesses a customer would Google instead of choosing "${topic}".
Use your training knowledge to identify actual companies — local, regional, or global — 
that directly compete for the same customers in this specific niche.

STEP 3 — FIND INDUSTRY COMPETITORS IN ${fullLocation}:
Which established ${industry || 'sector'} companies operate in ${fullLocation} 
and would compete for the same customers or budget, even if their offering differs slightly?

STEP 4 — IDENTIFY GLOBAL THREATS:
Which 1–2 global market leaders could expand into this space or already have a presence 
that would threaten any new entrant building "${topic}"?

══════════════════════════════════════════════
🚫 HARD RULES
══════════════════════════════════════════════

❌ NEVER use placeholder names like "Market Leader A", "Competitor B", "Company X", "Major Player 1"
❌ NEVER list companies with NO connection to "${topic}"
❌ NEVER invent companies — use only real companies from your training knowledge
✅ If exact revenue figures are unknown, provide research-based estimates and label them "(est.)"
✅ Every company profile must explain WHY it competes with "${topic}" specifically
✅ Be brutally honest — if this market is dominated or a bad bet, say so clearly

══════════════════════════════════════════════
📊 REQUIRED REPORT FORMAT
══════════════════════════════════════════════

# Deep Competitor Analysis: ${topic}

## Executive Summary
- What is the competitive landscape specifically for "${topic}" in ${fullLocation}?
- Competitive intensity rating: X/10 — with a one-sentence justification
- The single most dangerous competitor and why
- The biggest gap in the market that "${topic}" can exploit

## Market Overview — ${fullLocation}
- Estimated market size for the "${topic}" category in ${currency}
- CAGR 2024–2028 for this specific segment
- Key dynamics in ${fullLocation} that affect this business
- Cultural, regulatory, or infrastructure factors relevant to ${fullLocation}

---

## TIER 1: DIRECT COMPETITORS
(Real companies doing essentially the same thing as "${topic}" — highest priority)

### [REAL COMPANY NAME]
**Direct Competitive Overlap with "${topic}":** [Explain exactly how they compete]

**Company Profile:**
- **Revenue:** [Actual or estimated figure in ${currency}]
- **Market Share:** [% in this segment]
- **Employees:** [Number]
- **Founded:** [Year]
- **Funding / Status:** [Public/Private/Series/Bootstrap — include ticker if public]
- **Headquarters:** [City, Country]
- **Website:** [Domain if known]

**What They Offer vs "${topic}":**
[Compare their product/service to what "${topic}" would offer]

**Strengths:**
- [Specific competitive advantages]

**Weaknesses / Gaps They Leave Open:**
- [Where they underperform — opportunities for "${topic}"]

**Threat Level:** 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW
[Specific reason tied to "${topic}"]

---
[Repeat for 3–4 direct competitors]

---

## TIER 2: INDUSTRY PLAYERS IN ${fullLocation}
(Established ${industry || 'sector'} companies competing for the same customers in ${fullLocation})

[Same structure — 2–3 companies]

---

## TIER 3: GLOBAL / REGIONAL MARKET LEADERS
(Dominant players whose scale, brand, or platform makes them an indirect threat)

[Same structure — 1–2 companies]

---

## COMPETITIVE GAP ANALYSIS
What are the 3 biggest weaknesses in the current competitive landscape that "${topic}" can exploit?
Be specific — tie each gap to an actual competitor weakness identified above.

1. **Gap 1:** [Description + which competitor fails here]
2. **Gap 2:** [Description + which competitor fails here]
3. **Gap 3:** [Description + which competitor fails here]

---

## MARKET DYNAMICS

**Barriers to Entry for "${topic}" in ${fullLocation}:**
- Capital requirements (specific estimate in ${currency})
- Regulatory/licensing requirements in ${fullLocation}
- Hardest incumbent advantages to overcome
- Network effects or switching costs

**Market Opportunities:**
- Underserved segments the identified competitors miss
- Geographic pockets within ${fullLocation} with less competition
- Feature or service gaps
- Pricing opportunities

---

## STRATEGIC RECOMMENDATIONS FOR "${topic}"

**Recommended Entry Strategy:**
[Specific to this idea and this market — not generic]

**Differentiation Strategy:**
[How "${topic}" stands apart from the specific competitors listed above]

**First 90 Days:**
1. [Action]
2. [Action]
3. [Action]

**Risk Mitigation:**
- [Risk 1 from competitors above → mitigation]
- [Risk 2 from competitors above → mitigation]

---

## FINANCIAL BENCHMARKS (${currency})

**Competitor Pricing:**
[What the identified competitors charge — be specific]

**Investment Required to Compete:**
- Minimum launch budget (${currency})
- Marketing budget to break through
- Estimated months to first revenue

**Revenue Projections for "${topic}":**
- Year 1 (realistic, not optimistic)
- Year 3 growth scenario
- Estimated break-even point

**⚠️ Honest Market Reality Check:**
[Is this a good market to enter? Is it saturated? Is the timing right? Be brutally honest.
If the odds are poor, say so. Investors and founders need truth, not cheerleading.]

---

## CONCLUSION

**Overall Market Attractiveness for "${topic}" in ${fullLocation}: X/10**

**Recommendation:** [Pursue aggressively / Proceed with caution / Niche opportunity only / Avoid]

**The single most important factor for success:**

**Final Advice:**
[2–3 sentences of honest, direct advice for someone about to build "${topic}" in ${fullLocation}]

══════════════════════════════════════════════
✅ OUTPUT REQUIREMENTS
══════════════════════════════════════════════

- All financial figures in ${currency}
- Minimum 1,800 words
- Clean markdown formatting: ## for sections, ### for company names, **bold** for field labels
- Every competitor explicitly tied to "${topic}" — no generic industry players with no relevance
- Brutally honest where the market is tough

Return ONLY the markdown report. No preamble, no meta-commentary.`;

  return await callClaudeAPI(prompt);
}

// ─── IIDATECH Section Generation via Claude ───────────────────────────────────

/**
 * Generate a specific report section using Claude with the full IIDATECH system prompt.
 * Used as a fallback when Gemini fails on any structured section.
 */
export async function generateReportSectionWithClaude(
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
    | 'generic',
  topic: string,
  industry: string,
  location: string,
  currency: string,
  outputFormat: 'json' | 'text' = 'json',
  additionalInstructions: string = ''
): Promise<string | null> {
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, section);
  const cls = classifyIndustry(topic, industry);

  const sectionDescriptions: Record<string, string> = {
    executiveSummary: `a comprehensive 400-word executive summary covering market size in ${currency}, key competitors in ${location}, major trends, and strategic outlook`,
    marketAnalysis: `a detailed market analysis including market size in ${currency}, CAGR, 8–12 real companies operating in ${location}, growth drivers, barriers, and segmentation`,
    competitiveAnalysis: `a deep competitive landscape analysis with 8–12 real competitors in ${location}, market shares (summing to <100%), strategies, pricing, and competitive gaps`,
    financialProjections: `5-year financial projections with revenue forecasts (Conservative/Base/Aggressive scenarios), profitability metrics, investment requirements in ${currency}, and unit economics`,
    swotAnalysis: `a brutally honest SWOT analysis with 5–7 factors per quadrant, all specific to "${topic}" (${cls.label}) in ${location}`,
    riskAssessment: `a comprehensive risk assessment covering 8–12 specific risks with severity (1–10), probability, financial impact in ${currency}, and mitigation strategies`,
    supplyChain: `a supply chain analysis with 5–7 real suppliers, lead times, pricing in ${currency}, reliability scores, and geographic concentration risk`,
    strategicRecommendations: `actionable strategic recommendations with investment in ${currency}, expected ROI, timelines (Immediate/Near-term/Long-term), owners, KPIs, and 3–5 real vendors per recommendation`,
    investmentReadiness: `an investment readiness assessment with valuation methodology (${cls.valuationMethod}), IRR, MOIC, exit scenarios, and deal attractiveness rating`,
    criticalAnalysis: `a final critical analysis challenging key assumptions with scenario analysis (Base/Bull/Bear), TAM reality check, and brutally honest market assessment`,
    generic: 'a detailed analysis section',
  };

  const prompt = `${systemPrefix}

You are a senior business intelligence analyst. Generate ${sectionDescriptions[section] || 'a detailed report section'} for:

Topic: "${topic}"
Industry Type: ${cls.label}
Location: ${location}
Currency: ${currency}

${additionalInstructions ? `ADDITIONAL REQUIREMENTS:\n${additionalInstructions}\n` : ''}

CRITICAL OUTPUT RULES:
- Industry type is ${cls.label.toUpperCase()} — use ONLY these metrics: ${cls.metrics.join(', ')}
- NEVER use: ${cls.neverUseMetrics.join(', ') || 'wrong-industry metrics'}
- All financial figures in ${currency} with FULL numbers (no abbreviations — write 1000000 not 1M)
- All companies must be REAL and verifiable via Google
- Market data must be specific to ${location} (NOT global figures presented as local)
- Be BRUTALLY HONEST — include negative projections where market reality warrants
- Market shares must sum to <100% (account for long-tail fragmentation)

${outputFormat === 'json' ? 'Return ONLY valid JSON. No markdown, no code fences, no prose before or after. Begin directly with { or [ and end with } or ].' : 'Return ONLY the professional report text. No JSON, no markdown headers, just the prose content.'}`;

  return await callClaudeAPI(prompt);
}

/**
 * Generate SWOT analysis using Claude with full IIDATECH system prompt.
 */
export async function generateSWOTWithClaude(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any | null> {
  const result = await generateReportSectionWithClaude(
    'swotAnalysis',
    topic,
    industry,
    location,
    currency,
    'json',
    `Return JSON with this structure:
{
  "strengths": [{"title": "...", "description": "150+ word detailed explanation with real data", "impact": "High/Medium/Low", "examples": "Real companies in ${location} leveraging this"}],
  "weaknesses": [{"title": "...", "description": "150+ word brutal assessment with real data", "impact": "Critical/High/Medium", "mitigation": "Realistic mitigation"}],
  "opportunities": [{"title": "...", "description": "150+ word analysis with market sizing in ${currency}", "potential": "${currency} X", "timeframe": "When to act", "difficulty": "Easy/Medium/Hard"}],
  "threats": [{"title": "...", "description": "150+ word honest assessment", "severity": "Critical/High/Medium", "probability": "XX%", "impactedRevenue": "${currency} X"}]
}`
  );

  if (!result) return null;
  try {
    const cleaned = result.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const match = cleaned.match(/\{[\s\S]*\}/);
    return JSON.parse(match ? match[0] : cleaned);
  } catch {
    return null;
  }
}

/**
 * Generate financial projections using Claude with full IIDATECH system prompt.
 */
export async function generateFinancialProjectionsWithClaude(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any | null> {
  const cls = classifyIndustry(topic, industry);

  const result = await generateReportSectionWithClaude(
    'financialProjections',
    topic,
    industry,
    location,
    currency,
    'json',
    `Revenue model for this ${cls.label} business: ${cls.revenueModel}
Gross margin benchmark: ${cls.grossMarginRange}
Valuation: ${cls.valuationMethod}

Return JSON with this structure:
{
  "revenueForecasts": [
    {"scenario": "Conservative", "assumptions": "Realistic for ${location}", "year1": "${currency} X", "year2": "${currency} X", "year3": "${currency} X", "year4": "${currency} X", "year5": "${currency} X", "cagr": "X.X%", "probability": "60%"},
    {"scenario": "Base Case", "assumptions": "Most likely for ${location}", "year1": "${currency} X", "year2": "${currency} X", "year3": "${currency} X", "year4": "${currency} X", "year5": "${currency} X", "cagr": "X.X%", "probability": "25%"},
    {"scenario": "Aggressive", "assumptions": "Optimistic but achievable", "year1": "${currency} X", "year2": "${currency} X", "year3": "${currency} X", "year4": "${currency} X", "year5": "${currency} X", "cagr": "X.X%", "probability": "15%"}
  ],
  "profitabilityMetrics": {
    "grossMargin": "X-X% (${location} benchmark)",
    "operatingMargin": "X-X%",
    "netMargin": "X-X%",
    "ebitdaMargin": "X-X%",
    "breakEvenTimeline": "XX months"
  },
  "investmentRequirements": {
    "initialCapital": "${currency} X with breakdown",
    "workingCapital": "${currency} X monthly",
    "operationalExpenses": "${currency} X annually",
    "totalInvestment": "${currency} X",
    "fundingSources": ["Realistic sources in ${location}"]
  },
  "unitEconomics": {
    "avgRevenuePerCustomer": "${currency} X",
    "customerAcquisitionCost": "${currency} X",
    "lifetimeValue": "${currency} X",
    "churnRate": "X.X%",
    "paybackPeriod": "XX months"
  }
}`
  );

  if (!result) return null;
  try {
    const cleaned = result.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const match = cleaned.match(/\{[\s\S]*\}/);
    return JSON.parse(match ? match[0] : cleaned);
  } catch {
    return null;
  }
}

/**
 * Generate strategic recommendations using Claude with full IIDATECH system prompt.
 */
export async function generateStrategicRecommendationsWithClaude(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any | null> {
  const result = await generateReportSectionWithClaude(
    'strategicRecommendations',
    topic,
    industry,
    location,
    currency,
    'json',
    `Return JSON with this structure:
{
  "immediate": [
    {
      "title": "Action-oriented recommendation title",
      "description": "200+ word implementation plan specific to ${location}",
      "timeline": "XX days/weeks",
      "investment": "${currency} X",
      "expectedROI": "XX% within XX months",
      "priority": "Critical/High/Medium",
      "complexity": "Easy/Medium/Hard",
      "successMetrics": ["Specific KPI 1", "Specific KPI 2", "Specific KPI 3"],
      "risks": "Potential downsides specific to ${location}",
      "vendors": [{"name": "Real Company in ${location}", "service": "Specific service", "estimatedCost": "${currency} X", "website": "domain.com", "whyRecommended": "Specific reason"}]
    }
  ],
  "shortTerm": [],
  "longTerm": [],
  "avoidanceList": [{"title": "What NOT to do", "reason": "Why this fails in ${location}", "commonMistake": "Real example of failure"}]
}`
  );

  if (!result) return null;
  try {
    const cleaned = result.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const match = cleaned.match(/\{[\s\S]*\}/);
    return JSON.parse(match ? match[0] : cleaned);
  } catch {
    return null;
  }
}

/**
 * Generate risk assessment using Claude with full IIDATECH system prompt.
 */
export async function generateRiskAssessmentWithClaude(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any | null> {
  const result = await generateReportSectionWithClaude(
    'riskAssessment',
    topic,
    industry,
    location,
    currency,
    'json',
    `Return JSON with this structure:
{
  "overallRiskScore": "X/10",
  "riskProfile": "Conservative/Moderate/High",
  "risks": [
    {
      "category": "Market/Financial/Operational/Regulatory/Technology/Competitive",
      "title": "Specific risk name",
      "description": "100+ word explanation with real historical examples from ${location}",
      "probability": "High (>60%)/Medium (30-60%)/Low (<30%)",
      "impact": "Critical/High/Medium/Low",
      "severity": 7,
      "financialImpact": "${currency} X potential loss",
      "mitigation": "Specific mitigation strategy for ${location}",
      "mitigationCost": "${currency} X",
      "monitoringMetrics": ["KPI 1", "KPI 2", "KPI 3"]
    }
  ],
  "scenarioAnalysis": [
    {"scenario": "Best case", "probability": "X%", "description": "What happens in ${location}", "financialImpact": "${currency} +X"},
    {"scenario": "Worst case", "probability": "X%", "description": "What happens in ${location}", "financialImpact": "${currency} -X"},
    {"scenario": "Black swan", "description": "Catastrophic event", "financialImpact": "${currency} -XX"}
  ]
}`
  );

  if (!result) return null;
  try {
    const cleaned = result.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const match = cleaned.match(/\{[\s\S]*\}/);
    return JSON.parse(match ? match[0] : cleaned);
  } catch {
    return null;
  }
}

/**
 * Generate Supply Chain Analysis using Claude with full IIDATECH system prompt.
 */
export async function generateSupplyChainWithClaude(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any | null> {
  const result = await generateReportSectionWithClaude(
    'supplyChain',
    topic,
    industry,
    location,
    currency,
    'json',
    `You are a supply chain specialist. Create a detailed supply chain analysis for "${topic}" in the ${industry} industry for ${location}.

Return JSON with this structure:
{
  "overview": "150-200 word overview of supply chain for ${topic} in ${location}",
  "criticalSuppliers": [
    {
      "category": "Supplier category (e.g., 'Battery Cells', 'Cloud Infrastructure', 'Logistics')",
      "suppliers": [
        {
          "name": "Real Company Name",
          "location": "Country/Region",
          "criticality": "Critical/High/Medium",
          "annualSpend": "${currency} X (estimated)",
          "leadTime": "X days/weeks",
          "reliabilityScore": "X%",
          "geographicRisk": "Risk description (e.g., 'Single country concentration')",
          "alternativeSuppliers": "Real alternative supplier names or 'Limited alternatives'",
          "contractTerms": "Typical terms for ${location}"
        }
      ]
    }
  ],
  "keyRisks": [
    {
      "risk": "Specific supply chain risk for ${topic} in ${location}",
      "impact": "High/Medium/Low",
      "mitigation": "Practical mitigation strategy for ${location}",
      "estimatedCost": "${currency} X"
    }
  ],
  "recommendations": [
    {
      "title": "Actionable recommendation",
      "description": "Detailed implementation plan for ${location}",
      "investment": "${currency} X",
      "timeline": "X months",
      "expectedBenefit": "Quantified benefit"
    }
  ]
}

CRITICAL:
- Use REAL supplier names verifiable via Google
- All cost estimates in ${currency} with FULL numbers (no abbreviations)
- Suppliers must be relevant to "${topic}" specifically
- Geographic risk must be specific to ${location}
- Include 5-7 supplier categories with 2-3 suppliers each
- Include 4-6 key risks and 3-5 recommendations`
  );

  if (!result) return null;
  try {
    const cleaned = result.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const match = cleaned.match(/\{[\s\S]*\}/);
    return JSON.parse(match ? match[0] : cleaned);
  } catch {
    return null;
  }
}

/**
 * Generate Investment Readiness Assessment using Claude with full IIDATECH system prompt.
 */
export async function generateInvestmentReadinessWithClaude(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any | null> {
  const cls = classifyIndustry(topic, industry);

  const result = await generateReportSectionWithClaude(
    'investmentReadiness',
    topic,
    industry,
    location,
    currency,
    'json',
    `You are an investment banker specializing in ${cls.label} businesses. Create a comprehensive investment readiness assessment for "${topic}" in ${location}.

Valuation methodology for this ${cls.label} business: ${cls.valuationMethod}

Return JSON with this structure:
{
  "readinessScore": "X/10 with justification",
  "valuationAnalysis": {
    "method": "${cls.valuationMethod}",
    "currentValuation": "${currency} X based on [specific metrics]",
    "comparableTransactions": [
      {
        "company": "Real Company Name in ${topic} sector",
        "location": "${location} or region",
        "dealSize": "${currency} X",
        "multiple": "Xe.g., 5.2x ARR, 12x EBITDA",
        "date": "Month Year",
        "acquirer": "Real acquirer name or 'IPO'"
      }
    ],
    "valueDrivers": [
      "Specific factor driving valuation for ${topic}",
      "Factor 2",
      "Factor 3"
    ]
  },
  "roiScenarios": [
    {
      "scenario": "Base Case",
      "probability": "60%",
      "exitYear": 5,
      "exitValuation": "${currency} X",
      "exitMultiple": "Xx (e.g., 6.5x ARR)",
      "irr": "X.X%",
      "moic": "X.Xx (e.g., 3.2x)",
      "assumptions": "Key assumptions for ${location}"
    },
    {
      "scenario": "Bull Case",
      "probability": "25%",
      "exitYear": 4,
      "exitValuation": "${currency} X",
      "exitMultiple": "Xx",
      "irr": "X.X%",
      "moic": "X.Xx",
      "assumptions": "Optimistic but achievable assumptions"
    },
    {
      "scenario": "Bear Case",
      "probability": "15%",
      "exitYear": 7,
      "exitValuation": "${currency} X",
      "exitMultiple": "Xx",
      "irr": "X.X%",
      "moic": "X.Xx",
      "assumptions": "Conservative assumptions"
    }
  ],
  "fundingRequirements": {
    "totalRequired": "${currency} X",
    "useOfFunds": [
      {"category": "Category", "amount": "${currency} X", "percentage": "X%"}
    ],
    "fundingRounds": [
      {
        "round": "Seed/Series A/B/C",
        "timing": "Month Year",
        "amount": "${currency} X",
        "dilution": "X%",
        "keyMilestones": "Milestones to achieve this round"
      }
    ]
  },
  "dealAttractiveness": {
    "rating": "Highly Attractive / Attractive / Moderate / Below Average",
    "reasoning": "Brutally honest 200-word assessment",
    "strengthsForInvestors": ["Strength 1", "Strength 2", "Strength 3"],
    "concernsForInvestors": ["Concern 1", "Concern 2", "Concern 3"],
    "recommendedInvestorProfile": "Type of investor best suited for ${topic} in ${location}"
  }
}

HONESTY REQUIREMENT:
- Be BRUTALLY HONEST about deal attractiveness
- If IRR <20% or MOIC <3x, clearly state this is BELOW venture norms
- Include realistic exit scenarios for ${location}
- All financial figures in ${currency} with FULL numbers (no abbreviations)
- Use REAL comparable transactions with verifiable company names`
  );

  if (!result) return null;
  try {
    const cleaned = result.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const match = cleaned.match(/\{[\s\S]*\}/);
    return JSON.parse(match ? match[0] : cleaned);
  } catch {
    return null;
  }
}

/**
 * Generate Critical Analysis using Claude with full IIDATECH system prompt.
 */
export async function generateCriticalAnalysisWithClaude(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any | null> {
  const cls = classifyIndustry(topic, industry);

  const industryRealityChecks =
    cls.type === 'hardware'
      ? `- Can we compete with Chinese manufacturing scale and cost advantage in ${location}?
- What happens when government subsidies end or are reduced?
- Is infrastructure growing fast enough to support demand?
- What is our realistic COGS trajectory and when do we reach positive unit economics?`
      : cls.type === 'saas'
      ? `- Why won't incumbents (Microsoft, Google, Salesforce) build this feature?
- What if CAC keeps rising and organic acquisition dries up?
- Is this a feature or a company? Could we be acqui-hired instead of IPO?
- Can we realistically reach Rule of 40 within our funding runway?`
      : cls.type === 'marketplace'
      ? `- Can we solve the cold-start problem without burning our runway?
- What prevents buyers and sellers from going direct?
- What happens when a large platform enters this category?
- Is our take rate sustainable or will competition compress it?`
      : `- What are the fundamental constraints of "${topic}" business model in ${location}?`;

  const result = await generateReportSectionWithClaude(
    'criticalAnalysis',
    topic,
    industry,
    location,
    currency,
    'json',
    `You are a brutally honest business analyst. Create a final critical analysis that CHALLENGES all key assumptions for "${topic}" in ${location}.

INDUSTRY-SPECIFIC REALITY CHECKS (${cls.label.toUpperCase()}):
${industryRealityChecks}

Return JSON with this structure:
{
  "executiveSummary": "200-300 word brutally honest summary — Is this a good opportunity or not?",
  "keyAssumptionsChallenged": [
    {
      "assumption": "Specific assumption being made about ${topic}",
      "challenge": "Why this assumption might be wrong for ${location}",
      "evidence": "Real data or examples from ${location} or similar markets",
      "impact": "What happens if this assumption fails (in ${currency})"
    }
  ],
  "scenarioAnalysis": {
    "baseCase": {
      "probability": "60%",
      "description": "Most likely outcome for ${topic} in ${location}",
      "revenue5Year": "${currency} X",
      "marketShare": "X%",
      "profitability": "EBITDA margin X%",
      "exitValuation": "${currency} X",
      "irr": "X.X%",
      "moic": "X.Xx"
    },
    "bullCase": {
      "probability": "25%",
      "description": "What has to go RIGHT",
      "revenue5Year": "${currency} X",
      "marketShare": "X%",
      "exitValuation": "${currency} X",
      "catalysts": ["Catalyst 1", "Catalyst 2", "Catalyst 3"]
    },
    "bearCase": {
      "probability": "15%",
      "description": "What goes WRONG",
      "revenue5Year": "${currency} X",
      "marketShare": "X%",
      "exitValuation": "${currency} X or failure",
      "risks": ["Risk 1", "Risk 2", "Risk 3"]
    }
  },
  "tamRealityCheck": {
    "statedTAM": "${currency} X (from market analysis)",
    "actualSOM": "${currency} X — Serviceable Obtainable Market (realistic)",
    "reasoning": "Why the SOM is much smaller than TAM for ${location}",
    "targetMarketShare": "X% — Realistically achievable in 5 years",
    "marketShareJustification": "Why this % is achievable or NOT achievable"
  },
  "competitiveRealityCheck": {
    "biggestThreat": "Name of specific competitor or market force",
    "whyTheyWin": "Honest assessment of their advantages over ${topic}",
    "ourOnlyChance": "What would have to be true for ${topic} to win in ${location}",
    "probabilityOfSuccess": "X% — with reasoning"
  },
  "investmentRecommendation": {
    "recommendation": "PURSUE AGGRESSIVELY / PROCEED WITH CAUTION / NICHE OPPORTUNITY ONLY / AVOID",
    "reasoning": "150-word honest, direct advice",
    "minimumConditions": ["Condition 1 that MUST be met", "Condition 2", "Condition 3"],
    "dealBreakers": ["Red flag 1", "Red flag 2"]
  },
  "finalVerdict": "2-3 sentences: The single most important truth about ${topic} in ${location} that founders/investors need to accept"
}

HONESTY REQUIREMENT:
- This is the FINAL word — be ruthlessly honest
- If the market is saturated, say so explicitly
- If the odds are poor, state the probability of failure
- Challenge optimistic revenue projections with real data
- All financial figures in ${currency} with FULL numbers (no abbreviations)
- Include 5-7 challenged assumptions with real evidence`
  );

  if (!result) return null;
  try {
    const cleaned = result.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const match = cleaned.match(/\{[\s\S]*\}/);
    return JSON.parse(match ? match[0] : cleaned);
  } catch {
    return null;
  }
}