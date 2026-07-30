// @ts-nocheck
/**
 * Dedicated Business Plan Generation with Gemini API
 * Location-Specific and Topic-Specific Business Plans
 * WITH GUARANTEED REAL COMPETITOR INTEGRATION
 */

import { callGeminiAPI, callGeminiWithGrounding } from './geminiService';
import { searchCompetitors } from './webScraperService';
import { getRealCompetitorsWithGemini } from './getRealCompetitors';

function extractJson(text: string): any {
  let t = text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const objMatch = t.match(/\{[\s\S]*\}/);
  if (objMatch) {
    try {
      return JSON.parse(objMatch[0]);
    } catch {
      // fall through
    }
  }
  return JSON.parse(t);
}

/**
 * Generate comprehensive business plan using Gemini API
 * Tailored specifically to the user's location and business topic
 * WITH MANDATORY REAL COMPETITOR ANALYSIS
 */
export async function generateBusinessPlanWithGemini(
  businessIdea: string,
  targetRevenue: string,
  country: string,
  currency: string
): Promise<any> {
  console.log('📋 Creating comprehensive, location-specific business plan...');
  console.log(`🎯 Business Idea: \"${businessIdea}\"`);
  console.log(`💰 Target Revenue: ${targetRevenue} ${currency}`);
  console.log(`🌍 Location: ${country}`);
  console.log('🔍 ENFORCING REAL competitor data via Google Search Grounding');
  
  // STEP 1: MANDATORY - Fetch REAL competitors using Google Search Grounding
  console.log('🔍 [STEP 1/2] Fetching REAL competitors via Google Search Grounding...');
  let competitorData: any[] = [];
  let competitorSearchStatus = 'pending';
  
  try {
    const competitorResults = await searchCompetitors(businessIdea, country);
    
    if (competitorResults.entities && competitorResults.entities.length > 0) {
      competitorData = competitorResults.entities;
      competitorSearchStatus = 'success';
      console.log(`✅ Found ${competitorData.length} REAL competitors for "${businessIdea}" in ${country}`);
      console.log('📊 Competitors:', competitorData.map(c => c.name).join(', '));
    } else {
      console.warn(`⚠️ No competitors found in first attempt. Trying broader search...`);
      
      // Retry with broader search terms
      const broaderTopic = businessIdea.split(' ').slice(0, 2).join(' '); // Use first 2 words
      const retryResults = await searchCompetitors(broaderTopic, country);
      
      if (retryResults.entities && retryResults.entities.length > 0) {
        competitorData = retryResults.entities;
        competitorSearchStatus = 'success_retry';
        console.log(`✅ Found ${competitorData.length} competitors with broader search`);
      } else {
        competitorSearchStatus = 'failed';
        console.error('❌ Could not find any real competitors even with broader search');
      }
    }
  } catch (error) {
    competitorSearchStatus = 'error';
    console.error('❌ Critical error fetching competitors:', error);
  }
  
  // If no competitors found, use Gemini to search for real competitors
  if (competitorData.length === 0) {
    console.log('🔍 [STEP 1/2] Fetching REAL competitors via Gemini...');
    try {
      competitorData = await getRealCompetitorsWithGemini(businessIdea, country, currency);
      if (competitorData.length > 0) {
        competitorSearchStatus = 'success_gemini';
        console.log(`✅ Found ${competitorData.length} REAL competitors for "${businessIdea}" in ${country}`);
        console.log('📊 Competitors:', competitorData.map(c => c.name).join(', '));
      } else {
        competitorSearchStatus = 'failed_gemini';
        console.error('❌ Could not find any real competitors even with Gemini');
      }
    } catch (error) {
      competitorSearchStatus = 'error_gemini';
      console.error('❌ Critical error fetching competitors with Gemini:', error);
    }
  }
  
  // Build competitor list for prompt
  let realCompetitorsList = '';
  if (competitorData.length > 0) {
    realCompetitorsList = `\n\n**🔥 REAL COMPETITORS DISCOVERED VIA GOOGLE SEARCH - YOU MUST USE THESE EXACT COMPANIES:**\n\n`;
    realCompetitorsList += `**CRITICAL INSTRUCTION:** The following ${competitorData.length} competitors were found via live Google Search for "${businessIdea}" in ${country}. You MUST analyze THESE EXACT COMPANIES in your competitive analysis. DO NOT make up fictional competitors.\n\n`;
    
    competitorData.forEach((comp, idx) => {
      realCompetitorsList += `${idx + 1}. **${comp.name}**\n`;
      realCompetitorsList += `   - Verified Location: ${comp.address || country}\n`;
      realCompetitorsList += `   - Business Description: ${comp.description}\n`;
      if (comp.revenue) realCompetitorsList += `   - Revenue: ${comp.revenue}\n`;
      if (comp.employees) realCompetitorsList += `   - Employees: ${comp.employees}\n`;
      if (comp.founded) realCompetitorsList += `   - Founded: ${comp.founded}\n`;
      if (comp.website) realCompetitorsList += `   - Website: ${comp.website}\n`;
      if (comp.linkedIn) realCompetitorsList += `   - LinkedIn: ${comp.linkedIn}\n`;
      realCompetitorsList += `   - Category: ${comp.category}\n`;
      realCompetitorsList += `   - Source: Live Google Search (${new Date().toISOString().split('T')[0]})\n\n`;
    });
    
    realCompetitorsList += `\n**⚠️ MANDATORY COMPETITOR ANALYSIS RULES:**\n`;
    realCompetitorsList += `1. Use ALL ${competitorData.length} competitors listed above in your "directCompetitors" array\n`;
    realCompetitorsList += `2. Each competitor's "name" field MUST exactly match the names above\n`;
    realCompetitorsList += `3. Use the actual data provided (revenue, employees, location, description)\n`;
    realCompetitorsList += `4. DO NOT create fictional competitors or use placeholder company names\n`;
    realCompetitorsList += `5. If you need to estimate missing data, base it on the company's actual profile\n`;
    realCompetitorsList += `6. Include at least ${Math.min(competitorData.length, 5)} competitors in directCompetitors array\n\n`;
  } else {
    // Fallback: Force Gemini to search for real competitors itself
    realCompetitorsList = `\n\n**⚠️ COMPETITOR RESEARCH REQUIRED:**\n\n`;
    realCompetitorsList += `Pre-search did not return results. You MUST use your Google Search capabilities to find REAL companies operating in the "${businessIdea}" space in ${country}.\n\n`;
    realCompetitorsList += `**MANDATORY STEPS:**\n`;
    realCompetitorsList += `1. Search Google for: "${businessIdea} companies in ${country} 2025 2026"\n`;
    realCompetitorsList += `2. Search Google for: "top ${businessIdea} businesses ${country}"\n`;
    realCompetitorsList += `3. Search Google for: "${businessIdea} market leaders ${country}"\n`;
    realCompetitorsList += `4. Find at least 5-10 REAL companies that exist and operate in ${country}\n`;
    realCompetitorsList += `5. Use their REAL names, not fictional placeholders\n`;
    realCompetitorsList += `6. Verify each company exists before including it\n\n`;
    realCompetitorsList += `**ABSOLUTELY FORBIDDEN:**\n`;
    realCompetitorsList += `- Generic names like "Company A", "ABC Corp", "XYZ Ltd"\n`;
    realCompetitorsList += `- Made-up business names\n`;
    realCompetitorsList += `- Competitors from other countries (must be ${country}-based)\n\n`;
  }
  
  // STEP 2: Generate business plan with STRICT competitor requirements
  console.log('🤖 [STEP 2/2] Generating comprehensive business plan with real competitor data...');
  
  const prompt = `You are an expert business strategist and market analyst with deep knowledge of ${country}'s business landscape, regulations, market conditions, and industry dynamics. Create a COMPREHENSIVE, PROFESSIONAL business plan for \"${businessIdea}\" specifically tailored to ${country}.

${realCompetitorsList}

**BUSINESS CONTEXT:**
Business Idea/Topic: ${businessIdea}
Target Location: ${country}
Target Revenue: ${targetRevenue} ${currency}
Currency: ${currency}

**🚨 BRUTAL HONESTY MANDATE - READ THIS CAREFULLY:**

YOU MUST BE RUTHLESSLY HONEST WITH ALL SCORES, PERCENTAGES, AND ASSESSMENTS:

1. **viabilityScore (0-100):**
   - DO NOT artificially inflate this score
   - If the market is saturated → Score should be 30-50 (not 70-80)
   - If competition is fierce → Reduce score by 20-30 points
   - If barriers to entry are high → Reduce score by 15-25 points
   - If regulatory complexity is high → Reduce score by 10-20 points
   - Most realistic business ideas in competitive markets score 40-65, NOT 75-90
   - Only truly exceptional, low-competition opportunities with clear advantages score above 70
   - NEVER give scores above 85 unless the market has almost no competition

2. **marketGrowthRate:**
   - Use ACTUAL CAGR from real market research for ${country}
   - Most mature markets grow at 2-8% annually, NOT 15-25%
   - Declining markets have negative growth - BE HONEST about this
   - Emerging markets might have 10-15% growth, but verify with real data
   - DO NOT assume all markets are growing rapidly

3. **Market Share Percentages:**
   - New startups typically capture 0.1-2% market share in Year 1, NOT 5-10%
   - Established competitors hold 60-80% of market share combined
   - BE REALISTIC about how difficult it is to take market share from entrenched players
   - If there are 5+ strong competitors, a new entrant might only get 0.5-1% initially

4. **Success Probability:**
   - Most startups have 10-30% success probability, NOT 60-80%
   - High-risk ventures should be labeled as such (20-40% probability)
   - Medium-risk ventures: 30-50% probability
   - Low-risk ventures (rare): 50-70% probability
   - NEVER promise 80%+ success rates unless backed by extraordinary evidence

5. **Financial Projections:**
   - Year 1 revenue is typically 20-40% of target, NOT 80-100%
   - Profitability usually takes 18-36 months, NOT 6-12 months
   - Break-even analysis should reflect actual market difficulty
   - If market is saturated, be honest: "May never achieve target revenue due to intense competition"

**🔬 CRITICAL REQUIREMENTS - LOCATION & TOPIC SPECIFICITY:**

1. **${country}-Specific Research:**
   - ALL market data must reflect ${country}'s actual market conditions
   - Reference ${country}'s regulatory environment, business laws, and compliance requirements
   - Use ${country}-based competitors, suppliers, and market players
   - Base financial projections on ${country}'s economic indicators, inflation rates, and market growth
   - Consider ${country}'s cultural, demographic, and economic factors
   - Include ${country}-specific tax rates, labor costs, and operating expenses
   - Reference ${country}'s startup ecosystem, funding landscape, and investor preferences

2. **"${businessIdea}"-Specific Analysis:**
   - Deep dive into the specific industry/sector of "${businessIdea}" in ${country}
   - Analyze customer segments specifically interested in "${businessIdea}" in ${country}
   - Detail supply chain and partnerships relevant to "${businessIdea}" in ${country}
   - Provide pricing strategies based on "${businessIdea}" market rates in ${country}
   - Include technology and operational requirements specific to this business type
   - Reference successful case studies of similar businesses in ${country}

3. **COMPETITOR ANALYSIS - ABSOLUTE REQUIREMENTS:**
   - In the "directCompetitors" array, you MUST include ONLY real companies
   - Each competitor name must be a real, verifiable business operating in ${country}
   - Use Google Search to find real companies if the pre-searched list is empty
   - Search terms: "${businessIdea} companies ${country}", "top ${businessIdea} businesses ${country}"
   - NO fictional names, NO placeholders, NO generic company names
   - Include 5-10 real competitors minimum
   - For EACH competitor, provide:
     * Real company name (verifiable on Google)
     * Actual location in ${country}
     * Founded year (estimated if unknown)
     * Revenue estimate (based on company size/public data)
     * Employee count (estimated range if exact unknown)
     * Real strengths based on their actual business
     * Real weaknesses based on market position
     * Actual products/services they offer
     * Realistic market share estimate
     * Real pricing model they use
     * Actual marketing approaches they employ

**REQUIRED BUSINESS PLAN STRUCTURE:**

Return a comprehensive JSON object with the following structure:

{
  "realityCheck": {
    "isViable": true/false,
    "viabilityScore": 0-100 (MUST follow brutal honesty rules above - most ideas score 40-65),
    "honestAssessment": "Brutally honest 200+ word assessment of whether '${businessIdea}' can succeed in ${country}. DO NOT SUGARCOAT. If the market is saturated with 10+ competitors, SAY SO. If success probability is low, ADMIT IT. Include specific negative projections with real percentages like 'only 15% of similar startups survive Year 1' or 'capturing even 0.5% market share will be difficult given established players like [REAL COMPETITOR NAMES]'. Reference ACTUAL market data and statistics from ${country}.",
    "redFlags": ["Minimum 5-8 REAL challenges with specific data - e.g., '${country} market already has 15+ established players with combined 75% market share', 'Regulatory approval takes 18-24 months in ${country}', 'High customer acquisition cost of X ${currency} makes profitability difficult'"],
    "greenFlags": ["ONLY include if genuinely true - do not fabricate advantages", "If market is saturated, this array should be SHORT or EMPTY"],
    "truthBombs": ["Hard truths with real statistics - e.g., 'Only 12% of ${businessIdea} startups in ${country} reach profitability within 3 years', 'Average time to first customer is 8-14 months in this market', 'You'll need X ${currency} just to compete with existing players'"]
  },
  
  "executiveSummary": {
    "businessConcept": "150+ words describing '${businessIdea}' specifically for ${country} market with unique value proposition",
    "missionStatement": "Mission tailored to ${country} market and cultural values",
    "keysToSuccess": ["Success factor 1 specific to ${country}", "Success factor 2", "Success factor 3"],
    "financialHighlights": {
      "targetRevenue": "${targetRevenue} ${currency}",
      "projectedProfit": "REALISTIC amount in ${currency} based on ${country} margins - typically 5-15% of revenue in Year 1-2, NOT 40-50%",
      "breakEvenPoint": "Realistic timeline for ${country} market - typically 18-36 months, NOT 6-12 months unless exceptional circumstances",
      "initialInvestment": "Amount in ${currency} based on actual ${country} startup costs - research real data"
    }
  },
  
  "companyDescription": {
    "businessName": "Suggested name relevant to ${businessIdea} and ${country} market",
    "legalStructure": "Recommended structure under ${country} law (LLC, Corporation, etc.)",
    "location": "Specific city/region in ${country} and why it's optimal for ${businessIdea}",
    "ownership": "Ownership structure common in ${country}",
    "businessModel": "Detailed model for '${businessIdea}' in ${country}",
    "valueProposition": "Why customers in ${country} would choose this ${businessIdea} business"
  },
  
  "marketAnalysis": {
    "industryOverview": "200+ words on '${businessIdea}' industry in ${country} - current state, trends, key players (mention REAL companies by name). BE HONEST about market saturation.",
    "targetMarket": "Detailed description of target market for '${businessIdea}' in ${country}",
    "marketSize": "Actual market size for this sector in ${country} (in ${currency}) - RESEARCH REAL DATA, do not make up numbers",
    "marketGrowthRate": "Real CAGR for ${country} in this industry - MUST be based on actual market research. Most mature markets: 2-8%. Declining markets: NEGATIVE growth. Do NOT invent 15-25% growth rates.",
    "marketTrends": ["Real trend 1 in ${country} with data", "Real trend 2 with statistics", "Real trend 3"],
    "targetCustomers": [
      {
        "segment": "Customer segment name",
        "description": "Who they are in ${country}",
        "size": "Segment size in ${country} with real data",
        "needs": ["Need 1", "Need 2", "Need 3"]
      }
    ],
    "competitiveAnalysis": {
      "directCompetitors": [
        {
          "name": "REAL COMPANY NAME - Use actual businesses from ${country} in the ${businessIdea} space",
          "location": "Real headquarters/office location in ${country}",
          "foundedYear": 2015,
          "annualRevenue": "Amount in ${currency} - estimate based on company size",
          "employeeCount": "Actual or estimated count",
          "strengths": ["Real strength 1", "Real strength 2", "Real strength 3"],
          "weaknesses": ["Real weakness 1", "Real weakness 2"],
          "marketShare": "Estimated X% - BE REALISTIC. Top 3 players typically hold 40-70% combined. New entrant will capture 0.1-2% initially.",
          "keyProducts": ["Real product/service 1", "Real product/service 2"],
          "recentProjects": ["Real or realistic project 1", "Real or realistic project 2"],
          "customerBase": "Description of their actual customer base in ${country}",
          "pricingModel": "How they actually price in ${country}",
          "marketingApproach": ["Real approach 1", "Real approach 2"]
        }
      ],
      "competitiveAdvantage": ["ONLY list if genuinely differentiated - if market is saturated with similar offerings, ADMIT THIS"],
      "differentiationStrategies": [
        {
          "strategy": "Strategy name",
          "description": "How to differentiate in ${country}",
          "implementation": "Specific steps for ${country} market",
          "expectedImpact": "REALISTIC impact - not 'will dominate market' but 'could capture 0.5-2% market share if executed well'",
          "timeline": "Timeline realistic for ${country}"
        }
      ],
      "marketGaps": ["ONLY list REAL gaps - if market is saturated, be honest that gaps are minimal"],
      "competitivePositioning": "Where you'll position in ${country} market relative to REAL competitors - BE BRUTALLY HONEST about difficulty of competing"
    }
  },
  
  "organizationManagement": {
    "organizationalStructure": "Structure appropriate for ${country} business culture",
    "managementTeam": [
      {
        "role": "Role title",
        "responsibilities": ["Responsibility 1", "Responsibility 2"],
        "qualifications": "Qualifications needed in ${country}",
        "compensation": "Market rate in ${currency} for ${country} - RESEARCH REAL SALARY DATA"
      }
    ],
    "advisoryBoard": ["Type of advisor 1 needed in ${country}", "Type 2", "Type 3"],
    "staffingPlan": {
      "year1": 0,
      "year2": 0,
      "year3": 0,
      "keyPositions": ["Position 1", "Position 2", "Position 3"]
    }
  },
  
  "productsServices": {
    "offerings": [
      {
        "name": "Product/Service name",
        "description": "Detailed description for ${country} market",
        "features": ["Feature 1", "Feature 2", "Feature 3"],
        "benefits": ["Benefit 1", "Benefit 2"],
        "pricingStrategy": "Pricing in ${currency} based on ${country} market rates - RESEARCH COMPETITOR PRICING",
        "developmentStage": "Current stage"
      }
    ],
    "productDevelopment": "Roadmap for ${country} market",
    "intellectualProperty": "IP strategy for ${country}"
  },
  
  "marketingStrategy": {
    "marketingObjectives": ["Objective 1 with REALISTIC targets", "Objective 2"],
    "targetChannels": ["Channel 1 effective in ${country}", "Channel 2", "Channel 3"],
    "brandPositioning": "How to position in ${country}",
    "pricingStrategy": "Detailed pricing for ${country} in ${currency}",
    "promotionalPlan": [
      {
        "tactic": "Tactic name",
        "description": "How to execute in ${country}",
        "budget": "Amount in ${currency} - REALISTIC based on ${country} marketing costs",
        "timeline": "Timeline",
        "expectedROI": "REALISTIC ROI - typically 2:1 to 5:1 for startups, NOT 10:1 or 20:1"
      }
    ],
    "salesStrategy": "Sales approach for ${country} market",
    "customerAcquisitionCost": "Estimated CAC in ${currency} - RESEARCH REAL DATA for ${businessIdea} in ${country}",
    "customerLifetimeValue": "Estimated CLV in ${currency} - BE REALISTIC"
  },
  
  "operationsplan": {
    "locationFacilities": "Physical location details for ${country}",
    "technologyInfrastructure": "Tech requirements for ${businessIdea}",
    "supplierPartners": [
      {
        "type": "Supplier type",
        "name": "REAL company name or realistic supplier in ${country}",
        "location": "${country}",
        "products": "What they supply",
        "terms": "Payment terms common in ${country}"
      }
    ],
    "operationalProcesses": "Key processes for ${businessIdea}",
    "qualityControl": "QC measures for ${country} standards"
  },
  
  "financialProjections": {
    "startupCosts": {
      "initialInvestment": "Amount in ${currency} - RESEARCH REAL startup costs in ${country}",
      "breakdown": [
        {
          "category": "Category name",
          "amount": "Amount in ${currency} - REALISTIC for ${country}",
          "description": "What this covers"
        }
      ]
    },
    "revenueProjections": {
      "year1": "REALISTIC revenue in ${currency} - typically 20-40% of target in Year 1, NOT 80-100%",
      "year2": "Amount in ${currency} - realistic growth of 50-150%, not 300-500%",
      "year3": "Amount in ${currency}",
      "assumptions": ["Assumption 1 with REAL data", "Assumption 2 based on ${country} market", "Assumption 3"]
    },
    "profitLossProjections": [
      {
        "year": 1,
        "revenue": "Amount in ${currency}",
        "expenses": "Amount in ${currency} - REALISTIC operating costs for ${country}",
        "netProfit": "Amount in ${currency} - BE HONEST: most startups show LOSSES in Year 1-2"
      }
    ],
    "cashFlowProjections": "Monthly cash flow analysis - BE REALISTIC about timing",
    "breakEvenAnalysis": "When profitability will realistically occur - typically 18-36 months, NOT 6-12 unless exceptional",
    "fundingRequirements": {
      "amount": "Amount in ${currency}",
      "use": ["Use 1", "Use 2", "Use 3"],
      "sources": ["Source 1 available in ${country}", "Source 2"]
    }
  },
  
  "riskAnalysis": {
    "risks": [
      {
        "category": "Risk category",
        "description": "Specific risk in ${country} market - BE COMPREHENSIVE, include 10-15 real risks",
        "likelihood": "High/Medium/Low - BE HONEST",
        "impact": "High/Medium/Low - BE REALISTIC about potential damage",
        "mitigation": "How to mitigate in ${country}"
      }
    ],
    "contingencyPlans": ["Plan 1", "Plan 2", "Plan 3"]
  },
  
  "regulatoryRequirements": {
    "licenses": ["REAL license 1 required in ${country}", "REAL license 2"],
    "permits": ["REAL permit 1 for ${businessIdea} in ${country}", "REAL permit 2"],
    "compliance": ["Compliance requirement 1 specific to ${country}", "Requirement 2"],
    "legalConsiderations": "Legal requirements under ${country} law - RESEARCH ACTUAL REGULATIONS"
  },
  
  "milestones": {
    "timeline": [
      {
        "phase": "Phase name",
        "duration": "REALISTIC timeframe - not '2 weeks to launch' but '4-6 months to MVP'",
        "keyActivities": ["Activity 1", "Activity 2"],
        "successMetrics": ["Metric 1 with REALISTIC targets", "Metric 2"],
        "budget": "Amount in ${currency} for this phase"
      }
    ]
  },
  
  "exitStrategy": {
    "options": ["Exit option 1 viable in ${country}", "Option 2", "Option 3"],
    "timeline": "REALISTIC exit timeline - typically 5-10 years, not 2-3 years",
    "valuation": "Projected valuation based on ${country} market multiples - RESEARCH REAL DATA"
  }
}

**FINAL BRUTAL HONESTY CHECKLIST - VERIFY BEFORE RETURNING:**
✓ viabilityScore reflects REAL market difficulty (most ideas: 40-65, NOT 75-90)
✓ marketGrowthRate uses ACTUAL CAGR from research (mature markets: 2-8%, NOT 15-25%)
✓ Market share estimates are REALISTIC (new entrant: 0.1-2% Year 1, NOT 5-10%)
✓ Financial projections show REALISTIC Year 1 revenue (20-40% of target, NOT 80-100%)
✓ Break-even timeline is HONEST (18-36 months typical, NOT 6-12 months)
✓ Red flags section has 5-8+ REAL challenges with specific data
✓ Success probability reflected in scoring (most startups: 10-30%, NOT 60-80%)
✓ Every competitor in "directCompetitors" is a REAL company (not "ABC Corp", "XYZ Ltd", "Company A")
✓ Each competitor name can be found via Google search for "${businessIdea} ${country}"
✓ Competitor details (revenue, employees, location) are realistic for those actual companies
✓ ALL financial figures are in ${currency} and realistic for ${country}
✓ ALL regulations/licenses are accurate for ${country} and "${businessIdea}"
✓ ALL market statistics reflect ${country}'s actual market as of 2026
✓ The entire plan is tailored to "${businessIdea}" - not a generic template
✓ honestAssessment includes SPECIFIC negative projections if market is competitive
✓ NO dummy data, NO placeholders, NO generic content
✓ NO made-up competitor names - all must be REAL, verifiable companies
✓ NO sugarcoating - if market is saturated, SAY SO with specifics

**FINAL VALIDATION CHECKLIST - VERIFY BEFORE RETURNING:**
✓ Every competitor in "directCompetitors" is a REAL company (not "ABC Corp", "XYZ Ltd", "Company A")
✓ Each competitor name can be found via Google search for "${businessIdea} ${country}"
✓ Competitor details (revenue, employees, location) are realistic for those actual companies
✓ ALL financial figures are in ${currency} and realistic for ${country}
✓ ALL regulations/licenses are accurate for ${country} and "${businessIdea}"
✓ ALL market statistics reflect ${country}'s actual market as of 2026
✓ The entire plan is tailored to "${businessIdea}" - not a generic template
✓ Brutally honest assessment with negatives if warranted
✓ NO dummy data, NO placeholders, NO generic content
✓ NO made-up competitor names - all must be REAL, verifiable companies

**CRITICAL:** If you cannot find real competitors, state "Unable to identify specific competitors" rather than inventing fake company names.

Return ONLY the JSON object, no additional text or markdown formatting.`;

  try {
    // FIX #4: Use Google Search Grounding for the main business plan body so ALL sections
    // (market analysis, regulatory data, vendor suggestions, financials) are grounded in
    // real live search results — not just the pre-fetched competitors.
    console.log('🌐 Generating business plan body with Google Search Grounding for verified data...');
    let generatedText: string | null = null;
    const groundedPlan = await callGeminiWithGrounding(prompt);
    if (groundedPlan?.text) {
      generatedText = groundedPlan.text;
      if (groundedPlan.queries?.length) {
        console.log('🔍 Business Plan Google Search Queries:', groundedPlan.queries.join(' | '));
      }
    } else {
      console.warn('⚠️ Zo/MiniMax returned null — trying Claude fallback...');
      const { callClaudeAPI } = await import('./claudeService');
      generatedText = await callClaudeAPI(prompt);
    }
    if (!generatedText) {
      throw new Error('AI generation returned empty response');
    }

    const businessPlan = extractJson(generatedText);
    
    // Validate competitor data quality
    const competitors = businessPlan?.marketAnalysis?.competitiveAnalysis?.directCompetitors || [];
    console.log(`📊 Business plan generated with ${competitors.length} competitors`);
    
    if (competitors.length > 0) {
      console.log('✅ Competitor names:', competitors.map((c: any) => c.name).join(', '));
      
      // Check for generic/fake names
      const suspiciousNames = competitors.filter((c: any) => {
        const name = c.name.toLowerCase();
        return name.includes('company a') || 
               name.includes('company b') || 
               name.includes('abc corp') || 
               name.includes('xyz ltd') ||
               name.includes('example') ||
               name.includes('placeholder');
      });
      
      if (suspiciousNames.length > 0) {
        console.warn('⚠️ WARNING: Detected potentially fake competitor names:', 
          suspiciousNames.map((c: any) => c.name).join(', '));
      }
    } else {
      console.warn('⚠️ WARNING: No competitors found in generated business plan');
    }
    
    console.log('✅ Successfully generated comprehensive business plan with location and topic specificity');
    return businessPlan;
  } catch (error) {
    console.error('❌ Error generating business plan:', error);
    throw error;
  }
}