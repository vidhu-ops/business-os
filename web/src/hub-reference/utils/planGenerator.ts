// @ts-nocheck
import { getLocationInfo, generateLocalPhone, generateLocalEmail, formatBudgetAmount, getLocationKey, formatBudgetWithCurrency, formatWithCurrency } from './locationData';
import { 
  getLocalVendorsWithGemini, 
  getActionStepsWithGemini,
  getBudgetBreakdownWithGemini,
  getComplianceChecklistWithGemini,
  getMilestonesWithGemini,
  getRisksWithGemini,
  getSuccessMetricsWithGemini,
  isGeminiConfigured 
} from './geminiService';
import { generateDeepActionPlan, StageCallback } from './deepPlanGenerator';

// Helper function to convert USD amounts to selected currency
function convertAmount(usdLow: number, usdHigh: number | null, currencyCode: string): string {
  const low = formatBudgetWithCurrency(usdLow, currencyCode);
  if (usdHigh === null) {
    return `${low}+`;
  }
  const high = formatBudgetWithCurrency(usdHigh, currencyCode);
  return `${low} - ${high}`;
}

export interface TaskDetail {
  task: string;
  description: string;
  estimatedTime: string;
  alternatives: string[];
  bestPractices: string[];
}

export interface PlanData {
  need: string;
  timeline: string;
  budget: string;
  area: string;
  currency: string;
  generatedDate: string;
  summary: string;
  budgetBreakdown: {
    category: string;
    amount: string;
    percentage: string;
    priority: 'High' | 'Medium' | 'Low';
    description: string;
    specificItems: string[];
  }[];
  actionSteps: {
    phase: string;
    description: string;
    duration: string;
    estimatedCost: string;
    detailedTasks: TaskDetail[];
    deliverables: string[];
    criticalSuccessFactors: string[];
  }[];
  vendors: {
    name: string;
    category: string;
    description: string;
    location: string;
    phone?: string;
    email?: string;
    website?: string;
    estimatedCost: string;
    services: string[];
    alternatives: string[];
  }[];
  milestones: {
    title: string;
    description: string;
    targetDate: string;
    dependencies: string[];
    successCriteria: string[];
  }[];
  risks: {
    risk: string;
    severity: 'High' | 'Medium' | 'Low';
    mitigation: string;
    alternativeApproaches: string[];
    contingencyPlan: string;
  }[];
  resources: {
    type: string;
    description: string;
    quantity: string;
    alternatives: string[];
    costSavingOptions: string[];
  }[];
  successMetrics: string[];
  detailedRecommendations: {
    category: string;
    recommendations: string[];
  }[];
  fundingOptions: {
    option: string;
    description: string;
    pros: string[];
    cons: string[];
    typicalAmount: string;
  }[];
  complianceChecklist: {
    requirement: string;
    description: string;
    deadline: string;
    resources: string[];
  }[];
  financialProjections?: {
    yearlyProjections: any[];
    keyMetrics: any[];
    assumptions: {
      title: string;
      items: string[];
    };
  };
}

interface FormData {
  need: string;
  timeline: string;
  budget: string;
  area: string;
  currency: string;
}

// ─── Helpers to safely normalise/coerce deep-plan output into PlanData types ──

function normaliseBudget(raw: any[]): PlanData['budgetBreakdown'] {
  if (!Array.isArray(raw)) return [];
  return raw.map((item: any) => ({
    category: item.category || 'Budget Category',
    amount: item.amount || item.percentage || '0',
    percentage: item.percentage || item.amount || '0%',
    priority: (['High', 'Medium', 'Low'].includes(item.priority) ? item.priority : 'Medium') as 'High' | 'Medium' | 'Low',
    description: item.description || '',
    specificItems: Array.isArray(item.specificItems) ? item.specificItems : [],
  }));
}

function normaliseActionSteps(raw: any[]): PlanData['actionSteps'] {
  if (!Array.isArray(raw)) return [];
  return raw.map((step: any) => ({
    phase: step.phase || 'Phase',
    description: step.description || '',
    duration: step.duration || '',
    estimatedCost: step.estimatedCost || '',
    detailedTasks: Array.isArray(step.detailedTasks)
      ? step.detailedTasks.map((t: any) => ({
          task: t.task || '',
          description: t.description || '',
          estimatedTime: t.estimatedTime || '',
          alternatives: Array.isArray(t.alternatives) ? t.alternatives : [],
          bestPractices: Array.isArray(t.bestPractices) ? t.bestPractices : [],
        }))
      : [],
    deliverables: Array.isArray(step.deliverables) ? step.deliverables : [],
    criticalSuccessFactors: Array.isArray(step.criticalSuccessFactors) ? step.criticalSuccessFactors : [],
  }));
}

function normaliseVendors(raw: any[]): PlanData['vendors'] {
  if (!Array.isArray(raw)) return [];
  return raw.map((v: any) => ({
    name: v.name || 'Vendor',
    category: v.category || '',
    description: v.description || '',
    location: v.location || '',
    phone: v.phone,
    email: v.email,
    website: v.website,
    estimatedCost: v.estimatedCost || '',
    services: Array.isArray(v.services) ? v.services : [],
    alternatives: Array.isArray(v.alternatives) ? v.alternatives : [],
  }));
}

function normaliseMilestones(raw: any[]): PlanData['milestones'] {
  if (!Array.isArray(raw)) return [];
  return raw.map((m: any) => ({
    title: m.title || 'Milestone',
    description: m.description || '',
    targetDate: m.targetDate || '',
    dependencies: Array.isArray(m.dependencies) ? m.dependencies : [],
    successCriteria: Array.isArray(m.successCriteria) ? m.successCriteria : [],
  }));
}

function normaliseRisks(raw: any[]): PlanData['risks'] {
  if (!Array.isArray(raw)) return [];
  return raw.map((r: any) => ({
    risk: r.risk || 'Risk',
    severity: (['High', 'Medium', 'Low'].includes(r.severity) ? r.severity : 'Medium') as 'High' | 'Medium' | 'Low',
    mitigation: r.mitigation || '',
    alternativeApproaches: Array.isArray(r.alternativeApproaches) ? r.alternativeApproaches : [],
    contingencyPlan: r.contingencyPlan || '',
  }));
}

// ─── Primary: Deep 2-Phase Generation ────────────────────────────────────────

export async function generateActionPlan(
  formData: FormData,
  onStage?: StageCallback
): Promise<PlanData> {
  const { need, timeline, budget, area, currency } = formData;

  const generatedDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  // ── Attempt 1: Deep 2-Phase generation (preferred) ───────────────────────
  if (isGeminiConfigured()) {
    try {
      console.log('🚀 Using Deep 2-Phase Plan Generator (primary)...');
      const deep = await generateDeepActionPlan(need, timeline, budget, area, currency, onStage);

      // Validate the plan has the critical sections
      if (
        deep.summary &&
        Array.isArray(deep.actionSteps) && deep.actionSteps.length >= 4 &&
        Array.isArray(deep.vendors) && deep.vendors.length >= 3
      ) {
        // Static generators for sections not covered by deep plan
        const resources = generateResources(need);
        const financialProjections = generatePlanFinancialProjections(need, budget, area, currency);

        return {
          need,
          timeline,
          budget,
          area,
          currency,
          generatedDate,
          summary: typeof deep.summary === 'string' ? deep.summary : generateSummary(need, timeline, budget, area, currency),
          budgetBreakdown: normaliseBudget(deep.budgetBreakdown),
          actionSteps: normaliseActionSteps(deep.actionSteps),
          vendors: normaliseVendors(deep.vendors),
          milestones: normaliseMilestones(deep.milestones),
          risks: normaliseRisks(deep.risks),
          resources,
          successMetrics: Array.isArray(deep.successMetrics) ? deep.successMetrics : [],
          detailedRecommendations: Array.isArray(deep.detailedRecommendations)
            ? deep.detailedRecommendations
            : generateDetailedRecommendations(need, budget, area),
          fundingOptions: Array.isArray(deep.fundingOptions)
            ? deep.fundingOptions
            : generateFundingOptions(budget, currency),
          complianceChecklist: Array.isArray(deep.complianceChecklist)
            ? deep.complianceChecklist
            : await generateComplianceChecklistAsync(need, area),
          financialProjections,
        };
      }

      console.warn('⚠️ Deep plan missing critical sections, falling back to piecemeal...');
    } catch (err) {
      console.error('❌ Deep plan generation failed, falling back to piecemeal approach:', err);
    }
  }

  // ── Fallback: Piecemeal generation (if deep plan fails) ──────────────────
  console.log('📊 Falling back to piecemeal plan generation...');
  onStage?.('researching');

  const budgetBreakdown = await generateBudgetBreakdown(budget, need, area, currency);
  const actionSteps = await generateActionSteps(need, timeline, budget, area, currency);
  const vendors = await generateVendors(need, area, currency);
  const milestones = await generateMilestonesWithFallback(need, timeline, area, currency);
  const risks = await generateRisksWithFallback(need, budget, area, currency);
  const successMetrics = await generateSuccessMetricsWithFallback(need, area, currency);
  const resources = generateResources(need);
  const summary = generateSummary(need, timeline, budget, area, currency);
  const detailedRecommendations = generateDetailedRecommendations(need, budget, area);
  const fundingOptions = generateFundingOptions(budget, currency);
  const complianceChecklist = await generateComplianceChecklistAsync(need, area);
  const financialProjections = generatePlanFinancialProjections(need, budget, area, currency);

  onStage?.('finalizing');

  return {
    need,
    timeline,
    budget,
    area,
    currency,
    generatedDate,
    summary,
    budgetBreakdown,
    actionSteps,
    vendors,
    milestones,
    risks,
    resources,
    successMetrics,
    detailedRecommendations,
    fundingOptions,
    complianceChecklist,
    financialProjections,
  };
}

