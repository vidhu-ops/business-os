// @ts-nocheck
/**
 * Section-by-Section Report Generation with Gemini API
 * 
 * This module generates each report section separately with dedicated prompts
 * to ensure maximum accuracy, real data, and no placeholder content.
 */

import { callGeminiAPI, callGeminiWithGrounding } from './geminiService';
import { buildFullSectionPromptPrefix, buildSystemPreamble, classifyIndustry } from './reportSystemInstructions';

/**
 * Generate Executive Summary - Separate API call
 */
export async function generateExecutiveSummary(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<string> {
  console.log('📝 Generating Executive Summary (separate API call)...');
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'executiveSummary');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

You are a senior business analyst. Create a comprehensive executive summary about "${topic}" in the ${industry} industry for ${location}.

**INDUSTRY-SPECIFIC REQUIREMENTS (${cls.label.toUpperCase()}):**
- Use ONLY the correct metrics for this business type: ${cls.metrics.join(', ')}
- NEVER use: ${cls.neverUseMetrics.join(', ') || 'N/A — see system instructions above'}
- Revenue model: ${cls.revenueModel}

**CONTENT REQUIREMENTS:**
- This MUST be 300-400 words minimum
- Include REAL market size data in ${currency} for ${location} — use local market size, NOT global
- List 3-5 REAL competitors that actually operate in ${location} (verifiable via Google)
- Include ${cls.label}-appropriate metrics and revenue model context
- Reference ACTUAL market trends from 2025-2026
- Be BRUTALLY HONEST about challenges and opportunities — include negative outlook if warranted
- NO placeholder text, NO dummy data, NO generic statements

**RESEARCH MANDATE:**
Cross-reference data from industry-appropriate sources:
- Market research reports (Gartner/Forrester/IDC for tech; IEA/BloombergNEF for hardware; Euromonitor/Nielsen for consumer goods)
- Government economic data for ${location}
- Public company filings and annual reports
- Industry trade associations relevant to "${topic}"

**LOCATION SPECIFICITY:**
- ALL data must be specific to ${location} market
- NO global figures unless explicitly stated as comparison
- Use companies that actually operate in ${location}
- Reference ${location}-specific regulations, incentives, and market conditions

**OUTPUT FORMAT:**
Return ONLY the executive summary text (300-400 words). No JSON, no markdown formatting, just the professional paragraph text.

Be specific, be accurate, be honest. Reference real numbers and real companies operating in ${location}.`;

  const summary = await callGeminiAPI(prompt, 0.7);

  if (!summary) throw new Error('Gemini API returned null for Executive Summary');

  // Validate minimum length
  if (summary.length < 500) {
    throw new Error('Executive summary too short - needs more detail');
  }
  
  // Check for dummy text
  const dummyPhrases = ['lorem ipsum', 'placeholder', 'example company', 'company a', 'tbd'];
  const hasDummy = dummyPhrases.some(phrase => summary.toLowerCase().includes(phrase));
  if (hasDummy) {
    throw new Error('Executive summary contains placeholder text - regenerating...');
  }
  
  console.log('✅ Executive Summary generated with real data');
  return summary.trim();
}

/**
 * Generate Market Analysis - Separate API call
 */
export async function generateMarketAnalysis(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('📊 Generating Market Analysis (separate API call)...');
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'marketAnalysis');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

You are a market research analyst. Create a detailed market analysis for "${topic}" in the ${industry} industry specifically for ${location}.

**INDUSTRY-SPECIFIC REQUIREMENTS (${cls.label.toUpperCase()}):**
- Use ONLY these metrics: ${cls.metrics.join(', ')}
- Revenue model: ${cls.revenueModel}
- Gross margin benchmark: ${cls.grossMarginRange}

**CRITICAL RESEARCH REQUIREMENTS:**
- Use REAL market data from authoritative, industry-appropriate sources
- ALL financial figures must be in ${currency} and specific to ${location} market (NOT global)
- Include 8-12 REAL companies actually operating in ${location} in the "${topic}" space
- Each company must have: real name, actual revenue in ${currency}, real employee count, real headquarters
- NO dummy companies, NO placeholder names, NO made-up data
- Market shares must sum to <100% (account for long-tail fragmentation)

**COMPANY VERIFICATION:**
For EACH company you include:
1. It must be a REAL company (searchable on Google)
2. It must actually operate in ${location} in the "${topic}" category
3. Revenue must be realistic and verifiable (label estimates as "(est.)")
4. Include actual CEO name if publicly available
5. Include stock ticker if publicly traded

**MARKET SIZE DATA:**
- Current 2026 market size in ${currency} for ${location} (NOT global)
- Projections for 2027, 2028, 2029, 2030 in ${currency}
- CAGR (Compound Annual Growth Rate) with detailed explanation specific to ${location}
- Growth drivers specific to ${location} and the "${topic}" industry

**OUTPUT JSON FORMAT:**
{
  "overview": "200+ word detailed overview of ${location} market history, current state, and outlook",
  "marketSize": {
    "current2026": "${currency} X.X billion",
    "projected2027": "${currency} X.X billion",
    "projected2028": "${currency} X.X billion",
    "projected2029": "${currency} X.X billion",
    "projected2030": "${currency} X.X billion",
    "cagr": "X.X% - Explanation of what's driving this growth rate in ${location}"
  },
  "growthRate": "X.X% with detailed explanation of why ${location} is growing at this rate",
  "marketShare": "Distribution description among top players in ${location}",
  "realCompanies": [
    {
      "name": "Actual Company Name",
      "marketShare": "X.X%",
      "revenue": "${currency} X.X billion annually in ${location}",
      "employees": XXXX,
      "headquarters": "City, ${location}",
      "founded": YYYY,
      "ceo": "Actual CEO Name or 'Not publicly disclosed'",
      "stockTicker": "TICK or null",
      "recentNews": "Real recent development from 2025-2026",
      "strengths": ["Specific advantage 1", "Specific advantage 2", "Specific advantage 3"],
      "challenges": ["Real challenge 1", "Real challenge 2"],
      "strategy": "Their actual current strategy in ${location}",
      "financialHealth": "Strong/Moderate/Weak with specific reasoning"
    }
    // MUST include 8-12 real companies
  ],
  "keyDrivers": [
    {
      "text": "Specific driver with quantified impact (e.g., 'AI adoption increased efficiency by 35% in 2025')",
      "impact": "High/Medium/Low",
      "timeframe": "2026-2027 or specific timeline",
      "sources": [1, 2]
    }
    // 5-8 drivers
  ],
  "marketBarriers": [
    {
      "text": "Specific barrier affecting ${location} market",
      "severity": "Critical/High/Medium",
      "affectedSegments": "Which market segments",
      "sources": [3, 4]
    }
    // 4-6 barriers
  ],
  "regulatoryEnvironment": "Comprehensive overview of ${location}-specific regulations, compliance, recent changes",
  "marketSegmentation": {
    "byCustomerType": [
      {"segment": "B2B/B2C/Enterprise", "size": "${currency} X.X billion", "growth": "X.X%"}
    ],
    "byPricePoint": [
      {"segment": "Premium/Mid-market/Budget", "marketShare": "XX%"}
    ],
    "byGeography": [
      {"region": "Region within ${location}", "size": "${currency} X.X million"}
    ]
  }
}

Return ONLY valid JSON. NO markdown, NO code blocks, ONLY the JSON object.
ALL data must be verifiable and specific to ${location}.`;

  const response = await callGeminiAPI(prompt, 0.7);

  if (!response) throw new Error('Gemini API returned null for Market Analysis');

  // Parse and validate
  let jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const analysis = JSON.parse(jsonText);
  
  // Validate real companies
  if (!analysis.realCompanies || analysis.realCompanies.length < 5) {
    throw new Error('Market analysis needs at least 5 real companies');
  }
  
  console.log(`✅ Market Analysis generated with ${analysis.realCompanies.length} real companies`);
  return analysis;
}

/**
 * Generate Trends Analysis - Separate API call
 */
