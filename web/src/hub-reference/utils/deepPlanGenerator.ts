// @ts-nocheck
/**
 * Deep Plan Generator — 2-Phase Action Plan Generation
 *
 * PHASE 1 — THINKING:
 *   Gemini performs a deep strategic pre-analysis of the exact idea and location
 *   before a single plan word is written. This produces a structured "intelligence
 *   brief" that governs every decision in Phase 2.
 *
 * PHASE 2 — GROUNDED BUILD:
 *   Using the Phase 1 brief as its foundation plus Google Search Grounding for
 *   real vendors, real pricing, and real regulatory data, Gemini generates the
 *   complete plan in one coherent call. Every section references the actual idea.
 *
 * This replaces the old 12-call fragmented approach where summary, action steps,
 * vendors, risks, and milestones were each written in total isolation.
 */

import { callGeminiAPI, callGeminiWithGrounding } from './geminiService';

export type StageCallback = (stage: string) => void;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function extractJson(text: string, arrayFallback = false): any {
  let t = text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  // Try object first, then array
  const objMatch = t.match(/\{[\s\S]*\}/);
  if (objMatch) {
    try { return JSON.parse(objMatch[0]); } catch { /* fall through */ }
  }
  if (arrayFallback) {
    const arrMatch = t.match(/\[[\s\S]*\]/);
    if (arrMatch) {
      try { return JSON.parse(arrMatch[0]); } catch { /* fall through */ }
    }
  }
  return JSON.parse(t); // let this throw so callers can handle it
}

// ─── PHASE 1: Deep Strategic Thinking ────────────────────────────────────────

export interface IdeaAnalysis {
  industry: string;
  subIndustry: string;
  businessModel: string;
  businessType: string;
  viabilityScore: number;
  viabilityAssessment: string;
  industryContext: string;
  criticalPath: string[];
  locationAdvantages: string[];
  locationChallenges: string[];
  regulatoryRequirements: string[];
  budgetSufficiency: string;
  budgetGuidance: string;
  vendorTypesNeeded: string[];
  timelineFeasibility: string;
  topRisks: Array<{ risk: string; severity: string }>;
  keySuccessFactors: string[];
  recommendedPhases: string[];
}