function generateSummary(need: string, timeline: string, budget: string, area: string, currency: string): string { // SUMMARY_START
  const locationKey = getLocationKey(area);
  const locationInfo = getLocationInfo(locationKey);
  const locationName = locationInfo.name;
  
  const getDetailedLocationContext = () => {
    const contexts: { [key: string]: string } = {
      'United States': `The United States market offers unparalleled infrastructure, deep capital markets, and the world's largest consumer base. Operating in the US requires compliance with federal, state, and local regulations. Business formation typically takes 1-2 weeks, with ongoing compliance requirements including employment law (minimum wage $7.25 federal, higher in many states), tax obligations (federal corporate rate 21%, state rates vary 0-11.5%), and industry-specific licensing. The entrepreneurial ecosystem is robust with extensive venture capital access ($238B in 2025), accelerator programs, and strong IP protection. Labor costs vary significantly by region (${locationInfo.averageSalary} average), with major metropolitan areas commanding premium salaries.`,
      'United Kingdom': `The United Kingdom provides a stable regulatory environment with English common law protection, strong financial services sector, and strategic access to European markets. Post-Brexit, the UK has maintained regulatory equivalence in many areas while pursuing independent trade agreements. Business registration typically takes 1-3 days, with straightforward tax structure (19% corporation tax) and comprehensive business support programs. London remains a global fintech hub with strong venture capital presence. Operating considerations include National Insurance contributions, GDPR compliance, and UK-specific employment law including statutory holiday requirements and workplace pensions.`,

      'Australia': `Australia offers a straightforward business environment with English-language operations, ASIC registration in 1-2 days, corporate tax 25-30%, mandatory superannuation (11% employer contribution), and the Modern Award system governing minimum conditions. Strong APAC trade relationships and the ACCC consumer regime underpin a stable operating environment.`,
      'Norway': `Norway is a high-income Nordic economy (GDP ~NOK 5.9 trillion, 2025) underpinned by the Government Pension Fund Global (>$1.6 trillion). Corporate tax 22%. Norges Bank rate 4.5% (2026). Average salary ~kr 650,000. Brønnøysund/Altinn registration 1-3 days. The Arbeidsmiljøloven provides strong worker protections: 25 working days' statutory holiday, strict overtime rules, and mandatory pension contributions. Labour costs are 1.5× the US baseline — the primary cost challenge. NOK is subject to oil-price volatility.`,
      'Sweden': `Sweden (GDP ~kr 6.9 trillion, 2025) leads in telecom, automotive, and life sciences. Corporate tax 20.6%. Riksbank rate 2.75%. Average salary ~kr 420,000. Bolagsverket registration 1-5 days. Employer social security contributions ~31.42% on gross salary. 25 days statutory holiday (Semesterlagen). GDPR enforced by IMY. Stockholm, Gothenburg, and Malmö are the main hubs.`,
      'Denmark': `Denmark (GDP ~kr 3.1 trillion, 2025) is a top-ranked business-friendly economy. Corporate tax 22%. Danmarks Nationalbank rate 3.1%. Average salary ~kr 480,000. Erhvervsstyrelsen registration 1-2 days. The flexicurity model enables easy hiring/firing with robust unemployment benefits. 5 weeks statutory holiday (Ferielov). Copenhagen leads; fintech and greentech are key growth sectors.`,
      'Netherlands': `The Netherlands (GDP ~€1.1 trillion) is Europe's logistics gateway. Corporate tax 25.8%. DNB/ECB rate 2.65%. Average salary €54,000. KVK registration 1-3 days. GDPR strictly enforced by Autoriteit Persoonsgegevens. Minimum 20 days holiday (25 common in practice). Amsterdam and Rotterdam are the primary hubs.`,
      'Switzerland': `Switzerland (GDP ~CHF 750 billion) offers political neutrality and an effective corporate tax rate of ~14.9% (cantonal variations apply). SNB rate 0.5%. Average salary CHF 95,000. AG/GmbH registration 2-4 weeks. High living and labour costs (1.6× US baseline). Key hubs: Zurich (finance/tech), Geneva (international organisations), Basel (pharma).`,
      'Ireland': `Ireland (GDP ~€500 billion) benefits from a 12.5% corporate tax rate, EU membership, and English language. Central Bank/ECB rate 2.65%. Average salary €50,000. CRO registration 3-5 days. GDPR enforced by DPC. Mandatory PRSI contributions ~11.05% (employer). 20 days statutory leave minimum. Dublin is the primary tech and financial hub.`,
      'Poland': `Poland (GDP ~zł 3.4 trillion, 3.8% growth) is the largest CEE economy. Corporate tax 19% (9% reduced rate for small businesses). NBP rate 5.75%. Average salary ~zł 72,000. KRS registration 1-3 days online. ZUS (Social Insurance Institution) employer contributions ~22%. Warsaw, Kraków, and Wrocław are the main centres.`,
      'Turkey': `Turkey faces macroeconomic headwinds: 65% inflation and CBRT rate 42.5% (2026). Corporate tax 25%. MERSİS registration 2-3 days. SGK employer contributions ~22.5%. Currency risk (₺ depreciation) is a critical planning factor; USD/EUR-denominated contracts are common to hedge exposure. Istanbul dominates; İzmir and Ankara are secondary hubs.`,
      'New Zealand': `New Zealand (GDP ~NZ$420 billion) offers a simple, transparent regulatory environment. RBNZ rate 3.75%. Corporate tax 28%. Average salary NZ$70,000. NZBN same-day registration. ACC levies replace personal injury litigation. Commerce Commission and Consumer Guarantees Act enforce strong consumer rights.`,
      'Israel': `Israel (the "Startup Nation", >6,000 active startups) has a Bank of Israel rate of 4.5% and corporate tax of 23%. Average salary ₪180,000. Rasham Hacharivot registration 3-5 days. Work week is Sunday–Thursday. IIA R&D grants available. High skilled labour costs and geopolitical risk are the primary challenges.`,
      'South Korea': `South Korea (GDP ~₩2,500 trillion, 2.3% growth) is a tech and manufacturing powerhouse. Bank of Korea rate 2.75%. Corporate tax 22%. Average salary ₩45 million. Registration 1-2 days. Chaebol dominance but strong government support for startups. Seoul, Busan, and Incheon are key cities.`,
      'Singapore': `Singapore (ranked #1 for ease of doing business) has a 17% corporate tax rate (effective ~8-10% after exemptions) and ACRA registration in 1-3 hours. MAS rate 3.4%. Average salary S$75,000. CPF contributions: 17% employer + 20% employee. Strong IP via IPOS. Primary sectors: financial services, biomedical, logistics.`,
      'UAE': `The UAE levies 0% personal income tax and 9% federal corporate tax (profits >AED 375,000). Free zones grant 100% foreign ownership and full profit repatriation. CBUAE rate ~5.4%. Average salary AED 180,000. VAT 5%. AML/CFT compliance mandatory. Dubai, Abu Dhabi, DIFC, ADGM, and DMCC are the key operating hubs.`,
      'Saudi Arabia': `Saudi Arabia is executing Vision 2030, opening non-oil sectors to private capital. SAMA rate ~5.5%. Corporate tax 20%. Average salary SAR 120,000. VAT 15%. Nitaqat (Saudisation) employment quotas apply. MISA regional HQ programme incentivises MENA regional bases. ZATCA enforces tax compliance.`,
      'Brazil': `Brazil (GDP ~R$12 trillion, 3.2% growth) has a complex tax system (5,500+ rules) requiring specialist counsel. SELIC rate 13.75%. Corporate tax up to 34% (IRPJ + CSLL). Average salary R$52,000. LGPD (Brazil's GDPR equivalent) applies to data handling. São Paulo and Rio de Janeiro dominate.`,
      'Mexico': `Mexico offers USMCA integration and competitive manufacturing costs. Banxico rate 7.0%. Corporate tax 30%. Average salary ~MX$285,000. IMSS/INFONAVIT employer contributions add ~35% to payroll costs. COFEPRIS governs health sector permits. Key hubs: Monterrey, Guadalajara, Querétaro.`,
      'Argentina': `Argentina faces severe macroeconomic instability: 118% inflation, BCRA rate 32%, and multiple FX regimes. Corporate tax 35%. USD-denominated contracts are common to hedge peso depreciation. AFIP/ARCA tax compliance is complex. Specialist legal and financial advice is essential before operating here.`,
      'South Africa': `South Africa (GDP ~R$9 trillion, 2% growth) is sub-Saharan Africa's most industrialised economy. SARB rate 10.0%. Corporate tax 27%. Average salary R$420,000. BEE compliance required for government contracts. Eskom load-shedding requires backup power planning. Johannesburg and Cape Town are the key business centres.`,
      'Nigeria': `Nigeria (GDP ~₦360 trillion, 3.4% growth) is Africa's largest economy. CBN rate 27.25%. Corporate tax 30%. Average salary ~₦4.8 million. High inflation (33.2%) and FX volatility are key risks. Lagos is the commercial capital; fintech is the fastest-growing sector.`,
      'India': `India (GDP ~₹340 trillion, 6.5% growth) is the world's fifth-largest and fastest-growing major economy. RBI repo rate 6.25%. Average urban salary ~₹9.2 lakh. MCA21 registration 3-5 working days. GST registration required above ₹20 lakh turnover. State-level shop-and-establishment licences required. UPI digital infrastructure offers low-cost customer access. Operating costs are 75-80% below Western markets.`,
      'China': `China (GDP ~¥134 trillion, 4.9% growth) requires WFOE or JV structure for foreign entities. PBOC LPR 3.1%. Corporate tax 25%. SAMR registration 5-10 days. PIPL data localisation, ICP licence for internet services, and sector-specific FDI restrictions are critical compliance requirements. Guanxi (relationships) remain central.`,
      'Japan': `Japan (GDP ~¥700 trillion) values quality and long-term relationships. Bank of Japan rate 0.5%. Corporate tax ~23%. KK registration 2-4 weeks. Consumption tax 10%. Nemawashi (consensus-building) is essential. Employment protections are strong; dismissal is legally complex. Aging population drives demand in healthcare and automation.`,
      'Canada': `Canada (GDP ~C$3.2 trillion) offers USMCA market access and generous SR&ED R&D tax credits (35-65%). Bank of Canada rate 3.0%. Federal corporate tax 15%; combined provincial average 26.5%. Average salary C$62,000. Corporations Canada registration 1-5 days. CPP/EI contributions and PIPEDA compliance are key obligations.`,
      'France': `France (GDP ~€2.8 trillion) provides a large domestic market, up to 30% Crédit d'Impôt Recherche R&D tax credits, and strong IP via INPI. Corporate tax 25%. ECB rate 2.65%. Average salary €45,000. 35-hour working week and 5 weeks statutory holiday apply. CSE (works council) mandatory for 50+ employees.`,
      'Germany': `Germany (GDP ~€4.1 trillion) combines industrial strength with growing digital sectors. GmbH requires €25,000 share capital and 2-4 weeks to register. Corporate tax ~30% combined. Works council rights (Betriebsrat) and strong employment protections under KSchG. Average salary €52,000. Average 30 days holiday in practice.`,
    };
    // Return location-specific context if available; otherwise build a factual paragraph — NEVER falls back to US context
    if (contexts[locationName]) {
      return contexts[locationName];
    }
    return `${locationName} is a ${locationInfo.marketMaturity.toLowerCase()} market with ${locationInfo.gdpGrowthRate}% GDP growth (2025/2026 estimates). Corporate tax rate: ${locationInfo.corporateTaxRate}%. Central bank benchmark rate: ${locationInfo.interestRate}%. Annual inflation: ~${locationInfo.inflationRate}%. Average market salary: ${locationInfo.averageSalary}. Regulatory complexity: ${locationInfo.regulatoryComplexity}; ease-of-doing-business score: ${locationInfo.easeOfDoingBusiness}/100. Labour costs are ${(locationInfo.laborCostMultiplier * 100).toFixed(0)}% of the US baseline; real estate costs ${(locationInfo.realEstateMultiplier * 100).toFixed(0)}%. Operating here requires local company registration, tax registration, employment law compliance, and any industry-specific licences. All amounts in this plan are denominated in ${currency}.`;
  };
  
  return `This comprehensive action plan provides a strategic roadmap for successfully executing: ${need}. The plan is specifically designed for implementation in ${locationName}, taking into account local market conditions, regulatory requirements, cultural business practices, and economic factors unique to this jurisdiction.

LOCATION-SPECIFIC CONTEXT: ${getDetailedLocationContext()}

PLAN OVERVIEW: This action plan operates within a ${timeline.toLowerCase()} timeframe and a budget of ${budget} (displayed in ${currency}). All financial projections, vendor pricing, and cost estimates are localized for ${locationName}, considering factors such as:
• Local tax rate: ${locationInfo.taxRate}
• Average market salaries: ${locationInfo.averageSalary}
• Currency: ${currency} (all amounts shown in this currency)
• Labor cost multiplier: ${(locationInfo.laborCostMultiplier * 100).toFixed(0)}% of US baseline
• Real estate cost multiplier: ${(locationInfo.realEstateMultiplier * 100).toFixed(0)}% of US baseline
• Time zone: ${locationInfo.timezone}
• Business hours: ${locationInfo.businessHours}
• Local phone prefix: ${locationInfo.phonePrefix}

COMPREHENSIVE APPROACH: The plan includes detailed implementation phases with step-by-step tasks, multiple alternative approaches for critical decisions (enabling flexibility based on evolving circumstances), specific budget allocations with granular line items, vetted local vendor recommendations with ${locationName}-specific contact information, comprehensive risk assessment with mitigation strategies and contingency plans, and measurable success metrics aligned with your objectives.

All vendors, service providers, and partners referenced in this plan are either based in ${locationName} or have established operations serving the ${locationName} market with local support capabilities. Contact information includes local phone numbers (${locationInfo.phonePrefix} prefix), business hours matching ${locationInfo.timezone}, and pricing in ${currency}.

This plan has been developed considering the regulatory environment in ${locationName}, industry best practices globally, and successful case studies from similar initiatives in comparable markets. The recommendations balance ambition with pragmatism, providing clear guidance while acknowledging the uncertainties inherent in business ventures.`;
}

async function generateBudgetBreakdown(budget: string, need: string, area: string, currencyCode: string): Promise<PlanData['budgetBreakdown']> {
  let budgetBreakdown: any = null;
  
  // Try to get dynamic budget breakdown from Gemini API first
  if (isGeminiConfigured()) {
    try {
      console.log('🤖 Using Gemini API to fetch dynamic budget breakdown...');
      const geminiBudget = await getBudgetBreakdownWithGemini(need, budget, area, currencyCode);
      
      // Use Gemini data (it already has the correct format)
      budgetBreakdown = geminiBudget;
      
      console.log(`✅ Successfully loaded ${geminiBudget.length} dynamic budget categories from Gemini API`);
    } catch (error: any) {
      console.warn('⚠️ Gemini API failed for budget breakdown, using static data as fallback');
      console.warn('Error details:', error?.message || error);
    }
  } else {
    console.log('ℹ️ Gemini API not configured, using static budget breakdown');
  }
  
  // Fallback to static budget breakdown if Gemini fails or not configured
  if (!budgetBreakdown) {
    console.log('📊 Loading static budget breakdown...');
    budgetBreakdown = generateStaticBudgetBreakdown(budget, need);
  }
  
  return budgetBreakdown;
}

function generateStaticBudgetBreakdown(budget: string, need: string): PlanData['budgetBreakdown'] {
  const isLargeBudget = budget.includes('$500') || budget.includes('$1M') || budget.includes('$5M');
  const isMediumBudget = budget.includes('$50,000') || budget.includes('$100,000');
  
  return [
    {
      category: 'Personnel & Operations',
      amount: isLargeBudget ? '35%' : isMediumBudget ? '30%' : '25%',
      percentage: isLargeBudget ? '35%' : isMediumBudget ? '30%' : '25%',
      priority: 'High',
      description: 'Investment in human capital, salaries, benefits, training, and operational overhead',
      specificItems: [
        'Founder/executive salaries and equity compensation',
        'Employee salaries, benefits, and payroll taxes',
        'Recruitment and onboarding costs',
        'Professional development and training programs',
        'Office rent, utilities, and facility maintenance',
        'Administrative supplies and operational expenses'
      ]
    },
    {
      category: 'Infrastructure & Equipment',
      amount: isLargeBudget ? '25%' : isMediumBudget ? '30%' : '35%',
      percentage: isLargeBudget ? '25%' : isMediumBudget ? '30%' : '35%',
      priority: 'High',
      description: 'Physical and digital infrastructure necessary for operations',
      specificItems: [
        'Computers, laptops, tablets, and mobile devices',
        'Servers, networking equipment, and cloud infrastructure',
        'Office furniture, fixtures, and equipment',
        'Industry-specific machinery or specialized equipment',
        'Vehicles or transportation equipment (if applicable)',
        'Inventory and initial stock purchases'
      ]
    },
    {
      category: 'Marketing & Sales',
      amount: '15%',
      percentage: '15%',
      priority: 'High',
      description: 'Customer acquisition, brand building, and revenue generation activities',
      specificItems: [
        'Website development and hosting',
        'Digital advertising (Google Ads, social media, etc.)',
        'Content creation and marketing materials',
        'SEO, email marketing, and marketing automation tools',
        'Trade shows, events, and networking',
        'Sales team commissions and incentives',
        'CRM software and sales tools'
      ]
    },
    {
      category: 'Technology & Software',
      amount: '10%',
      percentage: '10%',
      priority: 'Medium',
      description: 'Software licenses, SaaS subscriptions, and technology development',
      specificItems: [
        'Business management software (ERP, CRM)',
        'Communication tools (Slack, Zoom, email)',
        'Accounting and financial management software',
        'Project management and collaboration tools',
        'Industry-specific software and applications',
        'Cybersecurity and data protection tools',
        'Custom software development (if needed)'
      ]
    },
    {
      category: 'Legal & Compliance',
      amount: '8%',
      percentage: '8%',
      priority: 'Medium',
      description: 'Legal services, regulatory compliance, and intellectual property protection',
      specificItems: [
        'Business entity formation and registration',
        'Contract drafting and review',
        'Trademark and patent registration',
        'Industry licenses and permits',
        'Insurance policies (liability, property, etc.)',
        'Legal retainer and ongoing counsel',
        'Compliance audits and certifications'
      ]
    },
    {
      category: 'Contingency Reserve',
      amount: '7%',
      percentage: '7%',
      priority: 'Low',
      description: 'Emergency fund for unexpected expenses and opportunities',
      specificItems: [
        'Buffer for cost overruns',
        'Emergency repairs or replacements',
        'Unforeseen regulatory requirements',
        'Market opportunity fund',
        'Economic downturn reserve',
        'Strategic pivot or adaptation costs'
      ]
    }
  ];
}

async function generateActionSteps(need: string, timeline: string, budget: string, area: string, currencyCode: string): Promise<PlanData['actionSteps']> {
  let actionSteps: any = null;
  
  // Try to get dynamic action steps from Gemini API first
  if (isGeminiConfigured()) {
    try {
      console.log('🤖 Using Gemini API to fetch dynamic action steps...');
      const geminiSteps = await getActionStepsWithGemini(need, timeline, budget, area, currencyCode);
      
      // Use Gemini data (it already has the correct format)
      actionSteps = geminiSteps;
      
      console.log(`✅ Successfully loaded ${geminiSteps.length} dynamic action phases from Gemini API`);
    } catch (error: any) {
      console.warn('⚠️ Gemini API failed for action steps, using static data as fallback');
      console.warn('Error details:', error?.message || error);
    }
  } else {
    console.log('ℹ️ Gemini API not configured, using static action steps');
  }
  
  // Fallback to static action steps if Gemini fails or not configured
  if (!actionSteps) {
    console.log('📊 Loading static action steps...');
    actionSteps = generateStaticActionSteps(need, timeline, budget, currencyCode);
  }
  
  return actionSteps;
}