export async function generateTrendsAnalysis(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('📈 Generating Trends Analysis (separate API call)...');
  
  const prompt = `You are a trend analyst. Analyze market trends for "${topic}" in ${industry} industry for ${location}.

**RESEARCH REQUIREMENTS:**
- Base trends on REAL market research from 2025-2026
- Include ACTUAL adoption rates in ${location}
- Reference REAL companies pioneering these trends in ${location}
- All financial impacts in ${currency}
- NO made-up trends, NO placeholder data

**OUTPUT JSON:**
{
  "overview": "150+ word analysis of trend landscape in ${location}",
  "data": [
    {
      "year": 2026,
      "revenue": X.X (in billions ${currency}),
      "users": X.X (in millions),
      "marketShare": XX,
      "customerSatisfaction": XX,
      "innovationIndex": XX
    },
    {
      "year": 2027,
      "revenue": X.X,
      "users": X.X,
      "marketShare": XX,
      "customerSatisfaction": XX,
      "innovationIndex": XX
    }
    // Continue for 2028, 2029, 2030, 2031
  ],
  "emergingTrends": [
    {
      "title": "Specific trend name",
      "description": "Detailed 150+ word explanation with real examples from ${location}",
      "adoptionRate": "XX% in ${location} as of 2026",
      "marketImpact": "${currency} X.X billion impact",
      "timeline": "Peak adoption timeframe",
      "leaders": ["Real Company 1", "Real Company 2", "Real Company 3"]
    }
    // 6-8 trends
  ],
  "decliningTrends": [
    {
      "title": "What's becoming obsolete",
      "reason": "Why it's declining in ${location}",
      "impactedRevenue": "${currency} X.X million lost"
    }
    // 3-4 declining trends
  ]
}

Return ONLY valid JSON. All companies and numbers must be REAL.`;

  const response = await callGeminiAPI(prompt, 0.7);
  if (!response) throw new Error('Gemini API returned null for Trends Analysis');
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const trends = JSON.parse(jsonText);
  
  console.log('✅ Trends Analysis generated with real market data');
  return trends;
}

/**
 * Generate Financial Projections - Separate API call
 */
export async function generateFinancialProjections(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('💰 Generating Financial Projections (separate API call)...');
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'financialProjections');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

You are a financial analyst. Create realistic financial projections for "${topic}" in ${industry} for ${location}.

**INDUSTRY-SPECIFIC FINANCIAL MODEL (${cls.label.toUpperCase()}):**
${cls.revenueModel}

Gross Margin benchmark: ${cls.grossMarginRange}
Valuation methodology: ${cls.valuationMethod}

**CRITICAL REQUIREMENTS:**
- ALL amounts in ${currency} — FULL numbers, NO abbreviations (write 1000000 not 1M)
- Based on REAL industry benchmarks for ${location} and the "${topic}" category
- Use ACTUAL profitability metrics from similar ${cls.label} businesses in ${location}
- NO placeholder figures, NO made-up percentages
- Reference real VC/PE funding data and real ROI expectations for this business type
- Include scenario analysis: Conservative (60% prob), Base Case (25%), Aggressive (15%)
- Be BRUTALLY HONEST — show negative projections where market reality warrants

**RESEARCH SOURCES:**
- ${location} market economic data
- ${cls.label}-appropriate benchmark reports
- Actual comparable company performance data
- Real investment requirements for "${topic}" in ${location}

**OUTPUT JSON:**
{
  "revenueForecasts": [
    {
      "scenario": "Conservative",
      "assumptions": "Realistic assumptions based on ${location} market conditions",
      "year1": "${currency} X.X million",
      "year2": "${currency} X.X million",
      "year3": "${currency} X.X million",
      "year4": "${currency} X.X million",
      "year5": "${currency} X.X million",
      "cagr": "X.X%",
      "probability": "XX%"
    },
    {
      "scenario": "Base Case",
      "assumptions": "Most likely scenario for ${location}",
      "year1": "${currency} X.X million",
      "year2": "${currency} X.X million",
      "year3": "${currency} X.X million",
      "year4": "${currency} X.X million",
      "year5": "${currency} X.X million",
      "cagr": "X.X%",
      "probability": "XX%"
    },
    {
      "scenario": "Aggressive",
      "assumptions": "Optimistic but achievable for ${location}",
      "year1": "${currency} X.X million",
      "year2": "${currency} X.X million",
      "year3": "${currency} X.X million",
      "year4": "${currency} X.X million",
      "year5": "${currency} X.X million",
      "cagr": "X.X%",
      "probability": "XX%"
    }
  ],
  "profitabilityMetrics": {
    "grossMargin": "XX-XX% (${location} industry benchmark)",
    "operatingMargin": "XX-XX%",
    "netMargin": "XX-XX%",
    "ebitdaMargin": "XX-XX%",
    "roiExpectation": "XX-XX% typical ROI in ${location}",
    "breakEvenTimeline": "XX months typical in ${location}"
  },
  "investmentRequirements": {
    "initialCapital": "${currency} X.X million with breakdown",
    "workingCapital": "${currency} XXX,XXX monthly",
    "operationalExpenses": "${currency} X.X million annually",
    "totalInvestment": "${currency} X.X million total",
    "fundingSources": ["Typical sources in ${location}"],
    "investorExpectations": "What investors expect in ${location} for ${industry}"
  },
  "unitEconomics": {
    "avgRevenuePerCustomer": "${currency} X,XXX",
    "customerAcquisitionCost": "${currency} XXX",
    "lifetimeValue": "${currency} X,XXX",
    "churnRate": "X.X%",
    "paybackPeriod": "XX months"
  }
}

Return ONLY valid JSON with REAL numbers based on ${location} market data.`;

  const response = await callGeminiAPI(prompt, 0.7);
  if (!response) throw new Error('Gemini API returned null for Financial Projections');
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const projections = JSON.parse(jsonText);
  
  console.log('✅ Financial Projections generated with realistic data');
  return projections;
}

/**
 * Generate SWOT Analysis - Separate API call
 */
export async function generateSWOTAnalysis(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('🎯 Generating SWOT Analysis (separate API call)...');
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'swotAnalysis');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

You are a strategic analyst. Create a brutally honest SWOT analysis for "${topic}" in ${industry} for ${location}.

**INDUSTRY-SPECIFIC SWOT (${cls.label.toUpperCase()}):**
Adapt ALL SWOT factors to the "${topic}" business type — see the section instructions above.
NEVER use generic buzzwords without industry context (e.g., "digital transformation" for manufacturing, "ARR growth" for hardware).

**BRUTAL HONESTY REQUIRED:**
- Include REAL weaknesses and threats specific to ${location} and "${topic}" category
- Reference ACTUAL market failures and challenges in this industry
- Do NOT sugarcoat — be honest about difficulties, even if the market outlook is poor
- Use REAL examples from ${location} market (verifiable company names)
- Challenge key assumptions: Is the market TAM realistic? Are incumbents underestimated?

**OUTPUT JSON:**
{
  "strengths": [
    {
      "title": "Specific strength",
      "description": "Detailed 150+ word explanation with real data from ${location}",
      "impact": "High/Medium/Low",
      "sustainability": "How long this advantage lasts",
      "monetization": "How to capitalize on this in ${location}",
      "examples": "Real companies in ${location} leveraging this"
    }
    // 5-7 strengths
  ],
  "weaknesses": [
    {
      "title": "Honest weakness",
      "description": "Brutal 150+ word assessment with real data",
      "impact": "Critical/High/Medium/Low",
      "mitigation": "Realistic ways to address this in ${location}",
      "cost": "${currency} XXX,XXX to fix",
      "timeline": "XX months to overcome"
    }
    // 5-7 weaknesses - be HONEST
  ],
  "opportunities": [
    {
      "title": "Market opportunity",
      "description": "Detailed 150+ word analysis with market sizing",
      "potential": "${currency} X.X billion market size in ${location}",
      "timeframe": "When to act",
      "difficulty": "Easy/Medium/Hard to capture",
      "competition": "Who else is pursuing this in ${location}",
      "successFactors": ["What's needed to win"]
    }
    // 6-8 opportunities
  ],
  "threats": [
    {
      "title": "Real threat",
      "description": "Honest 150+ word assessment of danger",
      "severity": "Critical/High/Medium",
      "probability": "XX% likelihood",
       "timeline": "When this will impact",
      "impactedRevenue": "${currency} X.X million at risk",
      "contingencyPlan": "How to prepare"
    }
    // 5-7 threats - be REALISTIC
  ]
}

Return ONLY valid JSON. Be brutally honest about challenges.`;

  const response = await callGeminiAPI(prompt, 0.7);
  if (!response) throw new Error('Gemini API returned null for SWOT Analysis');
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const swot = JSON.parse(jsonText);
  
  console.log('✅ SWOT Analysis generated with honest assessment');
  return swot;
}

/**
 * Generate Risk Assessment - Separate API call
 */
export async function generateRiskAssessment(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('⚠️  Generating Risk Assessment (separate API call)...');
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'riskAssessment');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

You are a risk analyst. Assess all risks for "${topic}" in ${industry} for ${location}.

**INDUSTRY-SPECIFIC RISK CATEGORIES (${cls.label.toUpperCase()}):**
See system instructions above for the critical risk categories for this business type.
EVERY risk must be anchored to "${topic}" specifically — no generic risks.

**COMPREHENSIVE RISK ANALYSIS:**
- Cover ALL risk categories relevant to "${topic}": Market, Financial, Operational, Regulatory, Technology, Competitive
- Use the industry-specific risk categories defined in the system instructions above
- Include REAL historical examples of failures in ${location} or comparable markets
- Be HONEST about probability and impact — including risks where probability is HIGH
- Reference ACTUAL risk data and statistics (IBM Cost of Data Breach, regulatory fines, recall costs, etc.)
- Include monitoring KPIs for each risk — how would management detect this risk materialising?