export async function analyzeIdeaDeep(
  need: string,
  timeline: string,
  budget: string,
  area: string,
  currency: string
): Promise<IdeaAnalysis | null> {
  console.log('🧠 PHASE 1 — Deep strategic analysis of idea...');
  console.log(`   Idea: "${need}"`);
  console.log(`   Location: ${area} | Budget: ${budget} ${currency} | Timeline: ${timeline}`);

  const prompt = `You are a world-class business strategist with 25 years of experience launching and advising businesses across ${area} and globally. You have been asked to perform a DEEP, CRITICAL pre-planning analysis of a business idea BEFORE any action plan is written.

BUSINESS IDEA: "${need}"
TARGET LOCATION: ${area}
AVAILABLE BUDGET: ${budget} ${currency}
PLANNED TIMELINE: ${timeline}

Think carefully and rigorously through every dimension of this idea. Do NOT rush to optimism — if there are serious problems, name them clearly.

Answer these questions through your analysis:
1. What EXACTLY is this business? Its precise industry, business model (how does it make money?), and business type?
2. Is ${area} genuinely a good location for "${need}"? What specific structural advantages does ${area} offer? What real barriers exist?
3. Is ${budget} ${currency} actually sufficient to launch "${need}" in ${area}? If not, what minimum is needed? How should the budget be allocated?
4. What are the REAL challenges that cause businesses like "${need}" to fail in ${area}? Be honest.
5. What licenses, permits, registrations, and regulatory approvals are LEGALLY REQUIRED in ${area} for this type of business? Be specific — name the actual bodies.
6. What is the exact critical path? What must happen first, second, third? What cannot be parallelized?
7. What specific types of vendors, suppliers, and professional service providers does "${need}" require in ${area}?
8. Is ${timeline} realistic for this specific idea in ${area}? What causes delays?

IMPORTANT: Be brutally honest. A bad viability score (3-5) is more valuable than false optimism.

Return ONLY valid JSON. Absolutely no markdown fences, no prose before or after:
{
  "industry": "precise industry name (e.g. 'Specialty Coffee Retail' not just 'Food')",
  "subIndustry": "precise sub-sector (e.g. 'Third-Wave Coffee Shops')",
  "businessModel": "exactly how this business generates revenue (e.g. 'per-transaction product sales + loyalty subscription')",
  "businessType": "B2C / B2B / B2B2C / Marketplace / SaaS / etc",
  "viabilityScore": 7,
  "viabilityAssessment": "2-3 sentences of HONEST assessment of this idea in ${area} with ${budget} ${currency}. Address market fit, competition level, and budget adequacy specifically.",
  "industryContext": "Key market facts: size, growth rate, saturation level, dominant players — specifically for ${area}",
  "criticalPath": [
    "First: specific non-negotiable first action for this idea",
    "Second: specific second action",
    "Third: ...",
    "Fourth: ...",
    "Fifth: ..."
  ],
  "locationAdvantages": [
    "Specific advantage ${area} offers for THIS business idea",
    "Another specific advantage"
  ],
  "locationChallenges": [
    "Specific real challenge ${area} poses for THIS business idea",
    "Another specific challenge"
  ],
  "regulatoryRequirements": [
    "Specific license/permit/registration required in ${area} for this type of business",
    "Another specific requirement",
    "Another"
  ],
  "budgetSufficiency": "sufficient / tight / insufficient",
  "budgetGuidance": "How to split ${budget} ${currency} across the key cost centres for this specific business in ${area}. Be specific about percentages or amounts.",
  "vendorTypesNeeded": [
    "Specific type of vendor needed (e.g. 'Commercial kitchen equipment supplier')",
    "Another vendor type",
    "Another",
    "Another"
  ],
  "timelineFeasibility": "realistic / optimistic / tight",
  "topRisks": [
    { "risk": "Specific risk for this idea in ${area}", "severity": "High" },
    { "risk": "Specific risk 2", "severity": "High" },
    { "risk": "Specific risk 3", "severity": "Medium" },
    { "risk": "Specific risk 4", "severity": "Medium" },
    { "risk": "Specific risk 5", "severity": "Low" }
  ],
  "keySuccessFactors": [
    "Critical factor specific to ${need} success in ${area}",
    "Factor 2",
    "Factor 3",
    "Factor 4"
  ],
  "recommendedPhases": [
    "Phase 1 name specific to this idea (e.g. 'Site Selection & Lease Negotiation')",
    "Phase 2 name",
    "Phase 3 name",
    "Phase 4 name",
    "Phase 5 name",
    "Phase 6 name"
  ]
}`;

  try {
    const text = await callGeminiAPI(prompt, 0.15);
    if (!text) {
      console.warn('⚠️ Gemini returned null for Phase 1 analysis');
      // Try Claude fallback
      console.log('🔄 Attempting Claude API for Phase 1 analysis...');
      try {
        const { callClaudeAPI } = await import('./claudeService');
        const claudeText = await callClaudeAPI(prompt);
        if (claudeText) {
          console.log('✅ Claude returned response for Phase 1');
          const analysis: IdeaAnalysis = extractJson(claudeText);
          console.log(`✅ PHASE 1 COMPLETE (Claude API)`);
          console.log(`   Industry: ${analysis.industry} / ${analysis.subIndustry}`);
          console.log(`   Business Model: ${analysis.businessModel}`);
          console.log(`   Viability: ${analysis.viabilityScore}/10 — ${analysis.viabilityAssessment?.substring(0, 80)}...`);
          console.log(`   Budget: ${analysis.budgetSufficiency}`);
          console.log(`   Timeline: ${analysis.timelineFeasibility}`);
          console.log(`   Critical Path: ${analysis.criticalPath?.length} steps`);
          console.log(`   Regulatory Requirements: ${analysis.regulatoryRequirements?.length} identified`);
          console.log(`   Recommended Phases: ${analysis.recommendedPhases?.join(' → ')}`);
          return analysis;
        }
      } catch (claudeErr) {
        console.error('❌ Claude fallback for Phase 1 failed:', claudeErr);
      }
      return null;
    }
    
    const analysis: IdeaAnalysis = extractJson(text);

    console.log(`✅ PHASE 1 COMPLETE`);
    console.log(`   Industry: ${analysis.industry} / ${analysis.subIndustry}`);
    console.log(`   Business Model: ${analysis.businessModel}`);
    console.log(`   Viability: ${analysis.viabilityScore}/10 — ${analysis.viabilityAssessment?.substring(0, 80)}...`);
    console.log(`   Budget: ${analysis.budgetSufficiency}`);
    console.log(`   Timeline: ${analysis.timelineFeasibility}`);
    console.log(`   Critical Path: ${analysis.criticalPath?.length} steps`);
    console.log(`   Regulatory Requirements: ${analysis.regulatoryRequirements?.length} identified`);
    console.log(`   Recommended Phases: ${analysis.recommendedPhases?.join(' → ')}`);

    return analysis;
  } catch (err) {
    console.error('❌ PHASE 1 analysis failed:', err);
    // Try Claude as fallback
    console.log('🔄 Attempting Claude API for Phase 1 (Gemini errored)...');
    try {
      const { callClaudeAPI } = await import('./claudeService');
      const claudeText = await callClaudeAPI(prompt);
      if (claudeText) {
        const analysis: IdeaAnalysis = extractJson(claudeText);
        console.log(`✅ PHASE 1 COMPLETE (Claude fallback after error)`);
        console.log(`   Industry: ${analysis.industry} / ${analysis.subIndustry}`);
        console.log(`   Viability: ${analysis.viabilityScore}/10`);
        return analysis;
      }
    } catch (claudeErr) {
      console.error('❌ Claude fallback also failed:', claudeErr);
    }
    return null;
  }
}