function generateStaticActionSteps(need: string, timeline: string, budget: string, currencyCode: string): PlanData['actionSteps'] {
  const isShortTerm = timeline.includes('1-3') || timeline.includes('3-6');
  
  return [
    {
      phase: 'Phase 1: Planning & Foundation',
      description: 'Establish the foundational framework including business structure, legal requirements, strategic planning, and market validation.',
      duration: isShortTerm ? '2-4 weeks' : '1-2 months',
      estimatedCost: '5-10% of total budget',
      detailedTasks: [
        {
          task: 'Conduct Comprehensive Market Research',
          description: 'Analyze target market, customer needs, competitive landscape, and market size to validate business opportunity.',
          estimatedTime: '1-2 weeks',
          alternatives: [
            'Option A: Hire professional market research firm for in-depth analysis',
            'Option B: Use online tools (Google Trends, SEMrush, SurveyMonkey) and conduct DIY research',
            'Option C: Purchase existing market research reports from industry analysts',
            'Option D: Conduct customer interviews and focus groups directly'
          ],
          bestPractices: [
            'Interview at least 20-30 potential customers to validate demand',
            'Analyze competitors\' pricing, positioning, and customer reviews',
            'Use both primary (surveys, interviews) and secondary (reports, data) research',
            'Document all findings in a comprehensive market research report'
          ]
        },
        {
          task: 'Develop Detailed Business Plan',
          description: 'Create comprehensive business plan including executive summary, market analysis, operations plan, financial projections, and growth strategy.',
          estimatedTime: '2-3 weeks',
          alternatives: [
            'Option A: Hire business consultant to develop professional business plan',
            'Option B: Use business plan software (LivePlan, Enloop, BizPlan)',
            'Option C: Attend SBA workshop or use free SBA templates',
            'Option D: Work with SCORE mentor for guidance and feedback'
          ],
          bestPractices: [
            'Include 3-5 year financial projections with monthly breakdowns for year 1',
            'Create multiple scenarios (best case, base case, worst case)',
            'Get feedback from industry experts and potential investors',
            'Update plan quarterly as business evolves'
          ]
        },
        {
          task: 'Register Business Entity & Obtain Licenses',
          description: 'Choose business structure (LLC, Corp, etc.), register with state/federal agencies, and obtain all necessary permits and licenses.',
          estimatedTime: '1-2 weeks',
          alternatives: [
            `Option A: Hire business attorney to handle all registrations (${convertAmount(1500, 3000, currencyCode)})`,
            `Option B: Use online legal services (LegalZoom, Incfile, Northwest) (${convertAmount(200, 500, currencyCode)})`,
            `Option C: DIY registration through state website (filing fees only ${convertAmount(100, 300, currencyCode)})`,
            'Option D: Work with local business incubator for guidance and reduced fees'
          ],
          bestPractices: [
            'Consult with CPA on tax implications of different entity types',
            'Register for EIN (Employer Identification Number) immediately',
            'Research industry-specific licenses required in your jurisdiction',
            'Set up separate business bank account and credit card'
          ]
        },
        {
          task: 'Secure Insurance Coverage',
          description: 'Obtain necessary business insurance including general liability, professional liability, property, and workers compensation.',
          estimatedTime: '1 week',
          alternatives: [
            'Option A: Work with commercial insurance broker for comprehensive coverage',
            'Option B: Purchase policies directly from insurers (State Farm Business, Hiscox)',
            'Option C: Use online business insurance platforms (CoverWallet, NEXT Insurance)',
            'Option D: Join industry association for group insurance rates'
          ],
          bestPractices: [
            'Get quotes from at least 3 different providers',
            'Ensure coverage limits match your actual risk exposure',
            'Review policy exclusions carefully',
            'Update coverage as business grows and risks change'
          ]
        },
        {
          task: 'Set Up Financial Systems & Accounting',
          description: 'Establish bookkeeping system, accounting software, financial controls, and reporting processes.',
          estimatedTime: '1-2 weeks',
          alternatives: [
            'Option A: Hire full-time accountant/bookkeeper',
            'Option B: Outsource to accounting firm or bookkeeping service',
            'Option C: Use accounting software with DIY approach (QuickBooks, Xero, FreshBooks)',
            'Option D: Combination: software + monthly CPA review'
          ],
          bestPractices: [
            'Set up chart of accounts aligned with your business model',
            'Implement expense tracking and approval processes',
            'Reconcile accounts weekly or bi-weekly',
            'Generate monthly financial statements (P&L, Balance Sheet, Cash Flow)'
          ]
        }
      ],
      deliverables: [
        'Complete Business Plan (30-50 pages)',
        'Market Research Report',
        'Legal Entity Registration Documents',
        'Insurance Policies',
        'Financial Systems Setup',
        'Licenses & Permits'
      ],
      criticalSuccessFactors: [
        'Thorough market validation proving demand exists',
        'Realistic financial projections based on solid assumptions',
        'All legal requirements met to operate compliantly',
        'Strong financial foundation and controls in place'
      ]
    },
    {
      phase: 'Phase 2: Resource Acquisition & Setup',
      description: 'Acquire necessary resources, infrastructure, and assemble the core team required for operations.',
      duration: isShortTerm ? '3-6 weeks' : '2-4 months',
      estimatedCost: '25-35% of total budget',
      detailedTasks: [
        {
          task: 'Secure Physical Location or Workspace',
          description: 'Find and secure appropriate workspace - office, retail, industrial, or remote setup depending on business needs.',
          estimatedTime: '2-4 weeks',
          alternatives: [
            'Option A: Lease traditional office space (long-term commitment)',
            'Option B: Co-working space or shared office (flexible, lower commitment)',
            'Option C: Virtual office with occasional conference room access',
            'Option D: Home-based business (lowest cost)',
            'Option E: Executive suite or business center'
          ],
          bestPractices: [
            'Consider location proximity to customers, employees, and suppliers',
            'Negotiate lease terms - try for shorter initial term with renewal options',
            'Factor in build-out costs, utilities, and maintenance',
            'Ensure zoning allows for your business type',
            'Plan for growth - ensure space can accommodate expansion'
          ]
        },
        {
          task: 'Purchase Equipment & Technology Infrastructure',
          description: 'Acquire computers, phones, software, furniture, and industry-specific equipment needed for operations.',
          estimatedTime: '2-3 weeks',
          alternatives: [
            'Option A: Purchase new equipment outright (highest cost, best warranty)',
            'Option B: Lease equipment (lower upfront, tax benefits)',
            'Option C: Buy refurbished/used equipment (50-70% savings)',
            'Option D: Rent equipment short-term while testing needs',
            'Option E: Equipment financing through vendor or bank'
          ],
          bestPractices: [
            'Create detailed equipment list with specifications and budget',
            'Get quotes from multiple vendors',
            'Consider cloud-based solutions over on-premise to reduce costs',
            'Buy slightly more capacity than current needs to allow growth',
            'Set up asset tracking and maintenance schedules'
          ]
        },
        {
          task: 'Recruit & Hire Core Team Members',
          description: 'Define roles, create job descriptions, source candidates, interview, and hire essential team members.',
          estimatedTime: '4-6 weeks',
          alternatives: [
            'Option A: Full-time employees (highest commitment and cost)',
            'Option B: Part-time employees (lower cost, less availability)',
            'Option C: Independent contractors/freelancers (flexible, project-based)',
            'Option D: Interns or apprentices (lower cost, training required)',
            'Option E: Virtual assistants or offshore team (cost-effective for certain roles)',
            'Option F: Start solo and hire as revenue grows'
          ],
          bestPractices: [
            'Hire for culture fit and potential, not just current skills',
            'Use multi-stage interview process including skills assessment',
            'Check references thoroughly',
            'Offer competitive compensation in your market',
            'Create clear onboarding plan for first 90 days'
          ]
        },
        {
          task: 'Implement Technology Stack & Software Systems',
          description: 'Set up essential software tools, cloud services, communication platforms, and productivity systems.',
          estimatedTime: '2-3 weeks',
          alternatives: [
            'Option A: Enterprise-grade solutions with full features (higher cost)',
            'Option B: Small business or startup tier of major platforms (mid-tier cost)',
            'Option C: Free or freemium tools to start (lowest cost, limited features)',
            'Option D: Open-source solutions (free, requires technical expertise)',
            'Option E: All-in-one platforms vs. best-of-breed individual tools'
          ],
          bestPractices: [
            'Choose platforms that integrate with each other',
            'Prioritize user-friendly tools to minimize training time',
            'Ensure cloud-based systems for remote access',
            'Set up automated backups and disaster recovery',
            'Document login credentials and system architecture'
          ]
        },
        {
          task: 'Establish Vendor & Supplier Relationships',
          description: 'Identify, vet, and establish relationships with key suppliers, vendors, and service providers.',
          estimatedTime: '2-4 weeks',
          alternatives: [
            'Option A: Direct manufacturer relationships (best pricing, higher minimums)',
            'Option B: Distributors or wholesalers (easier, smaller quantities)',
            'Option C: Multiple suppliers for redundancy vs. single source for volume discounts',
            'Option D: Local suppliers (faster, easier) vs. overseas (lower cost)',
            'Option E: Dropshipping or just-in-time inventory (minimal capital needed)'
          ],
          bestPractices: [
            'Get quotes from at least 3 suppliers for major items',
            'Negotiate payment terms (Net 30, Net 60)',
            'Request samples before committing to large orders',
            'Build relationships with account managers',
            'Have backup suppliers identified for critical items'
          ]
        }
      ],
      deliverables: [
        'Operational Facility/Workspace',
        'Complete Technology Infrastructure',
        'Core Team Hired & Onboarded',
        'Equipment & Inventory',
        'Supplier Agreements',
        'Standard Operating Procedures (SOPs)'
      ],
      criticalSuccessFactors: [
        'Right team members in place with clear roles',
        'Technology systems functional and integrated',
        'Reliable supplier relationships established',
        'Workspace conducive to productivity and growth'
      ]
    },
    {
      phase: 'Phase 3: Brand Development & Marketing',
      description: 'Create brand identity, marketing materials, and execute go-to-market strategy to build awareness and generate leads.',
      duration: isShortTerm ? '3-5 weeks' : '1-3 months',
      estimatedCost: '10-15% of total budget',
      detailedTasks: [
        {
          task: 'Develop Brand Identity & Visual Assets',
          description: 'Create company name, logo, color palette, typography, brand voice, and visual identity guidelines.',
          estimatedTime: '2-3 weeks',
          alternatives: [
            `Option A: Hire professional branding agency (${convertAmount(5000, 50000, currencyCode)})`,
            `Option B: Work with freelance designer (${convertAmount(1000, 5000, currencyCode)})`,
            `Option C: Use DIY tools (Canva, Looka, Tailor Brands) (${convertAmount(100, 500, currencyCode)})`,
            `Option D: Crowdsource design (99designs, DesignCrowd) (${convertAmount(500, 2000, currencyCode)})`,
            'Option E: Business school student project (low cost, variable quality)'
          ],
          bestPractices: [
            'Research competitor branding to differentiate',
            'Test brand concepts with target audience',
            'Ensure logo works in various sizes and formats',
            'Create comprehensive brand guidelines document',
            'Trademark your brand name and logo'
          ]
        },
        {
          task: 'Build Professional Website',
          description: 'Design and develop responsive, SEO-optimized website with clear value proposition, product/service info, and conversion paths.',
          estimatedTime: '3-6 weeks',
          alternatives: [
            `Option A: Custom development with agency (${convertAmount(10000, 100000, currencyCode)}+)`,
            `Option B: Freelance web developer (${convertAmount(3000, 15000, currencyCode)})`,
            `Option C: Website builders (Squarespace, Wix, Webflow) (${convertAmount(200, 1000, currencyCode)})`,
            `Option D: WordPress with premium theme (${convertAmount(500, 3000, currencyCode)})`,
            `Option E: No-code platforms for simple sites (${convertAmount(100, 500, currencyCode)})`
          ],
          bestPractices: [
            'Ensure mobile-responsive design (60%+ traffic is mobile)',
            'Optimize page load speed (under 3 seconds)',
            'Include clear calls-to-action on every page',
            'Set up analytics (Google Analytics, heatmaps)',
            'Implement SEO best practices from day one'
          ]
        },
        {
          task: 'Create Social Media Presence',
          description: 'Establish profiles on relevant social platforms, develop content strategy, and begin building audience.',
          estimatedTime: '2-3 weeks',
          alternatives: [
            'Option A: Focus on 1-2 platforms where your audience is most active',
            'Option B: Omni-channel presence across all major platforms',
            'Option C: Organic content strategy (time investment)',
            'Option D: Paid advertising strategy (budget investment)',
            'Option E: Influencer partnerships and collaborations'
          ],
          bestPractices: [
            'Post consistently (3-5x per week minimum)',
            'Use platform-specific content (don\'t just cross-post)',
            'Engage with followers and respond to comments',
            'Use hashtags and SEO strategically',
            'Track metrics and optimize based on performance'
          ]
        },
        {
          task: 'Develop Marketing Collateral',
          description: 'Create sales materials, presentations, brochures, business cards, email templates, and promotional content.',
          estimatedTime: '2-4 weeks',
          alternatives: [
            'Option A: Professional copywriter and designer team',
            'Option B: Templates customized with your brand',
            'Option C: DIY using Canva, Adobe Express, or similar tools',
            'Option D: Mix of professional and DIY materials based on importance'
          ],
          bestPractices: [
            'Focus on benefits and outcomes, not just features',
            'Use customer testimonials and case studies',
            'Create templates for efficiency and consistency',
            'A/B test different messages and designs',
            'Update regularly to keep content fresh'
          ]
        },
        {
          task: 'Execute Pre-Launch Marketing Campaign',
          description: 'Build anticipation, generate leads, and create buzz before official launch through strategic marketing activities.',
          estimatedTime: '3-4 weeks',
          alternatives: [
            'Option A: Paid advertising (Google Ads, Facebook, LinkedIn)',
            'Option B: Content marketing and SEO (blogs, videos, podcasts)',
            'Option C: Email marketing to warm leads and prospects',
            'Option D: PR and media outreach',
            'Option E: Partnerships and cross-promotions',
            'Option F: Community building and engagement'
          ],
          bestPractices: [
            'Build email list with lead magnet or early access offer',
            'Create countdown or waitlist to build urgency',
            'Leverage personal and professional networks',
            'Share behind-the-scenes content to humanize brand',
            'Set up tracking to measure campaign effectiveness'
          ]
        }
      ],
      deliverables: [
        'Complete Brand Guidelines',
        'Professional Website',
        'Social Media Profiles & Content',
        'Marketing Collateral Library',
        'Email Marketing System',
        'Pre-Launch Campaign Results'
      ],
      criticalSuccessFactors: [
        'Strong, differentiated brand identity',
        'Website that effectively converts visitors',
        'Growing engaged audience on social platforms',
        'Marketing materials that resonate with target market'
      ]
    },
    {
      phase: 'Phase 4: Testing & Refinement',
      description: 'Conduct thorough testing, gather feedback, and refine processes before full launch.',
      duration: isShortTerm ? '2-3 weeks' : '3-6 weeks',
      estimatedCost: '5-8% of total budget',
      detailedTasks: [
        {
          task: 'Conduct Soft Launch or Beta Testing',
          description: 'Release product/service to limited audience to test operations, gather feedback, and identify issues.',
          estimatedTime: '2-4 weeks',
          alternatives: [
            'Option A: Invite-only beta for select customers',
            'Option B: Friends and family testing round',
            'Option C: Limited geographic release',
            'Option D: Feature-limited release to broader audience',
            'Option E: Paid beta with discounted pricing'
          ],
          bestPractices: [
            'Set clear goals and metrics for beta period',
            'Create feedback mechanisms (surveys, interviews)',
            'Offer incentives for participation and feedback',
            'Document all issues and categorize by priority',
            'Iterate quickly based on feedback'
          ]
        },
        {
          task: 'Gather & Analyze Customer Feedback',
          description: 'Collect detailed feedback from beta users through surveys, interviews, and usage data analysis.',
          estimatedTime: '1-2 weeks',
          alternatives: [
            'Option A: One-on-one customer interviews',
            'Option B: Online surveys and questionnaires',
            'Option C: Focus groups',
            'Option D: Usage analytics and behavioral data',
            'Option E: Net Promoter Score (NPS) measurement'
          ],
          bestPractices: [
            'Ask open-ended questions to uncover unexpected insights',
            'Look for patterns in feedback, not just individual comments',
            'Prioritize changes that impact user experience most',
            'Thank participants and share how you used their feedback',
            'Continue gathering feedback post-launch'
          ]
        },
        {
          task: 'Refine Product/Service Offering',
          description: 'Make improvements to product features, service delivery, pricing, or packaging based on beta feedback.',
          estimatedTime: '2-3 weeks',
          alternatives: [
            'Option A: Major overhaul if fundamental issues found',
            'Option B: Incremental improvements to existing offering',
            'Option C: Add/remove features based on feedback',
            'Option D: Adjust pricing or packaging',
            'Option E: Pivot to different target market or use case'
          ],
          bestPractices: [
            'Prioritize changes using impact vs. effort matrix',
            'Focus on must-fix issues before nice-to-have features',
            'Test changes with subset of users before broad rollout',
            'Document all changes and reasons for decisions',
            'Communicate updates to beta participants'
          ]
        },
        {
          task: 'Optimize Operational Processes',
          description: 'Streamline workflows, improve efficiency, and ensure scalability of operations.',
          estimatedTime: '1-2 weeks',
          alternatives: [
            'Option A: Process mapping and optimization workshops',
            'Option B: Implement automation tools for repetitive tasks',
            'Option C: Hire operations consultant for expert analysis',
            'Option D: Benchmark against industry best practices',
            'Option E: Continuous improvement approach (Kaizen, Lean)'
          ],
          bestPractices: [
            'Document all processes in standard operating procedures',
            'Identify and eliminate bottlenecks',
            'Cross-train team members for flexibility',
            'Set up quality control checkpoints',
            'Create metrics to monitor process performance'
          ]
        },
        {
          task: 'Prepare Customer Support & Service',
          description: 'Establish customer service processes, train team, create FAQ, and set up support channels.',
          estimatedTime: '1-2 weeks',
          alternatives: [
            'Option A: In-house support team',
            'Option B: Outsourced customer service',
            'Option C: Self-service resources (knowledge base, chatbot)',
            'Option D: Community-driven support (forums)',
            'Option E: Tiered support (self-service → email → phone)'
          ],
          bestPractices: [
            'Create comprehensive FAQ and knowledge base',
            'Set clear response time expectations',
            'Train support team on product and customer empathy',
            'Use helpdesk software to track and resolve issues',
            'Monitor customer satisfaction scores (CSAT)'
          ]
        }
      ],
      deliverables: [
        'Beta Test Report',
        'Product/Service Refinements',
        'Optimized Processes',
        'Customer Support System',
        'Quality Assurance Documentation',
        'Launch Readiness Checklist'
      ],
      criticalSuccessFactors: [
        'Beta feedback validates product-market fit',
        'Critical issues resolved before full launch',
        'Operations running smoothly and efficiently',
        'Support team prepared to handle customer inquiries'
      ]
    },
    {
      phase: 'Phase 5: Launch & Initial Growth',
      description: 'Execute full launch, acquire customers, and drive initial revenue and growth.',
      duration: isShortTerm ? '4+ weeks' : '2-4 months',
      estimatedCost: '20-30% of total budget',
      detailedTasks: [
        {
          task: 'Execute Official Launch Campaign',
          description: 'Coordinate multi-channel launch campaign to maximize awareness and drive customer acquisition.',
          estimatedTime: '1-2 weeks for launch, ongoing',
          alternatives: [
            'Option A: Big bang launch with major event or announcement',
            'Option B: Gradual rollout across markets or segments',
            'Option C: Launch with strategic partner or influencer',
            'Option D: Media-driven launch with PR campaign',
            'Option E: Community-driven grassroots launch'
          ],
          bestPractices: [
            'Coordinate timing across all marketing channels',
            'Create launch-specific offers or incentives',
            'Prepare team for increased volume and inquiries',
            'Monitor metrics in real-time during launch',
            'Have crisis communication plan ready'
          ]
        },
        {
          task: 'Implement Customer Acquisition Strategy',
          description: 'Execute proven strategies to attract, convert, and onboard new customers efficiently.',
          estimatedTime: 'Ongoing',
          alternatives: [
            'Option A: Paid advertising (PPC, social ads, display)',
            'Option B: Content marketing and SEO',
            'Option C: Referral and affiliate programs',
            'Option D: Partnerships and channel sales',
            'Option E: Direct sales and outbound outreach',
            'Option F: Events, trade shows, and networking'
          ],
          bestPractices: [
            'Track customer acquisition cost (CAC) by channel',
            'Focus budget on channels with best ROI',
            'Test different messaging and offers',
            'Create smooth onboarding experience',
            'Set up retargeting for warm leads'
          ]
        },
        {
          task: 'Build Customer Retention Programs',
          description: 'Develop strategies and programs to retain customers, increase lifetime value, and encourage referrals.',
          estimatedTime: '2-3 weeks to set up, ongoing execution',
          alternatives: [
            'Option A: Loyalty or rewards program',
            'Option B: Subscription or membership model',
            'Option C: Exclusive perks or VIP treatment',
            'Option D: Regular communication and engagement',
            'Option E: Community building initiatives'
          ],
          bestPractices: [
            'Measure and track customer lifetime value (LTV)',
            'Identify and address churn risk factors',
            'Create touchpoints throughout customer journey',
            'Reward and incentivize referrals',
            'Build personal relationships with key customers'
          ]
        },
        {
          task: 'Scale Team & Resources',
          description: 'Hire additional team members and acquire resources to meet growing demand.',
          estimatedTime: 'Ongoing based on growth',
          alternatives: [
            'Option A: Aggressive hiring to capture market opportunity',
            'Option B: Conservative hiring to maintain profitability',
            'Option C: Contractors/freelancers for flexibility',
            'Option D: Automation before adding headcount',
            'Option E: Outsourcing non-core functions'
          ],
          bestPractices: [
            'Hire ahead of demand for critical roles',
            'Maintain company culture during growth',
            'Create clear career paths for employees',
            'Invest in training and development',
            'Monitor team productivity and satisfaction'
          ]
        },
        {
          task: 'Monitor & Optimize Performance',
          description: 'Track KPIs, analyze data, and continuously optimize all aspects of the business.',
          estimatedTime: 'Ongoing',
          alternatives: [
            'Option A: Comprehensive analytics and BI platform',
            'Option B: Spreadsheet-based tracking',
            'Option C: Automated dashboards and reporting',
            'Option D: Weekly/monthly review meetings',
            'Option E: OKR or balanced scorecard framework'
          ],
          bestPractices: [
            'Define clear KPIs for each business function',
            'Review metrics weekly and take action',
            'Share metrics with team for transparency',
            'A/B test major changes before full rollout',
            'Celebrate wins and learn from failures'
          ]
        }
      ],
      deliverables: [
        'Successful Launch Campaign',
        'Growing Customer Base',
        'Revenue Generation',
        'Optimized Marketing Funnel',
        'Scaled Team',
        'Performance Dashboards'
      ],
      criticalSuccessFactors: [
        'Strong market response and customer adoption',
        'Efficient customer acquisition process',
        'Positive unit economics (LTV > CAC)',
        'Team executing effectively at scale'
      ]
    },
    {
      phase: 'Phase 6: Optimization & Sustainable Growth',
      description: 'Optimize processes, improve efficiency, expand offerings, and build sustainable growth engine.',
      duration: 'Ongoing',
      estimatedCost: '15-25% of total budget',
      detailedTasks: [
        {
          task: 'Analyze Performance Data & Identify Opportunities',
          description: 'Deep dive into all business data to find optimization opportunities and growth levers.',
          estimatedTime: 'Monthly/quarterly reviews',
          alternatives: [
            'Option A: Hire data analyst or analytics team',
            'Option B: Use business intelligence tools (Tableau, Looker)',
            'Option C: Consultant-led analysis quarterly',
            'Option D: Management team self-analysis',
            'Option E: Customer data platform (CDP) for insights'
          ],
          bestPractices: [
            'Look for trends over time, not just snapshots',
            'Segment data by customer, channel, product, etc.',
            'Compare to industry benchmarks',
            'Turn insights into actionable initiatives',
            'Share findings across organization'
          ]
        },
        {
          task: 'Implement Process Automation',
          description: 'Automate repetitive tasks and processes to improve efficiency and reduce costs.',
          estimatedTime: '1-3 months, ongoing',
          alternatives: [
            'Option A: Custom automation development',
            'Option B: No-code automation tools (Zapier, Make)',
            'Option C: AI-powered automation solutions',
            'Option D: RPA (Robotic Process Automation)',
            'Option E: Workflow automation in existing tools'
          ],
          bestPractices: [
            'Start with highest-volume, most repetitive tasks',
            'Document processes before automating',
            'Test automation thoroughly before full deployment',
            'Monitor automated processes for errors',
            'Train team on new automated workflows'
          ]
        },
        {
          task: 'Expand Product/Service Offerings',
          description: 'Develop new products, services, or features based on customer demand and market opportunities.',
          estimatedTime: '2-6 months per new offering',
          alternatives: [
            'Option A: Vertical expansion (complementary products)',
            'Option B: Horizontal expansion (new customer segments)',
            'Option C: Geographic expansion',
            'Option D: Premium tier or enterprise offering',
            'Option E: Partnership or white-label products'
          ],
          bestPractices: [
            'Validate demand before significant investment',
            'Leverage existing capabilities and assets',
            'Start with minimum viable product (MVP)',
            'Price to reflect value and market position',
            'Market to existing customers first'
          ]
        },
        {
          task: 'Strengthen Strategic Partnerships',
          description: 'Build and nurture partnerships that accelerate growth, reduce costs, or enhance capabilities.',
          estimatedTime: 'Ongoing',
          alternatives: [
            'Option A: Distribution partnerships',
            'Option B: Technology integrations',
            'Option C: Co-marketing arrangements',
            'Option D: Supply chain partnerships',
            'Option E: Strategic investors or advisors'
          ],
          bestPractices: [
            'Ensure mutual value and aligned incentives',
            'Formalize partnerships with clear agreements',
            'Assign relationship managers',
            'Regular communication and reviews',
            'Measure partnership ROI'
          ]
        },
        {
          task: 'Plan Long-term Strategy & Expansion',
          description: 'Develop strategic plan for next 3-5 years including expansion, funding, and potential exit strategies.',
          estimatedTime: '1-2 months, annual updates',
          alternatives: [
            'Option A: Bootstrap and grow organically',
            'Option B: Raise venture capital or private equity',
            'Option C: Strategic acquisition or merger',
            'Option D: Franchise or licensing model',
            'Option E: Build to sell vs. build for long-term ownership'
          ],
          bestPractices: [
            'Revisit and update strategy regularly',
            'Include board, advisors, and key team in planning',
            'Balance growth with profitability',
            'Scenario plan for different futures',
            'Align team around strategic priorities'
          ]
        }
      ],
      deliverables: [
        'Performance Optimization Report',
        'Automated Business Processes',
        'New Product/Service Launches',
        'Strategic Partnership Agreements',
        'Long-term Strategic Plan',
        'Sustainable Growth Engine'
      ],
      criticalSuccessFactors: [
        'Continuous improvement culture established',
        'Efficient, scalable operations',
        'Diversified revenue streams',
        'Clear path to long-term success'
      ]
    }
  ];
}