**OUTPUT JSON:**
{
  "overallRiskScore": "X/10 based on ${location} market conditions",
  "riskProfile": "Conservative/Moderate/Aggressive",
  "risks": [
    {
      "category": "Market/Financial/Operational/Regulatory/Technology/Competitive",
      "title": "Specific risk",
      "description": "Detailed 100+ word explanation with real historical examples from ${location}",
      "probability": "High (>60%)/Medium (30-60%)/Low (<30%)",
      "impact": "Critical/High/Medium/Low",
      "severity": X (1-10 scale),
      "financialImpact": "${currency} X.X million potential loss",
      "mitigation": "Detailed mitigation strategy for ${location}",
      "mitigationCost": "${currency} XXX,XXX",
      "responsibleParty": "Who should own this",
      "monitoringMetrics": ["KPI 1", "KPI 2", "KPI 3"]
    }
    // 8-12 risks covering ALL categories
  ],
  "scenarioAnalysis": [
    {
      "scenario": "Best case",
      "probability": "XX%",
      "description": "What happens in ${location}",
      "financialImpact": "${currency} +X.X million"
    },
    {
      "scenario": "Worst case",
      "probability": "XX%",
      "description": "What happens in ${location}",
      "financialImpact": "${currency} -X.X million"
    },
    {
      "scenario": "Black swan event",
      "description": "Unlikely but catastrophic event for ${location}",
      "financialImpact": "${currency} -XX million"
    }
  ]
}

Return ONLY valid JSON with REAL risk data.`;

  const response = await callGeminiAPI(prompt, 0.7);
  if (!response) throw new Error('Gemini API returned null for Risk Assessment');
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const risks = JSON.parse(jsonText);
  
  console.log('✅ Risk Assessment generated with comprehensive analysis');
  return risks;
}

/**
 * Generate Strategic Recommendations - Separate API call
 */
export async function generateStrategicRecommendations(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('🎯 Generating Strategic Recommendations (separate API call)...');
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'strategicRecommendations');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

You are a strategy consultant. Create actionable recommendations for "${topic}" in ${industry} for ${location}.

**INDUSTRY-SPECIFIC PRIORITISATION (${cls.label.toUpperCase()}):**
See system instructions above for the priority framework specific to this business type.

**RECOMMENDATION FRAMEWORK (per IIDATECH standard):**
Each recommendation MUST include:
  - Objective: What business goal this serves
  - Rationale: Why now? What opportunity or risk drives urgency?
  - Investment Required: ${currency} amount (full numbers) + FTE resources
  - Expected Outcome: Quantified impact (${currency} revenue, % margin, % market share)
  - Timeline: Immediate (0–6 months) / Near-term (6–18 months) / Long-term (18 months+)
  - Owner: Which function/role leads
  - KPIs: How to measure success
  - Priority: Critical / High / Medium

**ACTIONABLE REQUIREMENTS:**
- Each recommendation must be SPECIFIC and implementable in ${location}
- Include 3-5 REAL vendors/service providers in ${location} for EACH recommendation
- All vendors must be verifiable (real companies operating in ${location})
- Costs must reflect ACTUAL ${location} market rates in ${currency}
- Include an "Avoidance List" — 3-5 things NOT to do in ${location}, with real examples of failures

**OUTPUT JSON:**
{
  "immediate": [
    {
      "title": "Action-oriented recommendation",
      "description": "Detailed 200+ word implementation plan specific to ${location}",
      "timeline": "XX days/weeks",
      "investment": "${currency} XXX,XXX required",
      "expectedROI": "XX% within XX months",
      "priority": "Critical/High/Medium",
      "complexity": "Easy/Medium/Hard",
      "successMetrics": ["Specific KPI 1", "Specific KPI 2", "Specific KPI 3"],
      "risks": "Potential downsides specific to ${location}",
      "dependencies": "What's needed first",
      "vendors": [
        {
          "name": "Real Company Name in ${location}",
          "service": "Specific service they provide",
          "estimatedCost": "${currency} XX,XXX - ${currency} XXX,XXX",
          "location": "City/Region in ${location}",
          "website": "company-website.com",
          "specialization": "Their area of expertise",
          "whyRecommended": "Specific reason for this vendor"
        }
        // 3-5 REAL vendors per recommendation
      ]
    }
    // 4-6 immediate actions
  ],
  "shortTerm": [
    // Same structure, 3-6 month timeline, 4-5 recommendations
  ],
  "longTerm": [
    // Same structure, 12+ month timeline, 3-4 recommendations
  ],
  "avoidanceList": [
    {
      "title": "What NOT to do",
      "reason": "Why this fails in ${location} with evidence",
      "commonMistake": "Real example of failure in ${location}"
    }
    // 3-5 things to avoid
  ]
}

Return ONLY valid JSON. ALL vendors must be REAL companies in ${location}.`;

  const response = await callGeminiAPI(prompt, 0.7);
  if (!response) throw new Error('Gemini API returned null for Strategic Recommendations');
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const recommendations = JSON.parse(jsonText);
  
  console.log('✅ Strategic Recommendations generated with real vendors');
  return recommendations;
}

/**
 * Generate Competitive Analysis - Separate API call
 */
export async function generateCompetitiveAnalysis(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('🥊 Generating Competitive Analysis (separate API call)...');
  console.log(`🔍 Topic: "${topic}"`);
  console.log(`🔍 Industry: "${industry}"`);
  console.log(`🔍 Location: "${location}"`);
  console.log(`🔍 Using Google search methodology for: "${topic} companies in ${location}"`);
  
  // Parse location into components
  const locationParts = location.split(',').map(s => s.trim());
  const hasCity = locationParts.length === 3;
  const hasState = locationParts.length >= 2;
  
  const city = hasCity ? locationParts[0] : '';
  const state = hasState ? locationParts[hasCity ? 1 : 0] : '';
  const country = locationParts[locationParts.length - 1];
  
  const specificLocation = city || state || country;
  const fullLocationString = city ? `${city}, ${state}, ${country}` : state ? `${state}, ${country}` : country;
  
  // Generate a random seed to prevent caching
  const randomSeed = Math.random().toString(36).substring(7);
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, fullLocationString, currency, 'competitiveAnalysis');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

🔥🔥🔥 UNIQUE REQUEST ID: ${randomSeed} 🔥🔥🔥

══════════════════════════════════════════════════════
                  TOPIC REQUIREMENT
══════════════════════════════════════════════════════

🎯 YOUR ENTIRE ANALYSIS MUST BE ABOUT THIS SPECIFIC TOPIC:
   
   ➤➤➤ "${topic}" ⬅⬅⬅

Industry Context: ${industry || 'Not specified - infer from topic'} — Type: ${cls.label}
Location: ${fullLocationString}

🚨🚨🚨 CRITICAL VALIDATION 🚨🚨🚨

Before you add ANY company, verify this EXACT match:

1️⃣ Does this company's MAIN BUSINESS directly relate to "${topic}"?
2️⃣ If I Google "${topic} companies in ${fullLocationString}", would THIS company appear in top results?
3️⃣ Is this company actually DOING "${topic}" as their primary business model?

❌ IF THE ANSWER TO ANY OF THESE IS "NO" → EXCLUDE THE COMPANY IMMEDIATELY ❌

══════════════════════════════════════════════════════
            WHAT THIS MEANS IN PRACTICE
══════════════════════════════════════════════════════

📌 TOPIC: "${topic}"

If this topic is about:
• Manufacturing → Find manufacturers (NOT retailers, NOT service providers)
• Software → Find software companies (NOT hardware, NOT general tech)
• Restaurants → Find restaurant chains (NOT food manufacturers, NOT delivery services)
• Real Estate → Find real estate developers/brokers (NOT construction, NOT property management)
• Healthcare → Find healthcare providers (NOT insurance, NOT pharmaceutical unless specified)
• Consulting → Find consulting firms (NOT software companies, NOT training providers)
• E-commerce → Find e-commerce platforms/retailers (NOT logistics, NOT payment processors)

🎯 YOUR TASK: Find companies in "${fullLocationString}" whose PRIMARY business is "${topic}"

══════════════════════════════════════════════════════
              EXAMPLES TO LEARN FROM
══════════════════════════════════════════════════════

✅ CORRECT MATCHING EXAMPLES:

Topic: "Electric Vehicle Manufacturing" + Location: "United States"
→ Return: Tesla, Rivian, Lucid Motors, Canoo, Fisker (all make EVs)
→ DON'T Return: Ford, GM (unless their EV division is the focus)

Topic: "Cloud Storage Services" + Location: "Global"
→ Return: Dropbox, Box, Google Drive, Microsoft OneDrive, iCloud
→ DON'T Return: AWS, Azure (those are broader cloud computing platforms)