// ─── PHASE 2: Full Grounded Plan Generation ──────────────────────────────────

export async function buildGroundedPlan(
  need: string,
  timeline: string,
  budget: string,
  area: string,
  currency: string,
  analysis: IdeaAnalysis | null
): Promise<any> {
  console.log('🌐 PHASE 2 — Building complete grounded action plan with Google Search...');

  // Build the analysis context block to inject into the prompt
  const analysisBlock = analysis
    ? `═══ STRATEGIC PRE-ANALYSIS (Phase 1 Intelligence Brief) ═══
Industry: ${analysis.industry} → ${analysis.subIndustry}
Business Model: ${analysis.businessModel} (${analysis.businessType})
Viability: ${analysis.viabilityScore}/10 — ${analysis.viabilityAssessment}
Industry Context: ${analysis.industryContext}
Budget Status: ${analysis.budgetSufficiency.toUpperCase()} — ${analysis.budgetGuidance}
Timeline: ${analysis.timelineFeasibility.toUpperCase()}

Critical Path (must follow this sequence):
${analysis.criticalPath?.map((s, i) => `  ${i + 1}. ${s}`).join('\n')}

${area} Advantages for this business:
${analysis.locationAdvantages?.map(a => `  + ${a}`).join('\n')}

${area} Challenges for this business:
${analysis.locationChallenges?.map(c => `  ⚠ ${c}`).join('\n')}

Legal Requirements in ${area} for this business:
${analysis.regulatoryRequirements?.map(r => `  • ${r}`).join('\n')}

Key Success Factors:
${analysis.keySuccessFactors?.map(f => `  ★ ${f}`).join('\n')}

Top Risks:
${analysis.topRisks?.map(r => `  [${r.severity}] ${r.risk}`).join('\n')}

Vendor Types Required:
${analysis.vendorTypesNeeded?.map(v => `  → ${v}`).join('\n')}

Recommended Plan Phases:
${analysis.recommendedPhases?.map((p, i) => `  Phase ${i + 1}: ${p}`).join('\n')}
═══════════════════════════════════════════════════════`
    : `No pre-analysis available. Proceed with thorough direct research for "${need}" in ${area}.`;

  const phaseNames = analysis?.recommendedPhases?.length === 6
    ? analysis.recommendedPhases
    : [
        `${need} — Foundation & Setup`,
        `${need} — Resource & Infrastructure`,
        `${need} — Market Entry & Branding`,
        `${need} — Pre-Launch Testing`,
        `${need} — Launch & Activation`,
        `${need} — Growth & Optimisation`,
      ];

  const prompt = `You are a specialist business consultant who has just completed a deep strategic analysis of a client's business idea. Your job now is to write a COMPLETE, HIGHLY SPECIFIC action plan using that analysis and REAL Google Search data.

BUSINESS IDEA: "${need}"
LOCATION: ${area}
BUDGET: ${budget} ${currency}
TIMELINE: ${timeline}
ALL MONETARY AMOUNTS MUST USE CURRENCY: ${currency}

${analysisBlock}

═══ GENERATION RULES — NON-NEGOTIABLE ═══
1. SPECIFICITY: Every single element of this plan MUST be specifically about "${need}" in ${area}. NEVER write generic business advice. If you catch yourself writing something that could apply to any business, rewrite it.
2. REAL VENDORS: Use Google Search to find REAL companies/vendors in ${area} that serve businesses like "${need}". Every vendor name must be a real, searchable company.
3. REAL COSTS: All costs must be in ${currency} at ACTUAL ${area} market rates (verified via Google Search). Do not use US/generic prices unless ${area} is the United States.
4. REAL REGULATIONS: Compliance requirements must reference ACTUAL regulatory bodies in ${area}.
5. COHERENCE: Every section must be aware of and consistent with every other section. The budget, phases, vendors, and milestones must all tell one consistent story.
6. HONESTY: If the analysis flagged budget insufficiency or high risk, reflect that honestly in the plan.

USE GOOGLE SEARCH NOW TO FIND:
- Real vendors and service providers in ${area} for "${need}"
- Current market pricing for relevant services in ${area} in ${currency}
- Actual regulatory authorities and requirements in ${area} for this business type
- Real competitors or market data for "${need}" in ${area}

═══ GENERATE THE COMPLETE PLAN AS JSON ═══

Return ONLY valid JSON — no markdown fences, no text before or after, starting with { and ending with }:

{
  "summary": "Write exactly 3 paragraphs. ¶1: What '${need}' is, exactly how it makes money (${analysis?.businessModel || 'as determined'}), and why ${area} is/is not the right market — be specific about ${area} market conditions. ¶2: The critical path summary — what must happen in what order and the key challenges specific to ${area} that will make or break this. ¶3: What success looks like at the end of ${timeline} with ${budget} ${currency}, including realistic first-year revenue targets or key metrics. Minimum 220 words. This must sound like it was written specifically for someone launching '${need}' in ${area}.",

  "budgetBreakdown": [
    {
      "category": "Budget category name SPECIFIC to '${need}' operations (e.g. not 'Personnel' but 'Kitchen Staff & Chef Salaries')",
      "amount": "Actual ${currency} figure (e.g. ${currency} 18,000) — NOT a percentage",
      "percentage": "XX% of total ${budget} budget",
      "priority": "High",
      "description": "Why this budget category exists specifically for '${need}' in ${area} and what would happen if underfunded",
      "specificItems": [
        "Specific cost line item for '${need}' (with ${currency} estimate where possible)",
        "Another specific item",
        "Another specific item",
        "Another specific item"
      ]
    }
  ],

  "actionSteps": [
    {
      "phase": "${phaseNames[0]}",
      "description": "180+ word description written SPECIFICALLY for '${need}' in ${area}. Explain exactly what happens in this phase, why it comes first (reference the critical path), what ${area}-specific factors affect how this phase plays out, and what the most common pitfalls are for this type of business at this stage.",
      "duration": "Specific timeframe within ${timeline} (e.g. 'Weeks 1-4')",
      "estimatedCost": "${currency} X,XXX - X,XXX",
      "detailedTasks": [
        {
          "task": "Specific task name for '${need}' in ${area}",
          "description": "Exactly HOW to do this for '${need}' in ${area}, including ${area}-specific steps, contacts, or considerations",
          "estimatedTime": "X days/weeks",
          "alternatives": [
            "Alternative approach A for ${area} context (with rough cost if relevant)",
            "Alternative approach B",
            "Alternative approach C"
          ],
          "bestPractices": [
            "Best practice specific to ${area} for this task",
            "Best practice 2 learned from similar businesses in ${area}",
            "Best practice 3"
          ]
        },
        {
          "task": "Second specific task for this phase",
          "description": "How to do this for '${need}' in ${area}",
          "estimatedTime": "X days/weeks",
          "alternatives": ["Alternative A", "Alternative B", "Alternative C"],
          "bestPractices": ["Practice 1", "Practice 2", "Practice 3"]
        },
        {
          "task": "Third specific task for this phase",
          "description": "How to do this for '${need}' in ${area}",
          "estimatedTime": "X days/weeks",
          "alternatives": ["Alternative A", "Alternative B"],
          "bestPractices": ["Practice 1", "Practice 2"]
        }
      ],
      "deliverables": [
        "Concrete deliverable specific to '${need}' from this phase",
        "Another concrete deliverable",
        "Another"
      ],
      "criticalSuccessFactors": [
        "What MUST go right in this phase for '${need}' in ${area}",
        "Second critical factor"
      ]
    },
    {
      "phase": "${phaseNames[1]}",
      "description": "180+ word description for phase 2 specific to '${need}' in ${area}",
      "duration": "Specific timeframe",
      "estimatedCost": "${currency} X,XXX - X,XXX",
      "detailedTasks": [
        { "task": "Specific task", "description": "Specific description for '${need}' in ${area}", "estimatedTime": "X weeks", "alternatives": ["Alt A", "Alt B", "Alt C"], "bestPractices": ["Practice 1", "Practice 2", "Practice 3"] },
        { "task": "Specific task 2", "description": "Specific description", "estimatedTime": "X weeks", "alternatives": ["Alt A", "Alt B"], "bestPractices": ["Practice 1", "Practice 2"] },
        { "task": "Specific task 3", "description": "Specific description", "estimatedTime": "X weeks", "alternatives": ["Alt A", "Alt B"], "bestPractices": ["Practice 1", "Practice 2"] }
      ],
      "deliverables": ["Deliverable 1", "Deliverable 2", "Deliverable 3"],
      "criticalSuccessFactors": ["Factor 1", "Factor 2"]
    },
    {
      "phase": "${phaseNames[2]}",
      "description": "180+ word description for phase 3 specific to '${need}' in ${area}",
      "duration": "Specific timeframe",
      "estimatedCost": "${currency} X,XXX - X,XXX",
      "detailedTasks": [
        { "task": "Specific task", "description": "Specific description for '${need}' in ${area}", "estimatedTime": "X weeks", "alternatives": ["Alt A", "Alt B", "Alt C"], "bestPractices": ["Practice 1", "Practice 2", "Practice 3"] },
        { "task": "Specific task 2", "description": "Specific description", "estimatedTime": "X weeks", "alternatives": ["Alt A", "Alt B"], "bestPractices": ["Practice 1", "Practice 2"] },
        { "task": "Specific task 3", "description": "Specific description", "estimatedTime": "X weeks", "alternatives": ["Alt A", "Alt B"], "bestPractices": ["Practice 1", "Practice 2"] }
      ],
      "deliverables": ["Deliverable 1", "Deliverable 2", "Deliverable 3"],
      "criticalSuccessFactors": ["Factor 1", "Factor 2"]
    },
    {
      "phase": "${phaseNames[3]}",
      "description": "180+ word description for phase 4 specific to '${need}' in ${area}",
      "duration": "Specific timeframe",
      "estimatedCost": "${currency} X,XXX - X,XXX",
      "detailedTasks": [
        { "task": "Specific task", "description": "Specific description for '${need}' in ${area}", "estimatedTime": "X weeks", "alternatives": ["Alt A", "Alt B", "Alt C"], "bestPractices": ["Practice 1", "Practice 2", "Practice 3"] },
        { "task": "Specific task 2", "description": "Specific description", "estimatedTime": "X weeks", "alternatives": ["Alt A", "Alt B"], "bestPractices": ["Practice 1", "Practice 2"] }
      ],
      "deliverables": ["Deliverable 1", "Deliverable 2"],
      "criticalSuccessFactors": ["Factor 1", "Factor 2"]
    },
    {
      "phase": "${phaseNames[4]}",
      "description": "180+ word description for phase 5 specific to '${need}' in ${area}",
      "duration": "Specific timeframe",
      "estimatedCost": "${currency} X,XXX - X,XXX",
      "detailedTasks": [
        { "task": "Specific task", "description": "Specific description for '${need}' in ${area}", "estimatedTime": "X weeks", "alternatives": ["Alt A", "Alt B", "Alt C"], "bestPractices": ["Practice 1", "Practice 2", "Practice 3"] },
        { "task": "Specific task 2", "description": "Specific description", "estimatedTime": "X weeks", "alternatives": ["Alt A", "Alt B"], "bestPractices": ["Practice 1", "Practice 2"] }
      ],
      "deliverables": ["Deliverable 1", "Deliverable 2"],
      "criticalSuccessFactors": ["Factor 1", "Factor 2"]
    },
    {
      "phase": "${phaseNames[5]}",
      "description": "180+ word description for phase 6 specific to '${need}' in ${area}",
      "duration": "Ongoing from Month X",
      "estimatedCost": "${currency} X,XXX - X,XXX/month",
      "detailedTasks": [
        { "task": "Specific task", "description": "Specific description for '${need}' in ${area}", "estimatedTime": "Ongoing", "alternatives": ["Alt A", "Alt B", "Alt C"], "bestPractices": ["Practice 1", "Practice 2", "Practice 3"] },
        { "task": "Specific task 2", "description": "Specific description", "estimatedTime": "Monthly", "alternatives": ["Alt A", "Alt B"], "bestPractices": ["Practice 1", "Practice 2"] }
      ],
      "deliverables": ["Deliverable 1", "Deliverable 2"],
      "criticalSuccessFactors": ["Factor 1", "Factor 2"]
    }
  ],

  "vendors": [
    {
      "name": "REAL company name — verified via Google Search in ${area} for this vendor type: ${analysis?.vendorTypesNeeded?.[0] || 'primary vendor type'}",
      "category": "Vendor category directly relevant to '${need}'",
      "description": "What this company does and specifically why they matter for '${need}' in ${area}",
      "location": "City, ${area}",
      "website": "https://verified-company-website.com",
      "estimatedCost": "${currency} amount based on actual ${area} market rates",
      "services": ["Specific service for '${need}'", "Service 2", "Service 3"],
      "alternatives": ["Real alternative vendor in ${area}", "Another real alternative"]
    },
    {
      "name": "REAL vendor 2 in ${area} for: ${analysis?.vendorTypesNeeded?.[1] || 'secondary vendor type'}",
      "category": "Category",
      "description": "Description specific to '${need}'",
      "location": "City, ${area}",
      "website": "https://website.com",
      "estimatedCost": "${currency} amount",
      "services": ["Service 1", "Service 2", "Service 3"],
      "alternatives": ["Alternative 1", "Alternative 2"]
    },
    {
      "name": "REAL vendor 3 in ${area} for: ${analysis?.vendorTypesNeeded?.[2] || 'third vendor type'}",
      "category": "Category",
      "description": "Description specific to '${need}'",
      "location": "City, ${area}",
      "website": "https://website.com",
      "estimatedCost": "${currency} amount",
      "services": ["Service 1", "Service 2"],
      "alternatives": ["Alternative 1", "Alternative 2"]
    },
    {
      "name": "REAL vendor 4 — Legal/Compliance specialist in ${area} for '${need}' business type",
      "category": "Legal & Compliance",
      "description": "Why this legal firm/service is right for '${need}' in ${area}",
      "location": "City, ${area}",
      "website": "https://website.com",
      "estimatedCost": "${currency} amount",
      "services": ["Service 1", "Service 2", "Service 3"],
      "alternatives": ["Alternative 1", "Alternative 2"]
    },
    {
      "name": "REAL vendor 5 — Marketing/Digital agency in ${area} serving '${need}' businesses",
      "category": "Marketing & Growth",
      "description": "Why this agency fits '${need}' in ${area}",
      "location": "City, ${area}",
      "website": "https://website.com",
      "estimatedCost": "${currency} amount",
      "services": ["Service 1", "Service 2", "Service 3"],
      "alternatives": ["Alternative 1", "Alternative 2"]
    },
    {
      "name": "REAL vendor 6 in ${area} — fourth vendor type needed: ${analysis?.vendorTypesNeeded?.[3] || 'accounting/financial'}",
      "category": "Category",
      "description": "Description specific to '${need}'",
      "location": "City, ${area}",
      "website": "https://website.com",
      "estimatedCost": "${currency} amount",
      "services": ["Service 1", "Service 2"],
      "alternatives": ["Alternative 1"]
    }
  ],

  "milestones": [
    {
      "title": "Milestone name that represents a real checkpoint in '${need}' journey",
      "description": "What achieving this means for '${need}' in ${area} and why it matters",
      "targetDate": "Specific week/month within ${timeline}",
      "dependencies": ["What must be done first", "Another dependency specific to '${need}'"],
      "successCriteria": ["Measurable criterion 1 — with specific number/metric", "Measurable criterion 2"]
    },
    {
      "title": "Milestone 2 specific to '${need}'",
      "description": "Description",
      "targetDate": "Specific date in ${timeline}",
      "dependencies": ["Dependency 1", "Dependency 2"],
      "successCriteria": ["Criterion 1 with number", "Criterion 2"]
    },
    {
      "title": "Milestone 3 — First revenue event for '${need}'",
      "description": "Description",
      "targetDate": "Specific date",
      "dependencies": ["Dependency 1"],
      "successCriteria": ["Criterion 1", "Criterion 2"]
    },
    {
      "title": "Milestone 4 — Operations at scale for '${need}'",
      "description": "Description",
      "targetDate": "Specific date",
      "dependencies": ["Dependency 1"],
      "successCriteria": ["Criterion 1", "Criterion 2"]
    },
    {
      "title": "Milestone 5 — Market position established for '${need}' in ${area}",
      "description": "Description",
      "targetDate": "Specific date",
      "dependencies": ["Dependency 1"],
      "successCriteria": ["Criterion 1", "Criterion 2"]
    },
    {
      "title": "Milestone 6 — Break-even or profitability target for '${need}'",
      "description": "Description based on realistic ${area} market performance",
      "targetDate": "Specific date",
      "dependencies": ["Dependency 1"],
      "successCriteria": ["Criterion 1 — with specific ${currency} figure", "Criterion 2"]
    },
    {
      "title": "Milestone 7 — Growth phase initiation for '${need}'",
      "description": "Description",
      "targetDate": "End of ${timeline} or beyond",
      "dependencies": ["Dependency 1"],
      "successCriteria": ["Criterion 1", "Criterion 2"]
    }
  ],

  "risks": [
    {
      "risk": "Specific risk for '${need}' in ${area} — from the pre-analysis",
      "severity": "High",
      "mitigation": "Specific mitigation strategy tailored to ${area} context and '${need}' operations",
      "alternativeApproaches": [
        "Alternative approach 1 specific to ${area}",
        "Alternative approach 2",
        "Alternative approach 3"
      ],
      "contingencyPlan": "What to do if this risk materialises — specific actions for '${need}' in ${area}"
    },
    {
      "risk": "Risk 2 — specific to '${need}' in ${area}",
      "severity": "High",
      "mitigation": "Specific mitigation",
      "alternativeApproaches": ["Alternative 1", "Alternative 2"],
      "contingencyPlan": "Contingency specific to situation"
    },
    {
      "risk": "Risk 3 — specific to '${need}' in ${area}",
      "severity": "Medium",
      "mitigation": "Specific mitigation",
      "alternativeApproaches": ["Alternative 1", "Alternative 2"],
      "contingencyPlan": "Contingency"
    },
    {
      "risk": "Risk 4 — specific to '${need}' in ${area}",
      "severity": "Medium",
      "mitigation": "Specific mitigation",
      "alternativeApproaches": ["Alternative 1", "Alternative 2"],
      "contingencyPlan": "Contingency"
    },
    {
      "risk": "Risk 5 — regulatory or compliance risk specific to ${area} for '${need}'",
      "severity": "Medium",
      "mitigation": "Specific mitigation",
      "alternativeApproaches": ["Alternative 1"],
      "contingencyPlan": "Contingency"
    }
  ],

  "successMetrics": [
    "KPI 1 — specific measurable metric for '${need}' with target figure in ${currency} or percentage",
    "KPI 2 — customer/user metric with specific target number by end of ${timeline}",
    "KPI 3 — operational metric specific to '${need}' business type",
    "KPI 4 — financial metric with ${currency} target",
    "KPI 5 — market position metric for ${area}",
    "KPI 6 — team or capacity metric",
    "KPI 7 — customer satisfaction or retention metric with target %",
    "KPI 8 — unit economics metric specific to '${need}' (e.g. cost per acquisition, margin %)"
  ],

  "detailedRecommendations": [
    {
      "category": "Category directly relevant to '${need}' (e.g. '${analysis?.industry || 'Industry'} Strategy')",
      "recommendations": [
        "Specific actionable recommendation for '${need}' in ${area}",
        "Recommendation 2",
        "Recommendation 3",
        "Recommendation 4"
      ]
    },
    {
      "category": "Category 2 relevant to '${need}' (e.g. 'Customer Acquisition in ${area}')",
      "recommendations": [
        "Recommendation 1",
        "Recommendation 2",
        "Recommendation 3",
        "Recommendation 4"
      ]
    },
    {
      "category": "Category 3 relevant to '${need}' (e.g. '${area} Regulatory Navigation')",
      "recommendations": [
        "Recommendation 1",
        "Recommendation 2",
        "Recommendation 3"
      ]
    },
    {
      "category": "Category 4 relevant to '${need}' (e.g. 'Financial Management for ${area}')",
      "recommendations": [
        "Recommendation 1",
        "Recommendation 2",
        "Recommendation 3"
      ]
    }
  ],

  "fundingOptions": [
    {
      "option": "Funding option most relevant to '${need}' business type in ${area}",
      "description": "How this funding mechanism works for '${need}' in ${area} — include specific programs, institutions, or investors active in ${area}",
      "pros": ["Pro 1 specific to ${area} context", "Pro 2", "Pro 3"],
      "cons": ["Con 1 relevant to ${area}", "Con 2"],
      "typicalAmount": "${currency} amount range typical in ${area} for this funding type"
    },
    {
      "option": "Funding option 2 relevant to '${need}'",
      "description": "Description with ${area} specifics",
      "pros": ["Pro 1", "Pro 2"],
      "cons": ["Con 1", "Con 2"],
      "typicalAmount": "${currency} amount"
    },
    {
      "option": "Funding option 3 — Bootstrap or self-funding approach for '${need}'",
      "description": "How to bootstrap '${need}' in ${area} if external funding unavailable",
      "pros": ["Pro 1", "Pro 2"],
      "cons": ["Con 1", "Con 2"],
      "typicalAmount": "Self-funded: ${budget} ${currency} or less"
    }
  ],

  "complianceChecklist": [
    {
      "requirement": "REAL specific legal/regulatory requirement for '${need}' in ${area}",
      "description": "What this requirement entails, who enforces it in ${area}, and consequences of non-compliance",
      "deadline": "When this must be completed (before launch / within X months / ongoing)",
      "resources": ["Specific ${area} government body or website", "Additional resource"]
    },
    {
      "requirement": "Requirement 2 — specific to '${need}' in ${area}",
      "description": "Description",
      "deadline": "Deadline",
      "resources": ["Resource 1 in ${area}", "Resource 2"]
    },
    {
      "requirement": "Requirement 3 — tax registration specific to ${area}",
      "description": "Description",
      "deadline": "Deadline",
      "resources": ["Resource in ${area}"]
    },
    {
      "requirement": "Requirement 4 — industry-specific licence for '${need}' in ${area}",
      "description": "Description",
      "deadline": "Deadline",
      "resources": ["Resource in ${area}"]
    },
    {
      "requirement": "Requirement 5 — employment or insurance requirement in ${area}",
      "description": "Description",
      "deadline": "Ongoing",
      "resources": ["Resource in ${area}"]
    }
  ]
}

FINAL QUALITY CHECK — before returning, verify:
✅ Every action step phase name contains words specific to '${need}' (not "Phase 1: Planning")
✅ All vendor names are REAL companies findable via Google in ${area}
✅ All amounts are in ${currency} at ${area} market rates
✅ Compliance items name REAL ${area} regulatory bodies
✅ Success metrics have specific numbers/targets
✅ The summary mentions '${need}' and '${area}' specifically throughout
✅ Risks match the pre-analysis top risks
✅ Milestones align with the ${timeline} timeline`;

  // Attempt with grounding, retry on parse failure
  for (let attempt = 1; attempt <= 2; attempt++) {
    const retryNote = attempt === 2
      ? '\n\nCRITICAL PARSE ERROR ON ATTEMPT 1: Your previous response failed JSON parsing. Return ONLY raw JSON starting immediately with { and ending with }. Zero markdown, zero code fences, zero prose before or after.'
      : '';

    try {
      const groundingResult = await callGeminiWithGrounding(prompt + retryNote);
      if (!groundingResult) {
        console.warn(`⚠️ callGeminiWithGrounding returned null on attempt ${attempt}`);
        if (attempt === 2) {
          // Last attempt - try direct Claude API
          console.log('🔄 Attempting direct Claude API as final fallback...');
          try {
            const { callClaudeAPI } = await import('./claudeService');
            const claudeText = await callClaudeAPI(prompt);
            if (claudeText) {
              console.log('✅ Claude API returned response');
              const plan = extractJson(claudeText);
              console.log('✅ PHASE 2 COMPLETE (Claude API fallback)');
              console.log(`   Sections: ${Object.keys(plan).join(', ')}`);
              console.log(`   Action Steps: ${plan.actionSteps?.length}`);
              console.log(`   Vendors: ${plan.vendors?.length}`);
              console.log(`   Milestones: ${plan.milestones?.length}`);
              console.log(`   Risks: ${plan.risks?.length}`);
              return plan;
            }
          } catch (claudeErr) {
            console.error('❌ Claude fallback failed:', claudeErr);
          }
          throw new Error('All API attempts failed (Gemini + Claude)');
        }
        continue; // Try again
      }
      
      const { text, queries } = groundingResult;

      if (queries?.length) {
        console.log(`🔍 Phase 2 Google Search Queries (attempt ${attempt}): ${queries.join(' | ')}`);
      }

      const plan = extractJson(text);

      console.log(`✅ PHASE 2 COMPLETE (attempt ${attempt})`);
      console.log(`   Sections: ${Object.keys(plan).join(', ')}`);
      console.log(`   Action Steps: ${plan.actionSteps?.length}`);
      console.log(`   Vendors: ${plan.vendors?.length}`);
      console.log(`   Milestones: ${plan.milestones?.length}`);
      console.log(`   Risks: ${plan.risks?.length}`);

      return plan;
    } catch (err) {
      console.error(`❌ Phase 2 attempt ${attempt} failed:`, err);
      if (attempt === 2) throw err;
      console.log('🔄 Retrying Phase 2...');
    }
  }
}

// ─── MAIN EXPORT ─────────────────────────────────────────────────────────────

export async function generateDeepActionPlan(
  need: string,
  timeline: string,
  budget: string,
  area: string,
  currency: string,
  onStage?: StageCallback
): Promise<any> {
  console.log('\n══════════════════════════════════════════════════');
  console.log('🚀 DEEP PLAN GENERATOR — Starting 2-Phase Process');
  console.log(`   Idea: "${need}"`);
  console.log(`   ${area} | ${budget} ${currency} | ${timeline}`);
  console.log('══════════════════════════════════════════════════\n');

  // ── Phase 1: Thinking ────────────────────────────────────────────────────
  onStage?.('analyzing');
  const analysis = await analyzeIdeaDeep(need, timeline, budget, area, currency);

  // ── Phase 2: Grounded Build ──────────────────────────────────────────────
  onStage?.('researching');
  const plan = await buildGroundedPlan(need, timeline, budget, area, currency, analysis);

  onStage?.('finalizing');

  console.log('\n══════════════════════════════════════════════════');
  console.log('✅ DEEP PLAN GENERATOR — Complete');
  console.log('══════════════════════════════════════════════════\n');

  return { ...plan, _analysis: analysis };
}