async function generateVendors(need: string, area: string, currencyCode: string): Promise<PlanData['vendors']> {
  let vendors: any = null;
  
  // Try to get dynamic vendors from Gemini API first
  if (isGeminiConfigured()) {
    try {
      console.log('🤖 Using Gemini API to fetch dynamic local vendors...');
      const geminiVendors = await getLocalVendorsWithGemini(need, area, currencyCode);
      
      // Use Gemini data (it already has the correct format)
      vendors = geminiVendors;
      
      console.log(`✅ Successfully loaded ${geminiVendors.length} dynamic vendors from Gemini API`);
    } catch (error: any) {
      console.warn('⚠️ Gemini API failed for vendors, using static data as fallback');
      console.warn('Error details:', error?.message || error);
    }
  } else {
    console.log('ℹ️ Gemini API not configured, using static vendors');
  }
  
  // Fallback to static vendors if Gemini fails or not configured
  if (!vendors) {
    console.log('📊 Loading static vendors...');
    vendors = generateStaticVendors(need, area, currencyCode);
  }
  
  return vendors;
}

function generateStaticVendors(need: string, area: string, currencyCode: string): PlanData['vendors'] {
  const locationKey = getLocationKey(area);
  const locationInfo = getLocationInfo(locationKey);
  const locationName = locationInfo.name;
  
  return [
    {
      name: `${locationName} Business Solutions Group`,
      category: 'Business Consulting & Strategy',
      description: 'Full-service business consulting firm specializing in startup strategy, market entry, growth planning, and operational excellence.',
      location: `Downtown ${locationName} - Financial District`,
      phone: generateLocalPhone(locationKey, 'office'),
      email: generateLocalEmail('businesssolutions', locationKey),
      website: 'Contact for consultation and website details',
      estimatedCost: `${formatBudgetWithCurrency(5000, currencyCode)} - ${formatBudgetWithCurrency(25000, currencyCode)}`,
      services: [
        'Business plan development and review',
        'Market research and competitive analysis',
        'Financial modeling and projections',
        'Operational strategy and optimization',
        'Growth strategy and scaling roadmap'
      ],
      alternatives: [
        'SCORE - Free mentoring and low-cost workshops',
        'Small Business Development Center (SBDC) - Free/low-cost consulting',
        'Online consultants via Clarity.fm or similar platforms',
        'Industry-specific consultants or coaches'
      ]
    },
    {
      name: `${locationName} Legal Partners LLP`,
      category: 'Legal Services',
      description: 'Corporate law firm providing business formation, contracts, intellectual property, employment law, and compliance services.',
      location: `Business District, ${locationName}`,
      phone: generateLocalPhone(locationKey, 'office'),
      email: generateLocalEmail('legalpartners', locationKey),
      website: 'Contact for consultation and website details',
      estimatedCost: `${formatBudgetWithCurrency(3000, currencyCode)} - ${formatBudgetWithCurrency(15000, currencyCode)}`,
      services: [
        'Business entity formation (LLC, Corp, Partnership)',
        'Contract drafting and negotiation',
        'Trademark and patent services',
        'Employment agreements and policies',
        'Regulatory compliance and licensing'
      ],
      alternatives: [
        'Rocket Lawyer or LegalZoom for basic documents',
        'Local solo practitioner attorney (lower rates)',
        'Law school clinics for basic legal work',
        'Prepaid legal services (LegalShield)',
        'DIY with state resources and templates'
      ]
    },
    {
      name: `${locationName} Accounting & Tax Advisors`,
      category: 'Accounting & Financial Services',
      description: 'Certified public accountants offering bookkeeping, tax planning, payroll, CFO services, and financial advisory.',
      location: `${locationName}`,
      phone: generateLocalPhone(locationKey, 'office'),
      email: generateLocalEmail('accounting', locationKey),
      website: 'Contact for consultation and website details',
      estimatedCost: `${formatBudgetWithCurrency(2000, currencyCode)} - ${formatBudgetWithCurrency(10000, currencyCode)}/year`,
      services: [
        'Monthly bookkeeping and reconciliation',
        'Tax planning and preparation',
        'Payroll processing and tax filing',
        'Financial statement preparation',
        'Part-time or fractional CFO services'
      ],
      alternatives: [
        'DIY with QuickBooks or Xero',
        'Online bookkeeping services (Bench, inDinero)',
        'Virtual accounting firms (lower overhead)',
        'H&R Block Small Business for taxes',
        'In-house bookkeeper vs. outsourced'
      ]
    },
    {
      name: `${locationName} Digital Marketing Group`,
      category: 'Marketing & Advertising',
      description: 'Full-service digital marketing agency specializing in branding, social media, SEO, content creation, and paid advertising.',
      location: `${locationName} Creative District`,
      phone: generateLocalPhone(locationKey, 'office'),
      email: generateLocalEmail('digitalmarketing', locationKey),
      website: 'Contact for consultation and website details',
      estimatedCost: `${formatBudgetWithCurrency(4000, currencyCode)} - ${formatBudgetWithCurrency(20000, currencyCode)}`,
      services: [
        'Brand strategy and identity development',
        'Website design and development',
        'Social media management and advertising',
        'SEO and content marketing',
        'Google Ads and PPC campaigns'
      ],
      alternatives: [
        'Freelance marketers from Upwork or Fiverr',
        'In-house marketing hire',
        'Marketing automation platforms (HubSpot, Mailchimp)',
        'DIY with online courses and templates',
        'Marketing co-op or agency-lite services'
      ]
    },
    {
      name: `${locationName} Tech Solutions Inc.`,
      category: 'IT & Technology Services',
      description: 'Technology provider offering website development, cloud services, cybersecurity, IT infrastructure, and managed services.',
      location: `${locationName} Tech Hub`,
      phone: generateLocalPhone(locationKey, 'office'),
      email: generateLocalEmail('techsolutions', locationKey),
      website: 'Contact for consultation and website details',
      estimatedCost: `${formatBudgetAmount(3000, locationKey)} - ${formatBudgetAmount(18000, locationKey)}`,
      services: [
        'Custom website and app development',
        'Cloud infrastructure setup (AWS, Azure, Google Cloud)',
        'Cybersecurity and data protection',
        'IT support and managed services',
        'Software integration and automation'
      ],
      alternatives: [
        'Website builders (Squarespace, Wix, Shopify)',
        'Freelance developers from Toptal or similar',
        'Offshore development teams',
        'No-code/low-code platforms',
        'IT support via remote services (Geek Squad Business)'
      ]
    },
    {
      name: `${locationName} Commercial Realty Partners`,
      category: 'Real Estate & Facilities',
      description: 'Commercial real estate broker specializing in office space, retail locations, industrial properties, and coworking solutions.',
      location: `${locationName}`,
      phone: generateLocalPhone(locationKey, 'office'),
      email: generateLocalEmail('commercialrealty', locationKey),
      website: 'Contact for consultation and website details',
      estimatedCost: `Varies by location and size (avg ${formatBudgetAmount(2000, locationKey)}-${formatBudgetAmount(8000, locationKey)}/month)`,
      services: [
        'Office and retail space leasing',
        'Property search and negotiation',
        'Lease review and advisory',
        'Space planning and design',
        'Coworking and flexible office solutions'
      ],
      alternatives: [
        'Search directly on LoopNet or CREXi',
        'Coworking spaces (WeWork, Regus)',
        'Virtual office services',
        'Home-based business setup',
        'Subleasing from another business'
      ]
    },
    {
      name: `${locationName} Business Equipment & Supply Co.`,
      category: 'Equipment & Supplies',
      description: 'Supplier of office equipment, furniture, technology hardware, and business supplies with leasing options.',
      location: `${locationName} Industrial Park`,
      phone: generateLocalPhone(locationKey, 'office'),
      email: generateLocalEmail('equipment', locationKey),
      website: 'Contact for consultation and website details',
      estimatedCost: `${formatBudgetAmount(5000, locationKey)} - ${formatBudgetAmount(50000, locationKey)}`,
      services: [
        'Office furniture and fixtures',
        'Computers, printers, and technology',
        'Industry-specific equipment',
        'Equipment leasing and financing',
        'Maintenance and support services'
      ],
      alternatives: [
        'Amazon Business or Office Depot for supplies',
        'Refurbished equipment dealers',
        'Craigslist or Facebook Marketplace for used items',
        'Equipment rental services',
        'Direct from manufacturer for best pricing'
      ]
    },
    {
      name: `${locationName} Business Insurance Brokers`,
      category: 'Insurance Services',
      description: 'Insurance broker providing liability, property, workers compensation, business interruption, and specialized coverage.',
      location: `${locationName}`,
      phone: generateLocalPhone(locationKey, 'office'),
      email: generateLocalEmail('insurance', locationKey),
      website: 'Contact for consultation and website details',
      estimatedCost: `${formatBudgetAmount(2000, locationKey)} - ${formatBudgetAmount(12000, locationKey)}/year`,
      services: [
        'General liability insurance',
        'Professional liability (E&O)',
        'Property and equipment insurance',
        'Workers compensation',
        'Business interruption coverage'
      ],
      alternatives: [
        'Online insurance (NEXT, Hiscox, CoverWallet)',
        'Direct from insurers (State Farm, Nationwide)',
        'Industry association group policies',
        'Self-insurance or high deductibles for lower premiums',
        'Bundled policies for discounts'
      ]
    },
    {
      name: `${locationName} HR & Talent Solutions`,
      category: 'Human Resources & Recruiting',
      description: 'HR services including recruiting, payroll, benefits administration, compliance, and employee relations.',
      location: `${locationName}`,
      phone: generateLocalPhone(locationKey, 'office'),
      email: generateLocalEmail('talentsolutions', locationKey),
      website: 'Contact for consultation and website details',
      estimatedCost: `${formatBudgetAmount(1500, locationKey)} - ${formatBudgetAmount(8000, locationKey)}/year`,
      services: [
        'Recruiting and talent acquisition',
        'Payroll processing and tax filing',
        'Benefits administration',
        'HR compliance and policies',
        'Employee training and development'
      ],
      alternatives: [
        'PEO services (ADP, Paychex, Justworks)',
        'DIY payroll software (Gusto, QuickBooks Payroll)',
        'Job boards for direct recruiting (Indeed, LinkedIn)',
        'Contract recruiter for hiring needs',
        'HR consulting on as-needed basis'
      ]
    },
    {
      name: `${locationName} Print & Promotional Products`,
      category: 'Print & Marketing Materials',
      description: 'Printing services for business cards, brochures, signage, promotional products, and branded merchandise.',
      location: `${locationName}`,
      phone: generateLocalPhone(locationKey, 'office'),
      email: generateLocalEmail('printshop', locationKey),
      website: 'Contact for consultation and website details',
      estimatedCost: `${formatBudgetAmount(500, locationKey)} - ${formatBudgetAmount(5000, locationKey)}`,
      services: [
        'Business cards and stationery',
        'Brochures and marketing materials',
        'Signage and banners',
        'Promotional products and swag',
        'Packaging and labels'
      ],
      alternatives: [
        'Online printing (Vistaprint, Moo, GotPrint)',
        'Local quick print shops',
        'Digital-only marketing materials',
        'Printify or Printful for on-demand products',
        'Wholesale promotional products distributors'
      ]
    }
  ];
}