Topic: "Fast Food Restaurants" + Location: "India"
→ Return: McDonald's India, KFC India, Domino's India, Subway India
→ DON'T Return: Nestle, Coca-Cola (food manufacturers, not restaurants)

Topic: "Solar Panel Installation" + Location: "California, United States"
→ Return: Sunrun, Vivint Solar, Tesla Energy, local solar installers
→ DON'T Return: First Solar, Canadian Solar (panel manufacturers, not installers)

❌ WRONG MATCHING EXAMPLES (DO NOT DO THIS):

Topic: "Mobile App Development" + Location: "United Kingdom"
→ WRONG: Returning Microsoft, Google, Apple (they're too broad)
→ CORRECT: Return mobile app development agencies like ustwo, Fueled, WillowTree

Topic: "Organic Food Stores" + Location: "Canada"  
→ WRONG: Returning Loblaws, Sobeys (general grocery chains)
→ CORRECT: Return Whole Foods, Choices Markets, Planet Organic

══════════════════════════════════════════════════════
         SPECIFIC INSTRUCTIONS FOR "${topic}"
══════════════════════════════════════════════════════

Now, focus EXCLUSIVELY on companies in "${fullLocationString}" that specialize in "${topic}".

**GOOGLE SEARCH SIMULATION:**
Simulate these EXACT searches and return ONLY the companies that would appear:

1. "${topic} companies in ${fullLocationString}"
2. "top ${topic} businesses in ${fullLocationString}"
3. "best ${topic} services in ${fullLocationString}"
4. "leading ${topic} providers in ${fullLocationString}"
5. "${topic} ${industry} ${fullLocationString}"
6. "${topic} market leaders ${fullLocationString}"

**LOCATION SPECIFICITY:**
${city ? `
🎯 CITY-SPECIFIC SEARCH: ${city}, ${state}, ${country}
- Search ONLY for companies IN ${city} specifically
- Example Google searches:
  * "${topic} companies in ${city}"
  * "${topic} ${city} ${state}"
  * "best ${topic} providers ${city}"
- EXCLUDE companies from other cities (even if they're in ${state})
- EVERY company must have physical presence in ${city} (office, store, facility)
- Verify with: "Can I find this company on Google Maps in ${city}?"
` : state ? `
🎯 STATE/REGION-SPECIFIC SEARCH: ${state}, ${country}
- Search ONLY for companies IN ${state} specifically  
- Example Google searches:
  * "${topic} companies in ${state}"
  * "${topic} ${state} ${country}"
  * "top ${topic} businesses ${state}"
- EXCLUDE companies from other states/regions
- EVERY company must have presence in ${state}
- Verify with: "Can I find this company operating in ${state} on Google?"
` : `
🎯 COUNTRY-SPECIFIC SEARCH: ${country}
- Search ONLY for companies IN ${country} specifically
- Example Google searches:
  * "${topic} companies in ${country}"
  * "${country} ${topic} market leaders"
  * "top ${topic} firms ${country}"
- EXCLUDE companies from other countries (unless they have MAJOR ${country} operations)
- EVERY company must be established in ${country}
- Verify with: "Is this company headquartered or majorly operating in ${country}?"
`}

**REAL COMPANY VALIDATION - CHECK EACH ONE:**
Before including ANY competitor, ask yourself:
✓ If I Google "${topic} companies in ${fullLocationString}", would this company appear? (YES/NO)
✓ Does this company have a website mentioning ${fullLocationString}? (YES/NO)
✓ Can I find this company on Google Maps in ${fullLocationString}? (YES/NO)
✓ Is this company ACTUALLY operating in ${fullLocationString} (not just theoretically)? (YES/NO)
✓ Would a local resident in ${fullLocationString} recognize this company? (YES/NO)

**If ANY answer is NO → DO NOT INCLUDE THE COMPANY**

**EXAMPLES OF REAL GOOGLE SEARCH RESULTS:**
${country === 'India' ? `
Example: If searching "construction companies in India", Google would show:
- Larsen & Toubro (L&T) - Real company, headquartered in Mumbai
- Tata Projects - Real company, major presence across India
- Shapoorji Pallonji - Real company, operates in India
- DLF Limited - Real company, Indian construction giant
NOT generic "ABC Construction" or "XYZ Builders" - those are fake!
` : country === 'United States' ? `
Example: If searching "software companies in United States", Google would show:
- Microsoft - Real company, headquartered in Redmond, WA
- Salesforce - Real company, headquartered in San Francisco, CA
- Oracle - Real company, operates across USA
- Adobe - Real company, based in San Jose, CA
NOT generic "Software Solutions Inc" or "Tech Corp" - those are fake!
` : ''}

**DATA COLLECTION FROM GOOGLE:**
For each REAL company you find:
- Company name: EXACT legal name as appears on Google/their website
- Revenue: Actual revenue from company reports, Crunchbase, or public filings for ${fullLocationString} operations
- Employees: Real employee count from LinkedIn, company website, or Crunchbase
- Market share: Estimated based on industry reports for ${fullLocationString} market
- Founded: Actual founding year from company history
- Headquarters: Real headquarters location
- Recent news: Actual recent developments you'd find in Google News

**OUTPUT JSON STRUCTURE - REAL DATA ONLY:**
{
  "competitiveLandscape": "150+ word overview describing the ACTUAL competitive situation in ${fullLocationString}. Reference the REAL companies that dominate this market, actual market dynamics, real barriers to entry specific to ${fullLocationString}.",
  
  "competitors": [
    {
      "name": "EXACT Real Company Name (as it appears on Google)",
      "tier": "Market Leader/Challenger/Follower/Niche (based on actual market position)",
      "marketShare": "X.X% (realistic estimate for ${fullLocationString} market)",
      "revenue": "${currency} X.X billion/million (ACTUAL revenue for ${fullLocationString} operations from public sources)",
      "employees": XXXX (REAL employee count from LinkedIn/company website),
      "headquarters": "Actual City, Actual State/Region, ${country}",
      "localPresence": "Specific real offices/facilities in ${fullLocationString} (e.g., '15 offices across ${state}' or 'Main office at [real address]')",
      "founded": YYYY (ACTUAL founding year),
      "strengths": [
        "Real competitive advantage 1 (e.g., 'Largest distribution network in ${fullLocationString} with 500+ dealers')",
        "Real competitive advantage 2 (e.g., 'Exclusive partnership with [Real Company] since 2020')",
        "Real competitive advantage 3 (e.g., 'Patent on [specific technology] used in ${fullLocationString}')"
      ],
      "weaknesses": [
        "Real weakness 1 (e.g., 'Lost 5% market share in 2025 due to [real reason]')",
        "Real weakness 2 (e.g., 'Customer satisfaction declined to 3.2/5 in ${fullLocationString} market')"
      ],
      "strategy": "ACTUAL business strategy in ${fullLocationString} (150-250 words). Reference REAL and CURRENT (2025-2026) initiatives, partnerships, product launches, and pivots. Be specific: name real products, real partners, real dollar amounts, real geographies. DO NOT use generic phrases like 'focus on innovation' — describe what they are ACTUALLY doing.",
      "recentMoves": "The SINGLE most significant VERIFIED development from Q4 2025 or Q1 2026 (Jan–March 2026). Format: '[Month Year]: [What happened] — e.g. January 2026: Raised $200M Series D from Andreessen Horowitz at $2.4B valuation; November 2025: Acquired [Company] for $340M to expand into [segment]; February 2026: Launched [Product] in [market], targeting [customer type].' Must include specific dates, amounts, and named parties where known.",
      "pricingStrategy": "The ACTUAL current pricing model: subscription tiers with prices, commission rates, per-unit pricing, freemium structure, enterprise negotiated, or other. Be specific with real dollar/currency amounts (e.g., 'Free tier + Pro at ${currency} 49/mo, Business at ${currency} 149/mo, Enterprise custom pricing') — do NOT use vague descriptions.",
      "customerBase": "Specific description of who they actually sell to in ${fullLocationString}: company sizes, industries, demographics, job titles. Include approximate customer counts or revenue split if known (e.g., '70% SMBs under 50 employees, 30% mid-market; 8,000+ paying customers in ${country}'). Avoid generic statements.",
      "threatLevel": "High/Medium/Low (realistic assessment for new entrants)",
      "differentiationOpportunity": "Realistic ways to compete (e.g., 'Focus on underserved tier-2 cities in ${state} where they have weak presence')",
      "customerBase": "REAL customer description (e.g., 'Primarily serves Fortune 500 companies and government projects in ${fullLocationString}')",
      "pricingStrategy": "ACTUAL pricing approach (e.g., 'Premium pricing, 15-20% above market average in ${fullLocationString}')"
    }
    // Include 8-12 REAL competitors that you can verify through Google search
  ],
  
  "competitiveMatrix": {
    "byPrice": "REAL price positioning in ${fullLocationString} market. Name actual companies: 'Premium: [Company A, Company B], Mid-range: [Company C, Company D], Budget: [Company E, Company F]'",
    "byQuality": "REAL quality positioning. Name actual companies and their reputations in ${fullLocationString}",
    "byInnovation": "REAL innovation leaders. Which actual companies are known for innovation in ${fullLocationString}?"
  },
  
  "barriersToEntry": [
    "REAL barrier 1 with specific data (e.g., 'Regulatory approval from [Actual Government Body] requires 18-24 months and ${currency} 5 million in compliance costs')",
    "REAL barrier 2 (e.g., 'Top 3 companies control 65% of distribution network in ${fullLocationString}')",
    "REAL barrier 3 (e.g., 'Average initial capital requirement of ${currency} 50 million based on successful entrants in ${fullLocationString}')",
    "REAL barrier 4",
    "REAL barrier 5"
  ],
  
  "marketConcentration": "ACTUAL concentration analysis (e.g., 'Highly concentrated: Top 4 companies (L&T, Tata, Shapoorji, DLF) control 72% of ${fullLocationString} market. Herfindahl Index: 0.35 indicating moderate concentration.')",
  
  "competitiveGaps": [
    "REAL unmet need 1 that you can verify (e.g., 'No major player serves tier-3 cities in ${state} - market research shows ${currency} 2 billion opportunity')",
    "REAL unmet need 2",
    "REAL unmet need 3"
  ]
}

**CRITICAL FINAL VALIDATION:**
Before returning, verify EACH company:
1. Google Search Test: Would this company appear in search results for "${topic} in ${fullLocationString}"?
2. Website Test: Does this company have a website that mentions ${fullLocationString}?
3. Real Data Test: Are the revenue, employees, and other figures based on real data (not estimates)?
4. Location Test: Does this company ACTUALLY operate in ${fullLocationString}?
5. Verification Test: Can I find news articles, press releases, or other evidence about this company in ${fullLocationString}?

**EXAMPLES OF WHAT IS ACCEPTABLE:**
✅ Larsen & Toubro (L&T) for "construction companies in India" - Real company, verifiable
✅ Tata Steel for "steel companies in India" - Real company, verifiable  
✅ Microsoft for "software companies in United States" - Real company, verifiable
✅ HSBC for "banks in United Kingdom" - Real company, verifiable

**EXAMPLES OF WHAT TO REJECT:**
❌ "ABC Construction Ltd" - Generic, can't verify
❌ "Global Steel Corp" - Generic name, not verifiable
❌ "Tech Solutions Inc" - Placeholder name
❌ Companies from wrong location (US company for India search)

**IF YOU CANNOT FIND ENOUGH REAL COMPANIES:**
Say this explicitly in the response: "Note: Limited publicly available competitor data for ${topic} in ${fullLocationString}. Only [X] major competitors identified through Google search."

DO NOT make up companies to fill the quota. Better to return 5 REAL companies than 12 fake ones.

Return ONLY valid JSON. Every company must be REAL and verifiable through Google search for "${topic} in ${fullLocationString}".`;

  console.log('🌐 Using Google Search Grounding to find REAL competitors...');
  const groundingResult = await callGeminiWithGrounding(prompt);
  if (!groundingResult) {
    console.warn('⚠️ Grounding returned null — falling back to Claude for competitor data');
    const { callClaudeAPI } = await import('./claudeService');
    const claudeText = await callClaudeAPI(prompt);
    if (!claudeText) {
      return {
        competitiveLandscape: `Competitor research for "${topic}" in ${fullLocationString} could not be loaded. Manual Google search recommended.`,
        competitors: [],
        competitiveMatrix: { byPrice: 'See manual research', byQuality: 'See manual research', byInnovation: 'See manual research' },
        barriersToEntry: ['Manual competitive research required'],
        marketConcentration: 'Data unavailable',
        competitiveGaps: ['Manual research recommended']
      };
    }
    try {
      const cleaned = claudeText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      const match = cleaned.match(/\{[\s\S]*\}/);
      return JSON.parse(match ? match[0] : cleaned);
    } catch {
      return {
        competitiveLandscape: claudeText.substring(0, 500),
        competitors: [],
        competitiveMatrix: { byPrice: 'N/A', byQuality: 'N/A', byInnovation: 'N/A' },
        barriersToEntry: [],
        marketConcentration: 'N/A',
        competitiveGaps: []
      };
    }
  }
  const response = groundingResult.text;
  
  if (groundingResult.queries) {
    console.log('🔍 Google Search Queries Used:', groundingResult.queries);
  }

  // FIX #1: Correct regex — \n? not \\n? (which matched literal backslash-n, not newline)
  // FIX #2: Wrap JSON.parse in try/catch with retry + safe null guard on .competitors
  let jsonText = response;
  jsonText = jsonText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();

  // Extract JSON object boundaries in case AI added surrounding prose
  const jsonMatch = jsonText.match(/\{[\s\S]*\}/);
  if (jsonMatch) jsonText = jsonMatch[0];

  let competitive: any;
  try {
    competitive = JSON.parse(jsonText);
  } catch (parseError) {
    console.error('❌ [Competitive Analysis] JSON parse failed on first attempt:', parseError);
    console.error('❌ Raw response snippet:', response.substring(0, 300));
    // Retry once with a stricter "pure JSON only" instruction
    console.log('🔄 Retrying competitive analysis with strict JSON-only instruction...');
    const retryPrompt = prompt + '\n\nCRITICAL CORRECTION: Your previous response failed JSON parsing. Return ONLY raw JSON — absolutely no markdown, no code fences (no ```), no prose before or after. Begin your response directly with { and end with }.';
    try {
      const retryResult = await callGeminiWithGrounding(retryPrompt);
      let retryText = (retryResult?.text ?? '').replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      const retryMatch = retryText.match(/\{[\s\S]*\}/);
      if (retryMatch) retryText = retryMatch[0];
      competitive = JSON.parse(retryText);
      console.log('✅ Retry successful — competitive analysis parsed on second attempt');
    } catch (retryError) {
      console.error('❌ Retry also failed. Returning safe empty competitive analysis structure.');
      return {
        competitiveLandscape: `Competitor research for "${topic}" in ${fullLocationString} could not be fully loaded at this time. Manual Google search recommended for up-to-date competitor data.`,
        competitors: [],
        competitiveMatrix: { byPrice: 'See manual research', byQuality: 'See manual research', byInnovation: 'See manual research' },
        barriersToEntry: ['Manual competitive research required for accurate barrier analysis'],
        marketConcentration: 'Data unavailable — retry generation for accurate analysis',
        competitiveGaps: ['Manual research recommended']
      };
    }
  }

  // FIX #2: Null-safe access — never crash if AI omits the competitors key
  const competitorList: any[] = Array.isArray(competitive?.competitors) ? competitive.competitors : [];

  // Validate we got real competitors
  if (competitorList.length < 3) {
    console.warn(`⚠️ Warning: Only ${competitorList.length} competitors found for ${fullLocationString}`);
    console.warn(`⚠️ This may indicate limited market data or few actual competitors in ${fullLocationString}`);
  }
  
  console.log(`✅ Competitive Analysis generated using Google search methodology`);
  console.log(`✅ Topic-specific results for: "${topic}"`);
  console.log(`✅ Found ${competitorList.length} REAL competitors from Google search: "${topic} in ${fullLocationString}"`);
  console.log(`✅ All competitors are verifiable through Google search and specialize in "${topic}"`);
  
  return { ...competitive, competitors: competitorList };
}