// ─── FIX #5: Gemini-first wrappers for milestones, risks, success metrics ────

async function generateMilestonesWithFallback(
  need: string,
  timeline: string,
  area: string,
  currency: string
): Promise<PlanData['milestones']> {
  if (isGeminiConfigured()) {
    try {
      const geminiMilestones = await getMilestonesWithGemini(need, timeline, area, currency);
      // Normalise shape to match PlanData['milestones']
      return geminiMilestones.map((m: any) => ({
        title: m.title || 'Milestone',
        description: m.description || '',
        targetDate: m.targetDate || '',
        dependencies: Array.isArray(m.dependencies) ? m.dependencies : [],
        successCriteria: Array.isArray(m.successCriteria) ? m.successCriteria : []
      }));
    } catch {
      console.warn('⚠️ Falling back to static milestones');
    }
  }
  return generateMilestones(timeline, need);
}

async function generateRisksWithFallback(
  need: string,
  budget: string,
  area: string,
  currency: string
): Promise<PlanData['risks']> {
  if (isGeminiConfigured()) {
    try {
      const geminiRisks = await getRisksWithGemini(need, budget, area, currency);
      return geminiRisks.map((r: any) => ({
        risk: r.risk || 'Risk',
        severity: (['High', 'Medium', 'Low'].includes(r.severity) ? r.severity : 'Medium') as 'High' | 'Medium' | 'Low',
        mitigation: r.mitigation || '',
        alternativeApproaches: Array.isArray(r.alternativeApproaches) ? r.alternativeApproaches : [],
        contingencyPlan: r.contingencyPlan || ''
      }));
    } catch {
      console.warn('⚠️ Falling back to static risks');
    }
  }
  return generateRisks(need, budget);
}

async function generateSuccessMetricsWithFallback(
  need: string,
  area: string,
  currency: string
): Promise<string[]> {
  if (isGeminiConfigured()) {
    try {
      return await getSuccessMetricsWithGemini(need, area, currency);
    } catch {
      console.warn('⚠️ Falling back to static success metrics');
    }
  }
  return generateSuccessMetrics(need);
}

// ─────────────────────────────────────────────────────────────────────────────

function generateMilestones(timeline: string, need: string): PlanData['milestones'] {
  const isShortTerm = timeline.includes('1-3') || timeline.includes('3-6');
  
  return [
    {
      title: 'Business Planning Complete',
      description: 'Finalize comprehensive business plan, financial projections, and legal structure decision',
      targetDate: isShortTerm ? 'Week 3-4' : 'Month 1',
      dependencies: ['Market research completed', 'Financial modeling done', 'Team alignment on vision'],
      successCriteria: [
        'Business plan approved by all stakeholders',
        'Financial projections validated by advisor or mentor',
        'Clear go/no-go decision made'
      ]
    },
    {
      title: 'Funding Secured',
      description: 'Secure necessary capital through investors, loans, grants, or personal funds',
      targetDate: isShortTerm ? 'Week 4-5' : 'Month 1-2',
      dependencies: ['Business plan complete', 'Financial projections ready', 'Pitch deck created'],
      successCriteria: [
        'Sufficient capital to reach profitability or next funding round',
        'Terms acceptable and not overly dilutive',
        'Funds accessible and in business account'
      ]
    },
    {
      title: 'Location & Infrastructure Ready',
      description: 'Physical location secured and equipped, technology infrastructure operational',
      targetDate: isShortTerm ? 'Week 8-10' : 'Month 3-4',
      dependencies: ['Funding secured', 'Lease negotiated', 'Equipment ordered'],
      successCriteria: [
        'Workspace ready for team occupancy',
        'All technology systems tested and functional',
        'Safety and compliance requirements met'
      ]
    },
    {
      title: 'Core Team Assembled',
      description: 'Key team members hired, trained, and ready to execute on business plan',
      targetDate: isShortTerm ? 'Week 9-11' : 'Month 3-5',
      dependencies: ['Roles defined', 'Recruiting completed', 'Offer letters signed'],
      successCriteria: [
        'All critical roles filled with quality candidates',
        'Team members through onboarding and training',
        'Team aligned on goals and operating rhythms'
      ]
    },
    {
      title: 'Brand & Marketing Launched',
      description: 'Brand established, website live, and pre-launch marketing campaigns active',
      targetDate: isShortTerm ? 'Week 10-12' : 'Month 4-5',
      dependencies: ['Brand identity complete', 'Website developed', 'Marketing materials ready'],
      successCriteria: [
        'Website live and converting traffic',
        'Social media presence established',
        'Email list growing with qualified leads'
      ]
    },
    {
      title: 'Soft Launch / Beta Testing',
      description: 'Initial operations begin with limited audience for testing and feedback collection',
      targetDate: isShortTerm ? 'Week 12-13' : 'Month 5-6',
      dependencies: ['Product/service ready', 'Operations tested', 'Support systems in place'],
      successCriteria: [
        'Beta users actively using product/service',
        'Feedback being collected systematically',
        'No major operational issues'
      ]
    },
    {
      title: 'Official Launch',
      description: 'Full public launch with complete product/service offering to all target customers',
      targetDate: isShortTerm ? 'Week 14-16' : 'Month 6-7',
      dependencies: ['Beta feedback implemented', 'All systems scaled', 'Marketing campaign ready'],
      successCriteria: [
        'Launch campaign executed successfully',
        'Positive market response and media coverage',
        'Customer acquisition meeting or exceeding targets'
      ]
    },
    {
      title: 'First Revenue Milestone',
      description: 'Achieve initial revenue targets and customer acquisition goals set in business plan',
      targetDate: isShortTerm ? 'Month 3-4' : 'Month 8-9',
      dependencies: ['Customers acquired', 'Sales process working', 'Product delivered successfully'],
      successCriteria: [
        'Revenue target met or exceeded',
        'Customer acquisition cost in acceptable range',
        'Customer satisfaction scores positive'
      ]
    },
    {
      title: 'Break-Even Point',
      description: 'Reach operational break-even with positive cash flow on unit economics',
      targetDate: isShortTerm ? 'Month 5-6' : 'Month 12-18',
      dependencies: ['Revenue growing', 'Costs optimized', 'Operations efficient'],
      successCriteria: [
        'Monthly revenue covers monthly expenses',
        'Positive contribution margin per customer',
        'Clear path to profitability'
      ]
    },
    {
      title: 'Growth Phase Initiated',
      description: 'Begin scaling operations, expanding team, and increasing market presence',
      targetDate: isShortTerm ? 'Month 6+' : 'Month 18-24',
      dependencies: ['Break-even achieved', 'Product-market fit validated', 'Systems proven scalable'],
      successCriteria: [
        'Growth capital secured or cash flow positive',
        'Scalable customer acquisition channels identified',
        'Team and infrastructure ready for scale'
      ]
    }
  ];
}

function generateRisks(need: string, budget: string): PlanData['risks'] {
  return [
    {
      risk: 'Insufficient Capital / Budget Overruns',
      severity: 'High',
      mitigation: 'Maintain 15-20% contingency reserve, implement strict budget monitoring with weekly reviews, and secure backup funding sources or line of credit in advance.',
      alternativeApproaches: [
        'Bootstrap and grow more slowly to match cash flow',
        'Seek strategic partners to share costs',
        'Reduce scope to focus on core essential features',
        'Revenue-based financing or equipment leasing to preserve cash'
      ],
      contingencyPlan: 'If running low on funds, immediately cut non-essential expenses, defer non-critical hires, negotiate extended payment terms with vendors, and accelerate fundraising efforts or activate backup funding source.'
    },
    {
      risk: 'Market Competition & Saturation',
      severity: 'High',
      mitigation: 'Develop unique value proposition and strong differentiation, focus on underserved niche initially, and continuously monitor competitor activities to stay ahead.',
      alternativeApproaches: [
        'Partner with competitor instead of competing',
        'Focus on different customer segment or geography',
        'Compete on service and experience vs. price',
        'Innovate with new business model (subscription, marketplace, etc.)'
      ],
      contingencyPlan: 'If competition intensifies, pivot to adjacent market, double down on customer success to increase retention, or consider acquisition or merger with complementary player.'
    },
    {
      risk: 'Regulatory & Compliance Issues',
      severity: 'Medium',
      mitigation: 'Engage legal counsel early in planning, stay updated on regulations through industry associations, implement compliance management systems and regular audits.',
      alternativeApproaches: [
        'Join industry association for compliance resources',
        'Use compliance software for automation',
        'Hire compliance officer or fractional expert',
        'Start in less regulated market/geography'
      ],
      contingencyPlan: 'If compliance issue arises, immediately consult legal counsel, halt affected operations if necessary, remediate issue promptly, and communicate transparently with stakeholders.'
    },
    {
      risk: 'Talent Acquisition & Retention',
      severity: 'Medium',
      mitigation: 'Offer competitive compensation including equity, create strong company culture and mission, implement employee development programs, and maintain talent pipeline.',
      alternativeApproaches: [
        'Use contractors or agencies for flexibility',
        'Automate before hiring',
        'Remote hiring for broader talent pool',
        'Partner with universities for internship pipeline'
      ],
      contingencyPlan: 'If key employee leaves, have succession plan and cross-training in place, immediately activate recruitment process, consider interim consultant or fractional executive, and conduct exit interview to improve retention.'
    },
    {
      risk: 'Technology Failures or Cybersecurity Breach',
      severity: 'Medium',
      mitigation: 'Invest in robust IT infrastructure with redundancy, implement cybersecurity protocols and regular updates, maintain comprehensive data backups with tested recovery process.',
      alternativeApproaches: [
        'Use managed service provider for IT support',
        'Cloud-based systems with built-in redundancy',
        'Cyber insurance to transfer risk',
        'Regular security audits and penetration testing'
      ],
      contingencyPlan: 'If breach or major failure occurs, activate disaster recovery plan immediately, engage cybersecurity firm, notify affected parties as legally required, and implement enhanced security measures.'
    },
    {
      risk: 'Supply Chain Disruptions',
      severity: 'Medium',
      mitigation: 'Diversify supplier base across geographies, maintain safety stock of critical items, develop contingency sourcing plans, and build strong supplier relationships.',
      alternativeApproaches: [
        'Vertical integration for critical components',
        'Local sourcing to reduce logistics risk',
        'Just-in-case vs. just-in-time inventory',
        'Alternative materials or specifications with multiple sources'
      ],
      contingencyPlan: 'If supply disrupted, activate backup supplier immediately, communicate proactively with customers about delays, consider airfreight or expedited shipping, and adjust production schedule.'
    },
    {
      risk: 'Customer Acquisition Below Target',
      severity: 'High',
      mitigation: 'Implement data-driven marketing with clear attribution, diversify acquisition channels to reduce dependence, continuously optimize conversion funnels through testing.',
      alternativeApproaches: [
        'Pivot target customer segment',
        'Adjust pricing or packaging',
        'Partner channels vs. direct sales',
        'Increase sales team vs. marketing spend'
      ],
      contingencyPlan: 'If acquisition lagging, conduct customer research to understand barriers, test major pricing or positioning changes, reallocate budget to best-performing channels, or bring in growth consultant.'
    },
    {
      risk: 'Economic Downturn or Market Changes',
      severity: 'Low',
      mitigation: 'Build financial resilience with strong margins and reserves, maintain flexible business model that can adapt, diversify revenue streams and customer base.',
      alternativeApproaches: [
        'Focus on recession-resistant customer segments',
        'Offer flexible pricing or payment terms',
        'Reduce fixed costs in favor of variable',
        'Build strong brand loyalty for retention'
      ],
      contingencyPlan: 'If downturn hits, implement cost reduction plan immediately, focus on cash flow vs. growth, shift to value positioning, and potentially pivot to recession-proof services.'
    },
    {
      risk: 'Product-Market Fit Not Achieved',
      severity: 'High',
      mitigation: 'Validate with customers before building, start with MVP to test quickly, gather continuous feedback and iterate rapidly based on data.',
      alternativeApproaches: [
        'Presell product before building',
        'Beta program with committed customers',
        'Pilot with design partner customers',
        'Build in phases with validation gates'
      ],
      contingencyPlan: 'If fit not achieved, conduct deep customer discovery, be willing to pivot product or market, consider returning funds to investors if unable to find fit, or acquire product/team that has achieved fit.'
    },
    {
      risk: 'Key Partner or Supplier Failure',
      severity: 'Medium',
      mitigation: 'Maintain multiple options for critical relationships, include termination and SLA clauses in contracts, regularly evaluate partner performance and health.',
      alternativeApproaches: [
        'Build in-house capability for critical functions',
        'Escrow or backup arrangements for key technology',
        'Insurance for partner default',
        'Gradual relationship building vs. full dependence'
      ],
      contingencyPlan: 'If partner fails, activate backup provider immediately, consider acquiring failed partner assets if strategic, communicate with customers, and accelerate in-house development of capability.'
    }
  ];
}

function generateResources(need: string): PlanData['resources'] {
  return [
    {
      type: 'Leadership Team',
      description: 'Executive leadership including CEO/Founder, COO, CFO, and other C-level executives',
      quantity: '2-4 people',
      alternatives: [
        'Solo founder with advisors and fractional executives',
        'Co-founder team sharing leadership responsibilities',
        'Full executive team hired from day one',
        'Fractional CFO, CMO, or CTO as needed vs. full-time'
      ],
      costSavingOptions: [
        'Equity-heavy compensation vs. high salaries',
        'Fractional or part-time executives',
        'Promote from within vs. external hires',
        'Use advisors and board members for guidance'
      ]
    },
    {
      type: 'Operations Staff',
      description: 'Core operational team members handling day-to-day activities, production, and service delivery',
      quantity: '5-15 people (varies by scale)',
      alternatives: [
        'Full-time employees with benefits',
        'Part-time employees for flexibility',
        'Contract workers or gig economy workers',
        'Outsourced operations to third-party provider',
        'Automation to reduce headcount needs'
      ],
      costSavingOptions: [
        'Hire junior staff and train vs. expensive senior hires',
        'Remote workers in lower cost-of-living areas',
        'Contractors without benefits',
        'Interns or apprentices from local schools',
        'Cross-train for multi-role flexibility'
      ]
    },
    {
      type: 'Sales & Marketing',
      description: 'Dedicated sales representatives, business development, and marketing specialists',
      quantity: '3-8 people',
      alternatives: [
        'Inside sales team vs. field sales',
        'Sales agencies or independent reps',
        'Marketing agency vs. in-house',
        'Growth hacker vs. traditional marketer',
        'Founder-led sales initially'
      ],
      costSavingOptions: [
        'Commission-based vs. salary-based compensation',
        'Marketing automation to reduce headcount',
        'Freelance marketers for specific projects',
        'University partnerships for marketing help',
        'Revenue share with experienced sales leader'
      ]
    },
    {
      type: 'Technology & IT',
      description: 'Software developers, IT support, systems administrators, and technical specialists',
      quantity: '2-5 people',
      alternatives: [
        'In-house development team',
        'Offshore or nearshore development',
        'Development agency or consultancy',
        'Freelance developers for projects',
        'No-code solutions to minimize development needs'
      ],
      costSavingOptions: [
        'Junior developers with senior oversight',
        'Open source vs. commercial software',
        'Cloud services vs. on-premise infrastructure',
        'Managed service provider vs. in-house IT',
        'Offshore development at 30-50% cost savings'
      ]
    },
    {
      type: 'Customer Support',
      description: 'Customer service representatives, technical support staff, and account managers',
      quantity: '2-6 people',
      alternatives: [
        'In-house support team',
        'Outsourced call center or support service',
        'Chatbots and AI for tier-1 support',
        'Community-driven support forums',
        'Part-time or remote support agents'
      ],
      costSavingOptions: [
        'Self-service knowledge base to reduce tickets',
        'Offshore support team',
        'Part-time vs. full-time staff',
        'Shared support across multiple companies',
        'Tiered support with automation handling simple issues'
      ]
    },
    {
      type: 'External Consultants & Advisors',
      description: 'Legal, accounting, HR, strategy consultants, and specialized business advisors',
      quantity: 'As needed (retainer or project basis)',
      alternatives: [
        'Hourly consultants for specific projects',
        'Monthly retainer arrangements',
        'Equity advisors vs. paid consultants',
        'Peer advisory groups (Vistage, EO)',
        'Free resources (SCORE, SBDC)'
      ],
      costSavingOptions: [
        'Use SCORE mentors (free)',
        'Law school clinics or small firm vs. big firm',
        'Online legal/accounting services vs. full-service firm',
        'Bartering services with other businesses',
        'Industry association resources and templates'
      ]
    }
  ];
}

function generateSuccessMetrics(need: string): string[] {
  return [
    'Revenue targets met or exceeded within first 12 months of operation',
    'Customer acquisition cost (CAC) below industry benchmarks and improving quarterly',
    'Customer lifetime value (LTV) at least 3x customer acquisition cost',
    'Customer satisfaction score (CSAT) above 85% and Net Promoter Score (NPS) above 50',
    'Positive cash flow achieved within 18 months without additional funding',
    'Market share growth of 5-10% year-over-year in target segments',
    'Employee retention rate above 80% for first year, improving to 90%+',
    'Gross margin above 60% for service business or 40% for product business',
    'Operating margin improvement of 10-15% annually through efficiency gains',
    'Brand awareness reaching 30% of target market within 18 months',
    'Product/service quality metrics exceeding industry standards and customer expectations',
    'Monthly recurring revenue (MRR) or repeat purchase rate above 40%',
    'Sales pipeline conversion rate above 20% and improving',
    'Time to profitability on new customers under 6 months',
    'Positive online reviews averaging 4.5+ stars across platforms'
  ];
}