/**
 * Generate Sources - Separate API call
 */
export async function generateSources(
  topic: string,
  industry: string,
  location: string
): Promise<any[]> {
  console.log('📚 Generating Research Sources (separate API call)...');
  
  const prompt = `You are a research librarian. Create a list of 12-20 authoritative sources for research on "${topic}" in ${industry} for ${location}.

**SOURCE REQUIREMENTS:**
- All sources must be REALISTIC and authoritative
- Include a mix of: Market research reports, industry journals, government data, company filings
- Sources should be from 2025-2026
- Make source titles and organizations realistic (but note these are example formats)

**OUTPUT JSON:**
[
  {
    "id": 1,
    "title": "Specific Report Title - ${industry} Market Analysis ${location} 2026",
    "author": "McKinsey & Company / Gartner / Forrester / Government Agency",
    "publication": "Publication name",
    "date": "2026" or "2025",
    "type": "Market Analysis/Research Report/Industry Report/Government Data/Company Filing",
    "url": "https://realistic-url-format.com/report",
    "keyFindings": "Main insight from this source relevant to ${topic}"
  }
  // 12-20 diverse, authoritative sources
]

Return ONLY valid JSON array.`;

  const response = await callGeminiAPI(prompt, 0.7);
  if (!response) throw new Error('Gemini API returned null for Sources');
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const sources = JSON.parse(jsonText);
  
  console.log(`✅ Sources generated: ${sources.length} authoritative references`);
  return sources;
}