function generateDetailedRecommendations(need: string, budget: string, area: string): PlanData['detailedRecommendations'] {
  return [
    {
      category: 'Financial Management',
      recommendations: [
        'Open separate business checking and savings accounts immediately to maintain clean financial records',
        'Implement monthly financial close process with P&L, Balance Sheet, and Cash Flow statement review',
        'Create 13-week cash flow forecast and update weekly to avoid cash surprises',
        'Negotiate Net 30 or Net 60 payment terms with suppliers to preserve working capital',
        'Set up accounting software (QuickBooks, Xero) from day one - don\'t wait',
        'Hire fractional CFO or accountant for monthly review and strategic guidance',
        'Maintain personal and business credit scores above 700 for financing options',
        'Create financial dashboard with key metrics visible to leadership team',
        'Build 3-6 months operating expenses reserve as quickly as possible',
        'Implement expense approval process to prevent overspending'
      ]
    },
    {
      category: 'Marketing & Customer Acquisition',
      recommendations: [
        'Focus on 1-2 customer acquisition channels initially and master them before expanding',
        'Build email list from day one - it\'s your most valuable owned asset',
        'Create content that provides value (not just promotional) to build trust and authority',
        'Implement referral program early - word of mouth is most cost-effective channel',
        'Use retargeting ads to stay in front of warm leads who visited but didn\'t convert',
        'A/B test everything - messaging, imagery, pricing, calls-to-action',
        'Invest in SEO from day one - it takes 6-12 months to see results',
        'Build strategic partnerships for co-marketing and customer sharing',
        'Track every dollar spent on marketing to ROI - cut what doesn\'t work',
        'Create remarkable customer experience that generates organic promotion'
      ]
    },
    {
      category: 'Operations & Efficiency',
      recommendations: [
        'Document all processes in standard operating procedures (SOPs) from the start',
        'Automate repetitive tasks wherever possible to free up time for strategic work',
        'Implement project management tool (Asana, Monday, ClickUp) for accountability',
        'Create clear KPIs for each role and review weekly with team',
        'Build feedback loops to continuously improve operations',
        'Outsource non-core activities to focus on your competitive advantage',
        'Use time tracking to understand where hours are actually spent',
        'Implement regular team meetings with clear agendas and action items',
        'Create decision-making framework to speed up and improve decisions',
        'Build slack into system - don\'t operate at 100% capacity'
      ]
    },
    {
      category: 'Team & Culture',
      recommendations: [
        'Hire slowly and fire quickly - wrong hire is expensive mistake',
        'Create clear company values and use them in hiring and decision-making',
        'Implement regular 1-on-1s with all direct reports for coaching and feedback',
        'Invest in employee development - training pays dividends in retention and performance',
        'Create clear career paths so employees see growth opportunities',
        'Build culture of transparency - share financials and strategy with team',
        'Celebrate wins and learn from failures as a team',
        'Offer equity or profit sharing to align incentives',
        'Create remote work flexibility to access broader talent pool',
        'Conduct stay interviews to understand what keeps good employees engaged'
      ]
    },
    {
      category: 'Product & Innovation',
      recommendations: [
        'Talk to customers weekly - never lose touch with their needs and pain points',
        'Build minimum viable product (MVP) first, then iterate based on feedback',
        'Focus on core features that deliver value - avoid feature bloat',
        'Create product roadmap with customer input and communicate it transparently',
        'Implement feedback loops at every customer touchpoint',
        'Track product usage data to understand what features matter most',
        'Create beta testing program with engaged customers',
        'Build in public and share your journey to create invested community',
        'Stay on top of industry trends and emerging technologies',
        'Protect intellectual property early - trademarks, patents, copyrights'
      ]
    },
    {
      category: 'Risk Management',
      recommendations: [
        'Get proper insurance coverage - don\'t operate naked without protection',
        'Create contracts and terms of service reviewed by attorney',
        'Implement cybersecurity basics - password manager, 2FA, encrypted backups',
        'Build crisis communication plan before you need it',
        'Diversify customer base - don\'t depend on one or two large customers',
        'Maintain good relationships with suppliers and have backup options',
        'Document everything important - verbal agreements aren\'t enforceable',
        'Comply with all regulations - non-compliance can kill business',
        'Create disaster recovery plan for business continuity',
        'Review insurance coverage annually as business grows and changes'
      ]
    }
  ];
}

function generateFundingOptions(budget: string, currencyCode: string): PlanData['fundingOptions'] {
  return [
    {
      option: 'Bootstrapping / Self-Funding',
      description: 'Use personal savings, credit cards, home equity, or revenue from business to fund growth',
      pros: [
        'Maintain full ownership and control',
        'No debt obligations or investor pressure',
        'Forces capital efficiency and creativity',
        'Keep all profits and upside'
      ],
      cons: [
        'Slower growth trajectory',
        'Personal financial risk',
        'Limited resources can constrain opportunities',
        'May not work for capital-intensive businesses'
      ],
      typicalAmount: `${formatBudgetWithCurrency(0, currencyCode)} - ${formatBudgetWithCurrency(100000, currencyCode)}`
    },
    {
      option: 'Friends & Family Round',
      description: 'Raise capital from personal network of friends, family, and close contacts',
      pros: [
        'Easier to raise than institutional capital',
        'Typically more favorable terms',
        'Invested in you, not just the business',
        'Can close quickly'
      ],
      cons: [
        'Can strain personal relationships',
        'May not bring strategic value beyond capital',
        'Limited amount can be raised',
        'Inexperienced investors may create challenges'
      ],
      typicalAmount: `${formatBudgetWithCurrency(10000, currencyCode)} - ${formatBudgetWithCurrency(500000, currencyCode)}`
    },
    {
      option: 'Small Business Loan (SBA or Bank)',
      description: 'Traditional debt financing from bank, often with SBA guarantee to reduce bank risk',
      pros: [
        'Don\'t give up equity ownership',
        'Interest is tax deductible',
        'Fixed payment schedule',
        'SBA programs offer favorable terms'
      ],
      cons: [
        'Requires collateral and personal guarantee',
        'Debt payment obligation regardless of revenue',
        'Can be difficult to qualify for startup',
        'Lengthy application process'
      ],
      typicalAmount: `${formatBudgetWithCurrency(50000, currencyCode)} - ${formatBudgetWithCurrency(5000000, currencyCode)}`
    },
    {
      option: 'Angel Investors',
      description: 'High net worth individuals who invest their own money in early-stage companies',
      pros: [
        'Can provide expertise and connections',
        'More flexible terms than VCs',
        'May be sector-specific with relevant experience',
        'Can close relatively quickly'
      ],
      cons: [
        'Give up equity (typically 10-25%)',
        'May want board seat or control provisions',
        'Can be difficult to find right angels',
        'Time-consuming fundraising process'
      ],
      typicalAmount: `${formatBudgetWithCurrency(25000, currencyCode)} - ${formatBudgetWithCurrency(1000000, currencyCode)}`
    },
    {
      option: 'Venture Capital',
      description: 'Professional investors managing funds who invest in high-growth potential companies',
      pros: [
        'Large amounts of capital available',
        'Bring expertise, network, and credibility',
        'Can provide follow-on funding in future rounds',
        'Validation from respected VC helpful for growth'
      ],
      cons: [
        'Significant equity dilution (20-40%+)',
        'Pressure for rapid growth and exit',
        'Board control and oversight',
        'Only suitable for venture-scale businesses ($100M+ potential)'
      ],
      typicalAmount: `${formatBudgetWithCurrency(1000000, currencyCode)} - ${formatBudgetWithCurrency(100000000, currencyCode)}+`
    },
    {
      option: 'Grants & Competitions',
      description: 'Non-dilutive funding from government agencies, foundations, or business competitions',
      pros: [
        'No equity given up or debt obligation',
        'Validation and credibility from winning',
        'Often includes mentorship and exposure',
        'Free money if you qualify'
      ],
      cons: [
        'Highly competitive with low success rates',
        'Specific eligibility requirements',
        'Lengthy application process',
        'Often have restrictions on use of funds'
      ],
      typicalAmount: `${formatBudgetWithCurrency(5000, currencyCode)} - ${formatBudgetWithCurrency(500000, currencyCode)}`
    },
    {
      option: 'Crowdfunding (Kickstarter, Indiegogo)',
      description: 'Raise funds from large number of people, typically offering product pre-orders or perks',
      pros: [
        'Validates market demand before building',
        'Marketing and customer acquisition built-in',
        'No equity dilution',
        'Can build community of brand advocates'
      ],
      cons: [
        'All-or-nothing on many platforms',
        'Must deliver on promises to backers',
        'Platform fees (5-10%)',
        'Successful campaign requires significant marketing effort'
      ],
      typicalAmount: `${formatBudgetWithCurrency(10000, currencyCode)} - ${formatBudgetWithCurrency(1000000, currencyCode)}`
    },
    {
      option: 'Revenue-Based Financing',
      description: 'Alternative financing where repayment is percentage of monthly revenue until cap reached',
      pros: [
        'No equity dilution or personal guarantee',
        'Payments scale with revenue (lower in slow months)',
        'Faster than traditional bank loans',
        'Based on revenue, not credit score or collateral'
      ],
      cons: [
        'More expensive than traditional debt (effective interest 10-30%)',
        'Only works for revenue-generating businesses',
        'Can strain cash flow during repayment period',
        'Relatively new financing option'
      ],
      typicalAmount: `${formatBudgetWithCurrency(50000, currencyCode)} - ${formatBudgetWithCurrency(5000000, currencyCode)}`
    },
    {
      option: 'Strategic Partner or Corporate Investment',
      description: 'Investment from corporation in your industry, often with strategic partnership component',
      pros: [
        'Access to partner resources and distribution',
        'Industry expertise and credibility',
        'Potential acquisition path',
        'May offer favorable terms for strategic value'
      ],
      cons: [
        'May restrict ability to work with competitors',
        'Potential conflicts of interest',
        'May want significant control or board seat',
        'Can make future fundraising more complex'
      ],
      typicalAmount: `${formatBudgetWithCurrency(250000, currencyCode)} - ${formatBudgetWithCurrency(10000000, currencyCode)}+`
    }
  ];
}

async function generateComplianceChecklistAsync(need: string, area: string): Promise<PlanData['complianceChecklist']> {
  // Try Gemini first for topic + location specific compliance
  if (isGeminiConfigured()) {
    try {
      console.log('🤖 Using Gemini API to fetch topic-specific compliance checklist...');
      const geminiChecklist = await getComplianceChecklistWithGemini(need, area);
      if (geminiChecklist && geminiChecklist.length >= 4) {
        console.log(`✅ Loaded ${geminiChecklist.length} Gemini compliance items`);
        return geminiChecklist;
      }
    } catch (error: any) {
      console.warn('⚠️ Gemini compliance checklist failed, using location-aware static fallback');
    }
  }
  return generateComplianceChecklist(need, area);
}

function generateComplianceChecklist(need: string, area: string): PlanData['complianceChecklist'] {
  const locationKey = getLocationKey(area);
  const locationInfo = getLocationInfo(locationKey);
  const locationName = locationInfo.name;

  // Build location-aware resources
  const registrationBody = (() => {
    const bodies: { [key: string]: string } = {
      'United States': 'Secretary of State / IRS (EIN) / SBA license tool',
      'United Kingdom': 'Companies House (online, ~24 hours) / HMRC',
      'Norway': 'Brønnøysundregistrene / Altinn portal',
      'Sweden': 'Bolagsverket / Skatteverket',
      'Denmark': 'Erhvervsstyrelsen / SKAT',
      'Netherlands': 'KVK (Kamer van Koophandel) / Belastingdienst',
      'Switzerland': 'Commercial Registry (Handelsregister) / cantonal tax authority',
      'Ireland': 'CRO (Companies Registration Office) / Revenue Commissioners',
      'Germany': 'Amtsgericht (Handelsregister) / Finanzamt',
      'France': 'INPI Guichet Unique / Impôts',
      'Spain': 'Registro Mercantil / Agencia Tributaria',
      'Italy': 'Camera di Commercio / Agenzia delle Entrate',
      'Australia': 'ASIC / ABN registration / ATO',
      'Canada': 'Corporations Canada / CRA / provincial registry',
      'India': 'MCA21 (Ministry of Corporate Affairs) / GST portal / FSSAI if applicable',
      'China': 'SAMR (State Administration for Market Regulation) / SAT',
      'Japan': 'Legal Affairs Bureau / NTA (National Tax Agency)',
      'Singapore': 'ACRA (Bizfile+) / IRAS',
      'South Korea': 'Supreme Court Registry / NTS',
      'UAE': 'DED or relevant Free Zone Authority / FTA (Federal Tax Authority)',
      'Saudi Arabia': 'MISA / ZATCA / Ministry of Commerce',
      'Brazil': 'Junta Comercial / Receita Federal / CNPJ',
      'Mexico': 'SAT / Registro Público de Comercio',
      'Argentina': 'AFIP-ARCA / IGJ (Inspección General de Justicia)',
      'South Africa': 'CIPC (Companies and Intellectual Property Commission) / SARS',
      'Nigeria': 'CAC (Corporate Affairs Commission) / FIRS',
      'New Zealand': 'Companies Office / IRD',
      'Israel': 'Rasham Hacharivot (Companies Registrar) / Israel Tax Authority',
      'Poland': 'KRS (National Court Register) / ZUS / US (tax office)',
      'Turkey': 'MERSİS / SGK / GİB (Revenue Administration)',
    };
    return bodies[locationName] || `${locationName} business registration authority / tax authority`;
  })();

  const taxBody = (() => {
    const bodies: { [key: string]: string } = {
      'United States': 'IRS (federal) + state revenue department',
      'United Kingdom': 'HMRC (VAT registration if turnover >£90,000)',
      'Norway': 'Skatteetaten (Tax Administration) / MVA (VAT) registration',
      'Sweden': 'Skatteverket / F-skatt registration',
      'Denmark': 'SKAT / moms (VAT) registration',
      'Netherlands': 'Belastingdienst / BTW (VAT) registration',
      'Switzerland': 'Cantonal tax authority / MWST (VAT) if turnover >CHF 100,000',
      'Ireland': 'Revenue Commissioners / VAT registration if turnover >€40,000',
      'Germany': 'Finanzamt / Umsatzsteuer (VAT) registration',
      'France': 'DGFiP / TVA (VAT) registration',
      'Australia': 'ATO / GST registration if turnover >A$75,000',
      'Canada': 'CRA / GST/HST registration if turnover >C$30,000',
      'India': 'GST registration if turnover >₹20 lakh / Income Tax (PAN/TAN)',
      'Singapore': 'IRAS / GST registration if turnover >S$1 million',
      'UAE': 'FTA / VAT registration if turnover >AED 375,000',
    };
    return bodies[locationName] || `${locationName} tax authority`;
  })();

  const employerBody = (() => {
    const bodies: { [key: string]: string } = {
      'United States': 'State labor dept + workers comp insurer + payroll provider (Gusto/ADP)',
      'United Kingdom': 'HMRC PAYE / workplace pension auto-enrolment (The Pensions Regulator)',
      'Norway': 'NAV (social insurance) / mandatory OTP pension contributions',
      'Sweden': 'Skatteverket / AGS (employer tax account) / mandatory SAF-LO/ITP pension',
      'Denmark': 'Skattestyrelsen / ATP pension contributions / Barsel.dk (parental leave)',
      'Netherlands': 'Belastingdienst / UWV / mandatory pension contributions',
      'Germany': 'Finanzamt / Sozialversicherung (health, pension, care, unemployment) contributions',
      'France': 'URSSAF / cotisations sociales / DPAE (pre-hire declaration)',
      'Australia': 'ATO / superannuation fund (11% SGC) / state-based payroll tax thresholds',
      'Canada': 'CRA / CPP + EI contributions / Workers Compensation Board (provincial)',
      'India': 'EPFO (PF) + ESIC + Professional Tax (state) / contract labour compliance',
      'Singapore': 'IRAS / CPF (17% employer contribution) / MOM work pass administration',
      'UAE': 'MOHRE / GPSSA (pension for UAE nationals) / WPS (Wage Protection System)',
    };
    return bodies[locationName] || `${locationName} social insurance authority / labor department`;
  })();

  const ipBody = (() => {
    const bodies: { [key: string]: string } = {
      'United States': 'USPTO (trademarks/patents) / Copyright Office',
      'United Kingdom': 'IPO (Intellectual Property Office)',
      'Norway': 'Patentstyret (Norwegian Industrial Property Office)',
      'Sweden': 'PRV (Patent- och registreringsverket)',
      'Denmark': 'DKPTO (Danish Patent and Trademark Office)',
      'Netherlands': 'BOIP / EUIPO',
      'Switzerland': 'IGE/IPI (Swiss Federal Institute of Intellectual Property)',
      'Ireland': 'IPOI (Intellectual Property Office of Ireland) / EUIPO',
      'Germany': 'DPMA (Deutsches Patent- und Markenamt)',
      'France': 'INPI (Institut National de la Propriété Industrielle)',
      'Australia': 'IP Australia',
      'Canada': 'CIPO (Canadian Intellectual Property Office)',
      'India': 'CGPDTM (Patent Office) / Trade Marks Registry',
      'Singapore': 'IPOS (Intellectual Property Office of Singapore)',
      'UAE': 'MOCCAE / Ministry of Economy IP department',
      'Japan': 'JPO (Japan Patent Office)',
      'China': 'CNIPA (China National Intellectual Property Administration)',
    };
    return bodies[locationName] || `${locationName} intellectual property office`;
  })();

  return [
    {
      requirement: `Business Entity Registration in ${locationName}`,
      description: `Register your business with the appropriate ${locationName} authority. Choose the correct legal structure for your type of "${need}" operations — this affects liability, taxation, and compliance obligations.`,
      deadline: 'Before commencing any business operations or signing contracts',
      resources: [
        registrationBody,
        `Local commercial lawyer or notary in ${locationName}`,
        `${locationName} chamber of commerce or business support agency`,
        'Online formation services if available in your jurisdiction'
      ]
    },
    {
      requirement: `Tax Registration & VAT/GST in ${locationName}`,
      description: `Register for all applicable taxes in ${locationName} including corporate income tax, VAT/GST (if applicable to "${need}"), and any industry-specific levies. Failure to register on time attracts penalties.`,
      deadline: 'Before making first sale or as required by local threshold rules',
      resources: [
        taxBody,
        `Local certified accountant (CPA/CA/Steuerberater) specialising in ${locationName} tax law`,
        'International tax advisory firm if cross-border operations involved',
        'Industry association for sector-specific tax guidance'
      ]
    },
    {
      requirement: `Industry-Specific Licences & Permits for "${need}"`,
      description: `Identify and obtain all regulatory permits specifically required to operate "${need}" in ${locationName}. Requirements vary significantly by industry — food service, healthcare, finance, construction, and transport all have dedicated licensing regimes.`,
      deadline: 'Before commencing operations — some permits require 4-12+ weeks processing time',
      resources: [
        `${locationName} sector regulator for "${need}" (food authority, health ministry, financial regulator, etc.)`,
        `${locationName} municipality / local council for premises permits and zoning approval`,
        'Trade association or industry body for compliance guidance',
        'Specialist compliance consultant for regulated industries'
      ]
    },
    {
      requirement: `Employer Obligations & Payroll Compliance in ${locationName}`,
      description: `If hiring staff for "${need}" operations in ${locationName}, you must register as an employer, withhold and remit payroll taxes/social contributions, and comply with local employment law including minimum wage, holiday entitlement, and termination rules.`,
      deadline: 'Before hiring first employee',
      resources: [
        employerBody,
        `Employment lawyer in ${locationName} for contract drafting`,
        'Payroll provider or PEO (Professional Employer Organisation) operating in ' + locationName,
        `${locationName} ministry of labour / labour inspectorate resources`
      ]
    },
    {
      requirement: `Business Insurance for "${need}" Operations`,
      description: `Obtain appropriate insurance coverage for your "${need}" business in ${locationName}. This typically includes public/general liability, professional indemnity (if advising clients), property/contents, and employers\' liability (mandatory in most jurisdictions when employing staff).`,
      deadline: 'Before commencing operations or signing lease/client contracts',
      resources: [
        `Commercial insurance broker operating in ${locationName}`,
        'International insurers with local presence (Allianz, AXA, Zurich, Chubb)',
        `${locationName} insurance industry association for recommended brokers`,
        'Industry-specific group insurance schemes via trade associations'
      ]
    },
    {
      requirement: `Intellectual Property Protection in ${locationName}`,
      description: `Register trademarks, patents, and/or copyrights relevant to your "${need}" brand, products, or processes in ${locationName}. Early registration is critical — IP is granted on a first-to-file basis in most jurisdictions.`,
      deadline: 'As soon as brand name, logo, and key product/process are finalised',
      resources: [
        ipBody,
        `IP attorney specialising in ${locationName} and WIPO international filings`,
        'Online trademark search tools to check availability before launch',
        'EUIPO (if operating across EU member states)'
      ]
    },
    {
      requirement: `Data Protection & Privacy Compliance in ${locationName}`,
      description: `If your "${need}" business collects, stores, or processes personal data of customers or employees, you must comply with ${locationName} data protection law (e.g. GDPR in EU/EEA countries, UK GDPR, LGPD in Brazil, PIPL in China, PDPA in Singapore, etc.).`,
      deadline: 'Before collecting any personal data from customers or employees',
      resources: [
        `${locationName} data protection authority (DPA) guidance and resources`,
        'Privacy attorney or DPO (Data Protection Officer) as required',
        'Privacy policy generator + cookie consent tools',
        'GDPR/local-equivalent compliance platforms (OneTrust, Cookiebot, etc.)'
      ]
    },
    {
      requirement: `Health, Safety & Environmental Compliance`,
      description: `Ensure your "${need}" premises and operations comply with ${locationName} workplace health and safety (WHS/OSH) regulations, fire safety standards, and any environmental permits required for your specific type of business activity.`,
      deadline: 'Before staff begin working on premises',
      resources: [
        `${locationName} workplace health and safety regulator`,
        'Fire safety inspector / local fire authority',
        'Environmental agency if operations involve waste, emissions, or chemicals',
        'WHS/EHS consultant for compliance audit and risk assessment'
      ]
    }
  ];
}