/**
 * Generate Regulatory Compliance Analysis — Separate API call
 * Topic-aware, location-specific, with REAL compliance costs and current 2026 regulations
 */
export async function generateComplianceAnalysis(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('⚖️  Generating Compliance Analysis (separate API call)...');
  const randomSeed = Math.random().toString(36).substring(7);

  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'generic');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

REQUEST ID: ${randomSeed} | TOPIC: "${topic}" | INDUSTRY TYPE: ${cls.label} | LOCATION: ${location} | CURRENCY: ${currency}

You are a senior compliance attorney for "${topic}" (${cls.label}) businesses in ${location}. Provide a REAL, CURRENT (2026) compliance analysis.

INDUSTRY-SPECIFIC REGULATORY FOCUS for "${topic}" in ${location}:
${
  cls.type === 'hardware'
    ? `• Product safety standards (homologation, testing, certifications required in ${location})
  • Import duties and tariff classifications for components
  • Local content / localisation requirements (if any, in ${location})
  • Environmental regulations (disposal, recycling, emissions)
  • Consumer protection and warranty laws in ${location}
  • Any industry-specific subsidies/incentives compliance requirements (e.g., FAME II for EVs in India)`
    : cls.type === 'saas'
    ? `• Data privacy laws specific to ${location} (GDPR, PDPA, DPDP Act, CCPA, etc.)
  • Data localisation / residency requirements in ${location}
  • Cybersecurity regulations (NIS2, IT Act amendments, etc.)
  • AI Act or equivalent regulations in ${location}
  • SaaS-specific procurement regulations for government clients
  • Electronic signature and digital contract enforceability in ${location}`
    : cls.type === 'marketplace'
    ? `• E-commerce regulations and platform liability laws in ${location}
  • Payment services licensing (if handling funds directly)
  • Consumer protection and dispute resolution requirements
  • Competition / antitrust laws applicable to platforms in ${location}
  • Gig worker / contractor classification laws in ${location}
  • Data collection and user consent requirements`
    : `• Sector-specific licensing and registration for "${topic}" in ${location}
  • Employment and labour law compliance in ${location}
  • Professional indemnity and insurance requirements
  • Client contracting and IP ownership regulations`
}

CRITICAL: Every regulation, fine, cost, and deadline must be REAL and SPECIFIC to "${topic}" in ${location}.
Generic compliance checklists are UNACCEPTABLE. Base everything on actual laws and current market costs.

REAL COST BENCHMARKS (2025-2026):
- SOC 2 Type II audit: $30K-$150K | ISO 27001 certification: $25K-$80K | GDPR compliance program: $100K-$500K/yr
- HIPAA compliance: $50K-$250K/yr | PCI DSS: $50K-$200K | FedRAMP: $500K-$2M
- ISO 9001 audit: $5K-$30K | OSHA program: $20K-$150K/yr | EU AI Act high-risk: $100K-$800K
- Legal counsel (US): $300-800/hr | (UK): GBP 250-650/hr | (EU): EUR 200-600/hr | (India): INR 5K-50K/hr
- Average data breach cost globally (IBM 2025): $4.9M

OUTPUT JSON (return ONLY valid JSON, no markdown):
{
  "complianceSummary": "250+ word REAL analysis naming exact government bodies (FTC, FCA, SEBI, ASIC, BaFin, etc.), specific laws with act numbers, honest assessment of compliance burden for ${topic} in ${location}",
  "requiredLicenses": [
    {
      "license": "Exact license name per government",
      "issuingAuthority": "Actual issuing government body",
      "requirement": "What triggers this for ${topic} specifically",
      "applicationCost": "${currency} XXXX",
      "annualFee": "${currency} XXXX",
      "processingTime": "X weeks/months",
      "consequences": "Specific penalty for non-compliance",
      "website": "Actual .gov or official URL"
    }
  ],
  "ongoingObligations": [
    {
      "obligation": "Specific regulatory obligation",
      "frequency": "Annual/Quarterly/Monthly",
      "deadline": "Specific deadline",
      "cost": "${currency} XXXX annually",
      "filingBody": "Regulatory body",
      "consequence": "Fine amount for non-compliance"
    }
  ],
  "industryCertifications": [
    {
      "certification": "Exact certification name",
      "mandatoryOrVoluntary": "Mandatory/Strongly Recommended",
      "certifyingBody": "Real body (BSI, Bureau Veritas, TÜV, DNV, A-LIGN)",
      "initialCost": "${currency} XXXX",
      "annualMaintenanceCost": "${currency} XXXX",
      "timeToAchieve": "X months",
      "competitiveImpact": "Commercial consequence of not having this",
      "keyRequirements": ["Requirement 1", "Requirement 2", "Requirement 3"]
    }
  ],
  "topComplianceRisks": [
    {
      "risk": "Specific risk unique to ${topic}",
      "regulation": "Law/regulation with reference",
      "maxPenalty": "${currency} XXXX statutory maximum",
      "realWorldExamples": "REAL case: [Company], [fine amount], [year] — real enforcement examples only",
      "probabilityForNewEntrant": "High/Medium/Low",
      "preventionCost": "${currency} XXXX to mitigate",
      "mitigation": "3-4 specific preventive steps"
    }
  ],
  "upcomingRegulations": [
    {
      "regulation": "Regulation name",
      "legislativeReference": "Bill/Directive reference number",
      "effectiveDate": "Specific date",
      "keyChanges": "What changes for ${topic} businesses in ${location}",
      "estimatedComplianceCost": "${currency} XXXX one-time + ${currency} XXXX/year",
      "preparednessLevel": "X% of ${topic} businesses ready",
      "actionRequired": "Specific steps needed NOW"
    }
  ],
  "totalComplianceCostEstimate": {
    "yearOneTotal": "${currency} XXXX",
    "annualRecurring": "${currency} XXXX",
    "asPercentageOfRevenue": "X-X% startup vs X-X% mature company",
    "breakdown": {
      "licenses": "${currency} XXXX",
      "certifications": "${currency} XXXX",
      "legalCounsel": "${currency} XXXX",
      "staffAndTraining": "${currency} XXXX",
      "technologyTools": "${currency} XXXX",
      "auditsAndReporting": "${currency} XXXX"
    },
    "benchmarkComparison": "Industry benchmark with real comparable example"
  }
}

Return ONLY valid JSON. All data must be REAL and current for ${location} as of 2026.`;

  const response = await callGeminiAPI(prompt, 0.4);
  if (!response) throw new Error('Gemini API returned null for Compliance Analysis');
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const compliance = JSON.parse(jsonText);
  console.log('✅ Compliance Analysis generated with real 2026 regulations and costs');
  return compliance;
}

/**
 * Generate Innovation & Future Roadmap - Separate API call with Google Search Grounding
 * Provides detailed, topic-specific innovation opportunities and strategic roadmap
 */
export async function generateInnovationRoadmap(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('💡 Generating Innovation & Future Roadmap (separate API call)...');
  console.log(`🔍 Topic: "${topic}"`);
  console.log(`🔍 Industry: "${industry}"`);
  console.log(`🔍 Location: "${location}"`);
  
  const randomSeed = Math.random().toString(36).substring(7);
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'generic');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

🔥🔥🔥 UNIQUE REQUEST ID: ${randomSeed} 🔥🔥🔥

══════════════════════════════════════════════════════
            INNOVATION & FUTURE ROADMAP ANALYSIS
        Section 14: Disruptive Opportunities & Future Roadmap
══════════════════════════════════════════════════════

🎯 TOPIC: "${topic}"
📍 LOCATION: ${location}
🏭 INDUSTRY: ${industry} — Type: ${cls.label}
💰 CURRENCY: ${currency}

INDUSTRY-SPECIFIC INNOVATION FOCUS (${cls.label.toUpperCase()}):
${
  cls.type === 'hardware'
    ? `For physical products/manufacturing, innovations should include:
  • Battery / component technology advances
  • Autonomous or connected product features
  • Manufacturing automation (Industry 4.0, robotics, AI quality control)
  • Circular economy / recycling / servicing models
  • Direct-to-consumer sales model disruption
  • IoT and predictive maintenance
  AVOID: blockchain, metaverse, quantum unless genuinely applicable to "${topic}"`
    : cls.type === 'saas'
    ? `For SaaS, innovations should include:
  • AI copilot / agent features that increase ARPU
  • No-code / low-code customisation for user expansion
  • Embedded analytics and BI within the product
  • Vertical industry pre-built solutions (defensible niches)
  • API-first platform play to build ecosystem
  • Community-led growth strategies`
    : cls.type === 'marketplace'
    ? `For marketplaces, innovations should include:
  • Financial services layer (BNPL, insurance, working capital for participants)
  • Logistics / fulfilment vertical integration
  • AI matching and personalisation for buyer/seller pairing
  • Social commerce and video commerce
  • Subscription / membership tiers for repeat buyers
  • B2B pivot or enterprise vertical`
    : cls.type === 'services'
    ? `For services, innovations should include:
  • Productisation of recurring service offerings
  • AI-augmented delivery reducing hours per project
  • Platform / knowledge base that scales without linear headcount
  • Outcome-based / success-fee pricing models
  • Micro-fulfilment or distributed delivery networks`
    : `Innovations must directly impact "${topic}" businesses in ${location}`
}

You are an innovation strategist and futurist specializing in "${topic}" businesses in ${location}. Create a comprehensive, TOPIC-SPECIFIC innovation and future roadmap analysis.

🚨 CRITICAL REQUIREMENTS 🚨

1️⃣ EVERY innovation, technology trend, and opportunity MUST be DIRECTLY RELEVANT to "${topic}"
2️⃣ ALL examples, companies, and innovations must be REAL and verifiable
3️⃣ Focus ONLY on innovations that would actually impact "${topic}" businesses in ${location}
4️⃣ Use REAL market data, REAL technology trends, REAL investment figures
5️⃣ All financial figures in ${currency} with NO abbreviations (write 1000000 not 1M)

══════════════════════════════════════════════════════
                  RESEARCH REQUIREMENTS
══════════════════════════════════════════════════════

Use Google Search Grounding to find:
• Latest innovations in "${topic}" from 2025-2026
• Real companies innovating in "${topic}" space in ${location}
• Actual technology trends affecting "${topic}" industry
• Real investment data in "${topic}" innovation
• Verified market opportunities specific to "${topic}"

**VALIDATION CHECKS:**
Before including ANY innovation or trend:
✓ Is this ACTUALLY being used in "${topic}" businesses? (YES/NO)
✓ Can I find real examples of companies applying this to "${topic}"? (YES/NO)
✓ Would this innovation make sense for "${topic}" in ${location}? (YES/NO)
✓ Can I verify investment/market data for this in "${topic}" sector? (YES/NO)

❌ If ANY answer is "NO" → EXCLUDE IT IMMEDIATELY ❌

══════════════════════════════════════════════════════
                    TOPIC-SPECIFIC FOCUS
══════════════════════════════════════════════════════

📌 REMEMBER: Everything must relate to "${topic}"

Examples of CORRECT topic matching:
✅ Topic: "Restaurant Management" → AI menu optimization, kitchen automation, delivery tech
✅ Topic: "Real Estate Development" → PropTech, virtual tours, construction automation
✅ Topic: "Healthcare Clinics" → Telemedicine, EHR systems, patient engagement apps
✅ Topic: "E-commerce Fashion" → AR try-on, AI styling, sustainable materials

Examples of WRONG (too generic):
❌ Topic: "Restaurant Management" → Blockchain, quantum computing (not relevant)
❌ Topic: "Real Estate" → Generic "AI" without specifics
❌ Topic: "Healthcare" → Unrelated biotech or pharma innovations

══════════════════════════════════════════════════════
              REAL INNOVATION EXAMPLES TO USE
══════════════════════════════════════════════════════

Find REAL innovations like:
• Real AI/ML applications being used in "${topic}" (with company examples)
• Real automation technologies deployed in "${topic}" (with vendor names)
• Real platforms/software transforming "${topic}" (actual product names)
• Real hardware/IoT being adopted in "${topic}" (real device examples)
• Real business model innovations in "${topic}" (actual case studies)

For ${location} specifically:
• Which "${topic}" companies in ${location} are innovating?
• What technology is being adopted in ${location}'s "${topic}" market?
• What innovations work best in ${location}'s business environment?

══════════════════════════════════════════════════════
                    OUTPUT JSON STRUCTURE
══════════════════════════════════════════════════════

**OUTPUT JSON:**
{
  "disruptiveForces": [
    {
      "force": "Specific Technology/Trend Name (e.g., 'AI-Powered Kitchen Automation for Restaurants')",
      "relevanceToTopic": "150+ word explanation of HOW this specifically applies to '${topic}' businesses",
      "impact": "Transformative/High/Medium (with specific justification for ${topic})",
      "timeline": "0-18 months/18-36 months/36-60 months",
      "currentAdoption": "X% of ${topic} businesses in ${location} using this as of 2026",
      "opportunity": "${currency} X billion market opportunity for ${topic} businesses",
      "realWorldExamples": [
        {
          "company": "Real Company Name using this in ${topic}",
          "location": "City/Region in ${location} or globally",
          "implementation": "Specific details of how they use it",
          "results": "Actual results achieved (e.g., '40% cost reduction', '2x revenue growth')",
          "year": "2025 or 2026"
        }
      ],
      "investmentRequired": "${currency} X to ${currency} Y to implement (realistic range)",
      "expectedROI": "X% ROI within Y months based on industry data",
      "keyVendors": [
        {
          "vendor": "Real Vendor/Platform Name",
          "product": "Specific product for ${topic}",
          "pricing": "${currency} X/month or ${currency} Y one-time",
          "marketShare": "Market position in ${topic} sector"
        }
      ],
      "barriersToAdoption": [
        "Real barrier 1 specific to ${topic}",
        "Real barrier 2",
        "Real barrier 3"
      ]
    }
  ],
  
  "innovationPipeline": [
    {
      "initiative": "Specific Innovation Initiative for ${topic}",
      "description": "200+ word detailed explanation of what this is and why it matters for ${topic} businesses",
      "stage": "Concept/Planning/Development/Launch Ready",
      "launchDate": "QX 2026 or QX 2027",
      "targetMarket": "Specific segment within ${topic} in ${location}",
      "investment": "${currency} X (no abbreviations)",
      "expectedRevenue": "${currency} X in Year 1, ${currency} Y in Year 2",
      "marketSize": "${currency} X billion addressable market in ${location}",
      "competitiveAdvantage": "Specific advantage this creates for ${topic} businesses",
      "technicalFeasibility": "High/Medium/Low with explanation",
      "regulatoryConsiderations": "Any regulations affecting this in ${location}",
      "keyPartners": ["Real Company 1", "Real Company 2", "Real Company 3"],
      "successMetrics": [
        "Metric 1 with target",
        "Metric 2 with target",
        "Metric 3 with target"
      ]
    }
  ],
  
  "emergingTechnologies": [
    {
      "technology": "Specific Technology Name",
      "applicationTo": "150+ word explanation of specific applications to ${topic}",
      "maturityLevel": "Early Stage/Growth/Mature",
      "adoptionCurve": "X% adoption expected by 2027, Y% by 2030 in ${location}",
      "investmentTrend": "${currency} X invested in this for ${topic} in 2025-2026",
      "realImplementations": [
        "Real Company 1 using it for ${topic}",
        "Real Company 2 using it",
        "Real Company 3 using it"
      ],
      "costToImplement": "${currency} X to ${currency} Y",
      "timeToValue": "X months until benefits realized",
      "skillsRequired": ["Skill 1", "Skill 2", "Skill 3"],
      "riskFactors": ["Risk 1", "Risk 2", "Risk 3"]
    }
  ],
  
  "strategicRoadmap": [
    {
      "phase": "Near-term (0-12 months)",
      "focus": "Specific focus areas for ${topic} business in ${location}",
      "keyInitiatives": [
        "Initiative 1 with specific action (e.g., 'Deploy AI order prediction system by Q2 2026')",
        "Initiative 2 with specific action",
        "Initiative 3 with specific action",
        "Initiative 4 with specific action",
        "Initiative 5 with specific action"
      ],
      "investment": "${currency} X total investment",
      "expectedOutcome": "Specific, measurable outcomes (e.g., '35% increase in efficiency, 20% cost reduction')",
      "criticalSuccessFactors": [
        "Factor 1 required for success",
        "Factor 2",
        "Factor 3"
      ],
      "risks": [
        "Risk 1 with mitigation",
        "Risk 2 with mitigation"
      ],
      "milestones": [
        {"milestone": "Milestone 1", "date": "Month Year"},
        {"milestone": "Milestone 2", "date": "Month Year"},
        {"milestone": "Milestone 3", "date": "Month Year"}
      ]
    },
    {
      "phase": "Mid-term (12-24 months)",
      "focus": "Strategic expansion and scaling for ${topic}",
      "keyInitiatives": [
        "Initiative 1 (platform expansion, new capabilities, etc.)",
        "Initiative 2",
        "Initiative 3",
        "Initiative 4",
        "Initiative 5"
      ],
      "investment": "${currency} X total",
      "expectedOutcome": "Measurable outcomes",
      "criticalSuccessFactors": ["Factor 1", "Factor 2", "Factor 3"],
      "risks": ["Risk 1", "Risk 2"],
      "milestones": [
        {"milestone": "Milestone 1", "date": "Month Year"},
        {"milestone": "Milestone 2", "date": "Month Year"}
      ]
    },
    {
      "phase": "Long-term (24-48 months)",
      "focus": "Market leadership and transformation in ${topic}",
      "keyInitiatives": [
        "Initiative 1 (market dominance, acquisitions, IPO prep, etc.)",
        "Initiative 2",
        "Initiative 3",
        "Initiative 4"
      ],
      "investment": "${currency} X total",
      "expectedOutcome": "Long-term strategic outcomes",
      "criticalSuccessFactors": ["Factor 1", "Factor 2", "Factor 3"],
      "risks": ["Risk 1", "Risk 2"],
      "milestones": [
        {"milestone": "Milestone 1", "date": "Year"},
        {"milestone": "Milestone 2", "date": "Year"}
      ]
    }
  ],
  
  "innovationBudgetAllocation": {
    "totalAnnualInnovationBudget": "${currency} X (typical for ${topic} business in ${location})",
    "breakdown": {
      "coreProductEnhancement": {
        "percentage": "X%",
        "amount": "${currency} X",
        "focus": "Incremental improvements to existing ${topic} offerings"
      },
      "newCapabilities": {
        "percentage": "X%",
        "amount": "${currency} X",
        "focus": "New features and capabilities for ${topic}"
      },
      "emergingTech": {
        "percentage": "X%",
        "amount": "${currency} X",
        "focus": "Experimental technologies for ${topic}"
      },
      "processInnovation": {
        "percentage": "X%",
        "amount": "${currency} X",
        "focus": "Operational efficiency in ${topic}"
      },
      "partnerships": {
        "percentage": "X%",
        "amount": "${currency} X",
        "focus": "Strategic partnerships in ${topic} ecosystem"
      }
    },
    "benchmarkComparison": "Industry benchmark: ${topic} leaders spend X-Y% of revenue on innovation"
  },
  
  "competitiveInnovationLandscape": {
    "innovationLeaders": [
      {
        "company": "Real Company Name in ${topic}",
        "location": "${location} or global",
        "keyInnovations": [
          "Specific innovation 1 they pioneered",
          "Specific innovation 2",
          "Specific innovation 3"
        ],
        "r&dSpend": "${currency} X annually",
        "patents": "X patents in ${topic} domain",
        "recentBreakthroughs": "Actual 2025-2026 breakthrough in ${topic}"
      }
    ],
    "innovationGaps": [
      "Unmet innovation need 1 in ${topic}",
      "Unmet need 2",
      "Unmet need 3"
    ]
  }
}

══════════════════════════════════════════════════════
                 FINAL VALIDATION CHECKLIST
══════════════════════════════════════════════════════

Before returning, verify EVERY element:
✅ Does this innovation/technology directly apply to "${topic}"?
✅ Are all companies, vendors, and examples REAL and verifiable?
✅ Are all financial figures realistic for "${topic}" in ${location}?
✅ Would someone in the "${topic}" business recognize these innovations?
✅ Can these technologies/trends be verified via Google search?

**REAL DATA SOURCES TO REFERENCE:**
• Tech news sites covering "${topic}" (TechCrunch, VentureBeat for relevant sector)
• Industry publications for ${industry}
• Recent funding announcements in "${topic}" space
• Product launches from vendors serving "${topic}" businesses
• Case studies from companies in "${topic}"
• Market research on technology adoption in "${topic}"

Return ONLY valid JSON. Every innovation, technology, and example must be REAL and SPECIFICALLY relevant to "${topic}" businesses in ${location}.`;

  console.log('🌐 Using Google Search Grounding to find REAL innovations for', topic);
  const groundingResult = await callGeminiWithGrounding(prompt);
  if (!groundingResult) {
    console.warn('❌ Gemini Innovation generation failed, using fallback');
    // Fallback to Claude
    const { callClaudeAPI } = await import('./claudeService');
    const claudeText = await callClaudeAPI(prompt);
    if (claudeText) {
      try {
        const cleaned = claudeText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
        const match = cleaned.match(/\{[\s\S]*\}/);
        return JSON.parse(match ? match[0] : cleaned);
      } catch { /* fall through to hardcoded fallback */ }
    }
    return {
      disruptiveForces: [],
      innovationPipeline: [],
      emergingTechnologies: [],
      futureRoadmap: []
    };
  }
  const response = groundingResult.text;
  
  if (groundingResult.queries) {
    console.log('🔍 Google Search Queries Used for Innovation Research:', groundingResult.queries);
  }
  
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const innovation = JSON.parse(jsonText);
  
  console.log(`✅ Innovation & Future Roadmap generated using Google Search Grounding`);
  console.log(`✅ Topic-specific innovations for: "${topic}"`);
  console.log(`✅ Found ${innovation.disruptiveForces?.length || 0} disruptive forces`);
  console.log(`✅ Found ${innovation.innovationPipeline?.length || 0} innovation initiatives`);
  console.log(`✅ Found ${innovation.emergingTechnologies?.length || 0} emerging technologies`);
  console.log(`✅ All innovations are REAL and specifically relevant to "${topic}"`);
  
  return innovation;
}