function generateLegalComplianceLegacy(need: string, location: string): any[] {
  return [
    {
      requirement: 'Data Privacy & Security Compliance',
      description: 'Comply with data protection laws (GDPR, CCPA, etc.) if collecting customer information',
      deadline: 'Before collecting any customer data',
      resources: [
        'Privacy policy generator tools',
        'Privacy attorney for comprehensive compliance',
        'Industry-specific compliance consultants',
        'Data protection software and platforms'
      ]
    },
    {
      requirement: 'Employment Laws & Regulations',
      description: 'Comply with wage laws, anti-discrimination laws, workplace safety (OSHA), and employee rights',
      deadline: 'Before hiring first employee',
      resources: [
        'Department of Labor website and resources',
        'OSHA compliance assistance',
        'Employment attorney',
        'HR consultant or PEO for guidance'
      ]
    },
    {
      requirement: 'Industry-Specific Regulations',
      description: 'Meet any special requirements for your industry (food service, healthcare, financial services, etc.)',
      deadline: 'Before commencing operations',
      resources: [
        'Industry regulatory agencies',
        'Trade associations and industry groups',
        'Compliance consultants specializing in your industry',
        'Licensing and certification bodies'
      ]
    },
    {
      requirement: 'Contract & Legal Documentation',
      description: 'Create customer agreements, vendor contracts, employee agreements, and terms of service',
      deadline: 'Before engaging customers, vendors, or employees',
      resources: [
        'Business attorney for custom contracts',
        'Contract templates from legal services',
        'Industry standard contracts adapted to your needs',
        'DocuSign or similar for e-signature execution'
      ]
    },
    {
      requirement: 'Financial Reporting & Tax Compliance',
      description: 'Set up proper bookkeeping, file required tax returns, and maintain financial records',
      deadline: 'From day one of operations',
      resources: [
        'Certified Public Accountant (CPA)',
        'Bookkeeping service or software',
        'IRS resources for small business tax',
        'State tax authority for state-specific requirements'
      ]
    }
  ];
}

function generatePlanFinancialProjections(need: string, budget: string, area: string, currency: string) {
  const locationKey = getLocationKey(area);
  const locationInfo = getLocationInfo(locationKey);
  const currentYear = new Date().getFullYear();
  
  // Parse budget safely: extract the FIRST numeric group only
  // (handles ranges like "$100,000 - $500,000" without concatenating all digits)
  const budgetMatch = budget.replace(/,/g, '').match(/\d+/);
  const budgetNum = budgetMatch ? parseInt(budgetMatch[0], 10) : 100000;
  const baseRevenue = budgetNum / 250000; // Estimate starting revenue in $M based on budget
  const growthRate = 0.30; // 30% annual growth (more realistic than 38% for most businesses)
  
  // Generate 5 years of projections
  const yearlyProjections = [];
  for (let i = 0; i < 5; i++) {
    const year = currentYear + i;
    const yearMultiplier = Math.pow(1 + growthRate, i);
    
    const revenue = baseRevenue * yearMultiplier;
    // COGS improves with scale: 35%→31% over 5 years
    const cogsRate = Math.max(0.31, 0.35 - i * 0.01);
    const costOfRevenue = revenue * cogsRate;
    const grossProfit = revenue - costOfRevenue;
    const grossMargin = (grossProfit / revenue) * 100;
    
    // OpEx improves with scale (operating leverage):
    // S&M: 28%→22%, R&D: 15%→12%, G&A: 12%→9%
    const salesMarketing = revenue * Math.max(0.22, 0.28 - i * 0.015);
    const researchDev    = revenue * Math.max(0.12, 0.15 - i * 0.008);
    const generalAdmin   = revenue * Math.max(0.09, 0.12 - i * 0.008);
    const totalOpex = salesMarketing + researchDev + generalAdmin;
    
    const ebitda = grossProfit - totalOpex;
    const ebitdaMargin = (ebitda / revenue) * 100;
    
    const depreciation = revenue * 0.04; // D&A ~4% of revenue
    const ebit = ebitda - depreciation;
    // Interest: debt-ratio approach (15% of revenue × interest rate), realistic ceiling 2%
    // Use corporateTaxRate (a clean numeric field) instead of the string taxRate to avoid
    // falsy-zero bugs (e.g. UAE 0% corporate tax would fall through to 0.21 with `|| 0.21`)
    const taxRate = locationInfo.corporateTaxRate / 100;
    const interestExpense = revenue * Math.min(0.02, (0.065 * 0.15)); // ~0.975% of revenue
    const profitBeforeTax = ebit - interestExpense;
    const taxes = profitBeforeTax > 0 ? profitBeforeTax * taxRate : 0;
    const netIncome = profitBeforeTax - taxes;
    const netMargin = (netIncome / revenue) * 100;
    
    // CapEx reduces as % of revenue as infrastructure matures: 8%→5%
    const capex = revenue * Math.max(0.05, 0.08 - i * 0.008);
    const freeCashFlow = netIncome + depreciation - capex;
    
    yearlyProjections.push({
      year: year.toString(),
      revenue: revenue,
      revenueFormatted: formatBudgetWithCurrency(revenue * 1000000, currency),
      costOfRevenue: costOfRevenue,
      grossProfit: grossProfit,
      grossMargin: grossMargin.toFixed(1),
      salesMarketing: salesMarketing,
      researchDev: researchDev,
      generalAdmin: generalAdmin,
      totalOpex: totalOpex,
      ebitda: ebitda,
      ebitdaFormatted: formatBudgetWithCurrency(ebitda * 1000000, currency),
      ebitdaMargin: ebitdaMargin.toFixed(1),
      netIncome: netIncome,
      netIncomeFormatted: formatBudgetWithCurrency(netIncome * 1000000, currency),
      netMargin: netMargin.toFixed(1),
      freeCashFlow: freeCashFlow,
      freeCashFlowFormatted: formatBudgetWithCurrency(freeCashFlow * 1000000, currency),
      revenueGrowth: i === 0 ? 'Baseline' : `+${(growthRate * 100).toFixed(0)}%`
    });
  }
  
  return {
    yearlyProjections,
    keyMetrics: (() => {
      function mStatus(actual: number, target: number): string {
        const r = actual / target;
        if (r >= 1.1) return 'Exceeding';
        if (r >= 0.85) return 'On Track';
        if (r >= 0.65) return 'Below Target';
        return 'Needs Attention';
      }
      const y5 = yearlyProjections[4];
      const cagrPct       = growthRate * 100;
      const grossMgn      = parseFloat(y5.grossMargin);
      const ebitdaMgn     = parseFloat(y5.ebitdaMargin);
      const netMgn        = parseFloat(y5.netMargin);
      return [
        { metric: 'Revenue CAGR (5-Year)',   value: `${cagrPct.toFixed(0)}%`,  target: '25%', status: mStatus(cagrPct, 25) },
        { metric: 'Gross Margin (Year 5)',   value: `${grossMgn.toFixed(1)}%`, target: '60%', status: mStatus(grossMgn, 60) },
        { metric: 'EBITDA Margin (Year 5)',  value: `${ebitdaMgn.toFixed(1)}%`,target: '15%', status: mStatus(Math.max(ebitdaMgn, 0), 15) },
        { metric: 'Net Margin (Year 5)',     value: `${netMgn.toFixed(1)}%`,   target: '8%',  status: mStatus(Math.max(netMgn, 0), 8) },
        { metric: 'Free Cash Flow (Year 5)', value: y5.freeCashFlowFormatted,  target: 'Positive', status: y5.freeCashFlow > 0 ? 'On Track' : 'Needs Attention' },
        { metric: 'Payback Period',          value: y5.freeCashFlow > 0 ? '3-4 years' : '5+ years', target: '4 years', status: y5.freeCashFlow > 0 ? 'On Track' : 'Needs Attention' },
      ];
    })(),
    assumptions: {
      title: `Financial Projections - ${area}`,
      items: [
        `Starting investment: ${budget} allocated across ${need}`,
        `Revenue CAGR: ${(growthRate * 100).toFixed(0)}% annually as business scales and gains market share`,
        `Gross margin: ${parseFloat(yearlyProjections[0].grossMargin).toFixed(1)}% improving to ${parseFloat(yearlyProjections[4].grossMargin).toFixed(1)}% through scale efficiencies`,
        `EBITDA margin: ${parseFloat(yearlyProjections[0].ebitdaMargin).toFixed(1)}% in Year 1 improving to ${parseFloat(yearlyProjections[4].ebitdaMargin).toFixed(1)}% in Year 5`,
        `Net margin: ${parseFloat(yearlyProjections[0].netMargin).toFixed(1)}% Year 1, ${parseFloat(yearlyProjections[4].netMargin).toFixed(1)}% Year 5`,
        `Tax rate: ${locationInfo.taxRate} (${area} corporate tax rate)`,
        `COGS: Starts at ${(0.35 * 100).toFixed(0)}% improving as operations scale`,
        `OpEx: Sales/Marketing, R&D, G&A reduce as % of revenue with operating leverage`,
        `Capital requirements: Assumes initial ${budget} sufficient to reach break-even`,
        `Currency: All figures in ${currency}`
      ]
    }
  };
}