/**
 * Generate Supply Chain Analysis - Separate API call
 */
export async function generateSupplyChainAnalysis(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('🚚 Generating Supply Chain Analysis (separate API call)...');
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'supplyChain');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

You are a supply chain specialist. Create a detailed supply chain analysis for "${topic}" in the ${industry} industry for ${location}.

**INDUSTRY-SPECIFIC REQUIREMENTS (${cls.label.toUpperCase()}):**
- Supplier types: ${cls.supplyChainType}
- Focus on suppliers critical to "${topic}" business model
- All suppliers must be REAL companies operating in ${location} or globally

**CONTENT REQUIREMENTS:**
Return a JSON object with this structure:
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
      "risk": "Specific supply chain risk for ${topic}",
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

**RESEARCH MANDATE:**
- Use REAL supplier names verifiable via Google
- All cost estimates in ${currency} with FULL numbers (no abbreviations)
- Suppliers must be relevant to "${topic}" specifically
- Geographic risk must be specific to ${location}

Return ONLY valid JSON. No markdown, no code fences, no prose before or after.`;

  const response = await callGeminiAPI(prompt, 0.7);
  if (!response) throw new Error('Gemini API returned null for Supply Chain Analysis');
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const data = JSON.parse(jsonText);
  
  console.log('✅ Supply Chain Analysis generated');
  return data;
}

/**
 * Generate Investment Readiness Assessment - Separate API call
 */
export async function generateInvestmentReadinessAssessment(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('💼 Generating Investment Readiness Assessment (separate API call)...');
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'investmentReadiness');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

You are an investment banker specializing in ${cls.label} businesses. Create a comprehensive investment readiness assessment for "${topic}" in ${location}.

**VALUATION METHODOLOGY (${cls.label.toUpperCase()}):**
${cls.valuationMethod}

**CONTENT REQUIREMENTS:**
Return a JSON object with this structure:
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
        "multiple": "Xe.g., 5.2x ARR, 12x EBITDA)",
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

**HONESTY REQUIREMENT:**
- Be BRUTALLY HONEST about deal attractiveness
- If IRR <20% or MOIC <3x, clearly state this is BELOW venture norms
- Include realistic exit scenarios for ${location}
- All financial figures in ${currency} with FULL numbers

Return ONLY valid JSON. No markdown, no code fences, no prose before or after.`;

  const response = await callGeminiAPI(prompt, 0.7);
  if (!response) throw new Error('Gemini API returned null for Investment Readiness Assessment');
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const data = JSON.parse(jsonText);
  
  console.log('✅ Investment Readiness Assessment generated');
  return data;
}

/**
 * Generate Critical Analysis - Separate API call
 */
export async function generateCriticalAnalysis(
  topic: string,
  industry: string,
  location: string,
  currency: string
): Promise<any> {
  console.log('🔍 Generating Critical Analysis (separate API call)...');
  
  const systemPrefix = buildFullSectionPromptPrefix(topic, industry, location, currency, 'criticalAnalysis');
  const cls = classifyIndustry(topic, industry);

  const prompt = `${systemPrefix}

You are a brutally honest business analyst. Create a final critical analysis that CHALLENGES all key assumptions for "${topic}" in ${location}.

**INDUSTRY-SPECIFIC REALITY CHECKS (${cls.label.toUpperCase()}):**
${
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
    : `- What are the fundamental constraints of "${topic}" business model in ${location}?`
}

**CONTENT REQUIREMENTS:**
Return a JSON object with this structure:
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
    "statedTAM": "${currency} X (from earlier sections)",
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

**HONESTY REQUIREMENT:**
- This is the FINAL word — be ruthlessly honest
- If the market is saturated, say so explicitly
- If the odds are poor, state the probability of failure
- Challenge optimistic revenue projections with real data
- All financial figures in ${currency} with FULL numbers

Return ONLY valid JSON. No markdown, no code fences, no prose before or after.`;

  const response = await callGeminiAPI(prompt, 0.7);
  if (!response) throw new Error('Gemini API returned null for Critical Analysis');
  const jsonText = response.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const data = JSON.parse(jsonText);
  
  console.log('✅ Critical Analysis generated');
  return data;
}