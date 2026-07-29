// @ts-nocheck
import { getLocationInfo, getLocationKey, formatBudgetWithCurrency } from './locationData';
import { getRealCompetitors } from './realCompaniesData';

export interface Solution {
  title: string;
  description: string;
  difficulty: 'Low' | 'Medium' | 'High';
  timeline: string;
  estimatedCost: string;
  resources: string;
  implementationSteps: string[];
  localConsiderations: string;
  pros: string[];
  cons: string[];
  expectedOutcome: string;
}

export interface SolutionData {
  problem: string;
  goal: string;
  country: string;
  currency: string;
  solutions: Solution[];
  problemAnalysis: string;
  marketContext: string;
  priorityRecommendation: string;
}

/**
 * Intelligent Solution Generator
 * Analyzes the problem and generates contextual, unique solutions each time
 */
export function generateIntelligentSolutions(
  problem: string,
  goal: string,
  country: string,
  currency: string
): SolutionData {
  const locationKey = getLocationKey(country);
  const locationInfo = getLocationInfo(locationKey);
  
  // Analyze the problem to understand the core issue
  const problemAnalysis = analyzeProblem(problem, goal, country);
  
  // Generate context-aware solutions
  const solutions = generateContextualSolutions(
    problem,
    goal,
    country,
    locationInfo,
    currency,
    problemAnalysis
  );
  
  // Create market context
  const marketContext = generateMarketContext(country, problemAnalysis, locationInfo);
  
  // Generate priority recommendation
  const priorityRecommendation = generatePriorityRecommendation(solutions, problemAnalysis);
  
  return {
    problem,
    goal,
    country,
    currency,
    solutions,
    problemAnalysis: problemAnalysis.summary,
    marketContext,
    priorityRecommendation
  };
}

interface ProblemAnalysis {
  summary: string;
  category: string[];
  urgency: 'Low' | 'Medium' | 'High' | 'Critical';
  keywords: string[];
  specificIssues: string[];
}

function analyzeProblem(problem: string, goal: string, country: string): ProblemAnalysis {
  const pLower = problem.toLowerCase();
  const gLower = goal.toLowerCase();
  const combined = `${pLower} ${gLower}`;
  
  const categories: string[] = [];
  const specificIssues: string[] = [];
  const keywords: string[] = [];
  
  // Marketing/Sales
  if (/(customer|client|lead|sale|marketing|traffic|awareness|acquisition|conversion)/.test(combined)) {
    categories.push('Marketing & Sales');
    if (/no customer|few customer|not enough customer/.test(pLower)) specificIssues.push('customer_acquisition');
    if (/conversion|closing|won.t buy/.test(combined)) specificIssues.push('conversion_rate');
    if (/traffic|visitor|reach/.test(combined)) specificIssues.push('traffic_generation');
    if (/brand|awareness|recognition/.test(combined)) specificIssues.push('brand_awareness');
  }
  
  // Operations/Efficiency
  if (/(efficiency|process|operation|cost|expense|time|productivity|workflow)/.test(combined)) {
    categories.push('Operations');
    if (/too.*cost|expensive|high.*price/.test(pLower)) specificIssues.push('cost_reduction');
    if (/slow|inefficient|waste.*time/.test(pLower)) specificIssues.push('efficiency');
    if (/process|workflow|system/.test(pLower)) specificIssues.push('process_improvement');
  }
  
  // Financial
  if (/(money|cash|funding|capital|revenue|profit|financial|budget)/.test(combined)) {
    categories.push('Financial');
    if (/cash.*flow|running.*out/.test(pLower)) specificIssues.push('cash_flow');
    if (/funding|investment|capital/.test(pLower)) specificIssues.push('funding');
    if (/not.*profitable|losing.*money/.test(pLower)) specificIssues.push('profitability');
  }
  
  // Technology
  if (/(technology|digital|online|website|app|software|automation|tech)/.test(combined)) {
    categories.push('Technology');
    if (/outdated|old.*system|manual/.test(pLower)) specificIssues.push('modernization');
    if (/automation|automate/.test(combined)) specificIssues.push('automation');
  }
  
  // People/Team
  if (/(employee|staff|team|hire|hiring|talent|retention|culture)/.test(combined)) {
    categories.push('Human Resources');
    if (/hire|hiring|find.*people/.test(pLower)) specificIssues.push('hiring');
    if (/retention|turnover|quit/.test(pLower)) specificIssues.push('retention');
    if (/training|skill/.test(pLower)) specificIssues.push('training');
  }
  
  // Product/Service
  if (/(product|service|quality|feature|offering|value)/.test(combined)) {
    categories.push('Product/Service');
    if (/quality|better.*product/.test(pLower)) specificIssues.push('quality');
    if (/differentiat|unique|stand.*out/.test(pLower)) specificIssues.push('differentiation');
  }
  
  // Competition
  if (/(compet|rival|market.*share|losing.*to)/.test(combined)) {
    categories.push('Competition');
    specificIssues.push('competitive_pressure');
  }
  
  // Growth/Scaling
  if (/(grow|scale|expand|increase)/.test(gLower)) {
    categories.push('Growth & Scaling');
    specificIssues.push('growth_strategy');
  }
  
  // Determine urgency
  let urgency: 'Low' | 'Medium' | 'High' | 'Critical' = 'Medium';
  if (/(urgent|critical|failing|bankrupt|desperate|emergency)/.test(pLower)) urgency = 'Critical';
  else if (/(important|soon|quickly|asap)/.test(pLower)) urgency = 'High';
  else if (/(long.*term|eventually|future)/.test(pLower)) urgency = 'Low';
  
  // Extract keywords
  const commonWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'my', 'our', 'we', 'i', 'need', 'want', 'get'];
  const words = combined.split(/\W+/).filter(w => w.length > 3 && !commonWords.includes(w));
  keywords.push(...new Set(words));
  
  return {
    summary: `${categories.join(' + ')} challenge in ${country} market with ${urgency.toLowerCase()} priority`,
    category: categories,
    urgency,
    keywords,
    specificIssues
  };
}

function generateContextualSolutions(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  analysis: ProblemAnalysis
): Solution[] {
  const solutions: Solution[] = [];
  
  // Get real local competitors for context
  const localCompetitors = getRealCompetitors(country, problem, 50000);
  const hasCompetitors = localCompetitors.length > 0;
  
  // Generate solutions based on specific issues identified
  analysis.specificIssues.forEach(issue => {
    const solutionSet = getSolutionsForIssue(issue, problem, goal, country, locationInfo, currency, hasCompetitors, localCompetitors);
    solutions.push(...solutionSet);
  });
  
  // If no specific issues identified, generate general business growth solutions
  if (solutions.length === 0) {
    solutions.push(...getGeneralGrowthSolutions(problem, goal, country, locationInfo, currency, localCompetitors));
  }
  
  // Ensure we have 5-8 diverse solutions
  if (solutions.length < 5) {
    solutions.push(...getComplementarySolutions(problem, goal, country, locationInfo, currency, analysis, solutions));
  }
  
  // Return top 6 most relevant
  return solutions.slice(0, 6);
}

function getSolutionsForIssue(
  issue: string,
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  hasCompetitors: boolean,
  competitors: any[]
): Solution[] {
  const solutions: Solution[] = [];
  
  switch (issue) {
    case 'customer_acquisition':
      solutions.push({
        title: `Hyper-Targeted Local Marketing Campaign for ${country}`,
        description: `Launch a precision-targeted marketing campaign specifically designed for ${country} market conditions. Leverage local insights, cultural nuances, and proven channels to acquire customers efficiently. ${hasCompetitors ? `Study how ${competitors[0]?.name} acquires customers and identify gaps in their approach.` : ''}`,
        difficulty: 'Low',
        timeline: '4-8 weeks to first results',
        estimatedCost: `${formatBudgetWithCurrency(3000, currency)} - ${formatBudgetWithCurrency(8000, currency)} initial budget`,
        resources: '1 marketer or agency + ad budget',
        implementationSteps: [
          `Research ${country} consumer behavior: where do your ideal customers spend time online and offline?`,
          `Identify 2-3 highest-ROI channels for ${country} market (e.g., Google Ads, Facebook, local platforms)`,
          `Create compelling offers that resonate with ${country} cultural values and pain points`,
          'Develop location-specific ad creative with local language, imagery, and messaging',
          `Set up tracking for ${country} conversions (consider ${locationInfo.timezone} timing)`,
          'Launch with small test budget, measure performance daily',
          'Double down on winning channels/messages, cut losing ones ruthlessly',
          `Partner with local influencers or micro-businesses in ${country} for credibility`
        ],
        localConsiderations: `${country} market requires: Understanding local payment preferences (${country === 'India' ? 'UPI, Paytm' : country === 'China' ? 'WeChat Pay, Alipay' : 'local options'}), compliance with ${country} advertising regulations, platform preferences (${country === 'China' ? 'Baidu, WeChat, Douyin' : country === 'Japan' ? 'LINE, Yahoo Japan' : 'Google, Facebook'}), and cultural ad messaging. Tax rate ${locationInfo.taxRate} affects pricing. Average income ${locationInfo.averageSalary} influences affordability.`,
        pros: [
          `Directly addresses "${problem}"`,
          'Measurable ROI from day one',
          'Scalable once you find winning formula',
          'Can start small and test cheaply'
        ],
        cons: [
          'Requires ongoing ad spend',
          'Learning curve to find right channels',
          `${country} market may be saturated in some channels`,
          'Results stop when you stop spending'
        ],
        expectedOutcome: `Within 2-3 months: ${formatBudgetWithCurrency(50, currency)}-${formatBudgetWithCurrency(150, currency)} cost per customer acquisition, 20-40 new customers per month, data on what works in ${country}, and a scalable customer acquisition system. Goal: "${goal}".`
      });
      
      if (hasCompetitors && competitors.length > 0) {
        solutions.push({
          title: `Strategic Partnership with ${competitors[0].name} or Similar ${country} Leaders`,
          description: `Instead of competing directly, explore partnership opportunities with established players like ${competitors[0].name} in ${country}. They have distribution, you bring innovation/differentiation. This accelerates market entry and customer access.`,
          difficulty: 'Medium',
          timeline: '1-3 months to establish',
          estimatedCost: `${formatBudgetWithCurrency(1000, currency)} - ${formatBudgetWithCurrency(5000, currency)} setup + revenue sharing`,
          resources: 'Business development time + legal review',
          implementationSteps: [
            `Research ${competitors.slice(0, 3).map(c => c.name).join(', ')} and identify partnership opportunities`,
            'Develop win-win proposal: what value do you bring to them?',
            `Position as complementary, not competitive (e.g., you serve niche they ignore in ${country})`,
            'Start with small pilot project to build trust',
            'Leverage their customer base, you provide specialized service/product',
            'Formalize agreement with clear terms and metrics',
            'Scale successful partnerships, replicate with others'
          ],
          localConsiderations: `In ${country}, business partnerships require: ${country === 'Japan' || country === 'China' ? 'Significant relationship building, face-to-face meetings, patience' : 'Professional approach with clear mutual benefit'}. Understand ${country} business culture (${locationInfo.businessHours}), legal partnership structures, and tax implications (${locationInfo.taxRate}).`,
          pros: [
            'Fast access to established customer base',
            `Leverage ${competitors[0]?.name}'s brand credibility`,
            'Lower marketing costs',
            'Learn from their market experience'
          ],
          cons: [
            'Revenue sharing reduces margins',
            'Dependent on partner performance',
            'Loss of some control',
            'Potentially complex negotiations'
          ],
          expectedOutcome: `3-6 months: Access to ${competitors[0]?.employeeCount ? Math.floor(parseInt(competitors[0].employeeCount) * 0.1) : '1,000+'} potential customers, ${formatBudgetWithCurrency(20000, currency)}-${formatBudgetWithCurrency(100000, currency)} additional revenue, and market credibility boost. Partnership can 10x customer acquisition vs. going alone.`
        });
      }
      break;
      
    case 'cost_reduction':
      solutions.push({
        title: `Comprehensive Cost Optimization Audit for ${country} Operations`,
        description: `Systematically analyze every expense in your ${country} operations to identify 15-30% cost savings without sacrificing quality. Focus on high-impact, quick-win reductions that directly improve profitability and cash flow.`,
        difficulty: 'Low',
        timeline: '2-6 weeks to implement savings',
        estimatedCost: `${formatBudgetWithCurrency(500, currency)} - ${formatBudgetWithCurrency(2000, currency)} (pays for itself immediately)`,
        resources: 'Management time + possibly consultant',
        implementationSteps: [
          `Categorize all expenses: fixed vs. variable, essential vs. discretionary in ${country}`,
          `Benchmark costs against ${country} market rates for services (${hasCompetitors ? `compare to ${competitors[0]?.name}'s likely structure` : 'industry standards'})`,
          'Renegotiate contracts with existing suppliers - get 3 competing quotes',
          'Identify subscriptions/services no longer providing value - cancel ruthlessly',
          `Explore ${country} bulk buying, cooperative purchasing, or alternative suppliers`,
          'Automate manual tasks to reduce labor costs (while respecting ${country} labor laws)',
          `Review ${country} tax structure with accountant - ensure claiming all deductions (${locationInfo.taxRate} rate)`
        ],
        localConsiderations: `${country}-specific opportunities: Government incentives/subsidies available for your industry, ${country} tax optimization strategies, local vs. imported supplier costs (tariffs, shipping), ${country} labor cost structure (${locationInfo.averageSalary} average), and currency exchange optimization if dealing with international suppliers.`,
        pros: [
          'Immediate impact on profitability',
          'No revenue required - pure savings',
          'One-time effort with ongoing benefits',
          'Improves business resilience'
        ],
        cons: [
          'May require difficult decisions (relationships with suppliers)',
          'Some savings require upfront investment',
          'Team resistance to change',
          'Risk of cutting too deep and harming quality'
        ],
        expectedOutcome: `Within 1-3 months: ${formatBudgetWithCurrency(10000, currency)}-${formatBudgetWithCurrency(50000, currency)} annual savings, improved cash flow, better supplier terms, and optimized cost structure for ${country}. These savings compound annually and can fund growth initiatives.`
      });
      break;
      
    case 'cash_flow':
      solutions.push({
        title: `Cash Flow Rescue Plan: ${country} Funding + Payment Optimization`,
        description: `Immediate actions to improve cash position through ${country}-specific funding sources, payment term optimization, and cash management strategies. Addresses cash flow crisis within 30-60 days.`,
        difficulty: 'Medium',
        timeline: '30-60 days to improve position',
        estimatedCost: `${formatBudgetWithCurrency(1000, currency)} - ${formatBudgetWithCurrency(3000, currency)} professional fees`,
        resources: 'CFO/accountant + application time',
        implementationSteps: [
          `Apply for ${country} government emergency business loans/grants (${country === 'United States' ? 'SBA loans' : country === 'Canada' ? 'BDC financing' : country === 'United Kingdom' ? 'British Business Bank' : country}-specific programs)`,
          'Negotiate payment terms: ask customers for 50% deposits, extend payables to 60 days',
          `Invoice immediately and follow up aggressively (cultural norms in ${country} matter)`,
          'Offer early payment discounts (2% for paying within 10 days)',
          `Review ${country} invoice factoring or receivables financing (3-5% fee for immediate cash)`,
          'Identify non-essential assets to sell for quick cash injection',
          'Implement weekly cash flow forecasting and strict expense approval'
        ],
        localConsiderations: `${country} cash flow solutions: Local banking relationships (${country} banks offer different terms), ${country} government support programs, tax payment deferral options (discuss with ${country} tax authority), and ${country} factoring/alternative finance providers. ${locationInfo.taxRate} tax rate affects cash timing. Interest rates in ${country} currently ${locationInfo.interestRate}%.`,
        pros: [
          'Addresses urgent financial pressure',
          `Multiple ${country} funding sources available`,
          'Improved payment terms reduce future cash stress',
          'Forces financial discipline'
        ],
        cons: [
          'Some options costly (factoring, short-term loans)',
          'Application process time-consuming',
          'May require personal guarantees',
          'Doesn\'t address root profitability issue'
        ],
        expectedOutcome: `30-60 days: ${formatBudgetWithCurrency(10000, currency)}-${formatBudgetWithCurrency(100000, currency)} cash injection, 2-4 week improvement in cash conversion cycle, elimination of immediate financial crisis, and sustainable cash management system for ${country} operations.`
      });
      break;
      
    case 'efficiency':
      solutions.push({
        title: `Lean Operations Implementation for ${country} Market`,
        description: `Apply lean management principles adapted for ${country} business culture to eliminate waste, streamline processes, and improve productivity by 25-40%. Focus on quick wins that team can implement immediately.`,
        difficulty: 'Medium',
        timeline: '6-12 weeks for major improvements',
        estimatedCost: `${formatBudgetWithCurrency(2000, currency)} - ${formatBudgetWithCurrency(5000, currency)} training + tools`,
        resources: 'Team time + process documentation',
        implementationSteps: [
          `Map current workflows - identify bottlenecks specific to ${country} operations`,
          'Measure time spent on each activity (2-week baseline)',
          'Eliminate non-value-adding steps (meetings, approvals, redundant work)',
          `Automate repetitive tasks using ${country}-compatible software`,
          'Standardize best practices and create SOPs',
          `Train team on lean principles (adapted for ${country} work culture)`,
          'Implement continuous improvement meetings (Kaizen approach)'
        ],
        localConsiderations: `${country} efficiency considerations: Labor laws regarding productivity monitoring, cultural attitudes toward change and efficiency (${country === 'Germany' || country === 'Japan' ? 'high process orientation' : 'varies'}), ${country} technology infrastructure reliability, and ${locationInfo.businessHours} workflow optimization. Union/worker council involvement may be required in ${country}.`,
        pros: [
          'Increases capacity without hiring',
          'Improves employee satisfaction (less frustration)',
          'Scalable efficiency as you grow',
          'Competitive advantage through speed'
        ],
        cons: [
          'Team resistance to change',
          'Requires management commitment',
          'Temporary disruption during implementation',
          'Needs ongoing maintenance'
        ],
        expectedOutcome: `3-6 months: 25-40% reduction in process time, 15-25% cost savings, 30-50% increase in capacity, happier team, and faster customer service in ${country} market. Efficiency gains compound over time.`
      });
      break;
  }
  
  return solutions;
}

function getGeneralGrowthSolutions(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[]
): Solution[] {
  return [
    {
      title: `Digital-First Customer Acquisition for ${country}`,
      description: `Build a comprehensive digital presence optimized for ${country} market to attract and convert customers online. ${competitors.length > 0 ? `Differentiate from ${competitors[0]?.name} by focusing on underserved niches.` : 'Establish strong online presence before competitors.'}`,
      difficulty: 'Low',
      timeline: '2-3 months',
      estimatedCost: `${formatBudgetWithCurrency(2000, currency)} - ${formatBudgetWithCurrency(6000, currency)}`,
      resources: 'Marketing person + tools',
      implementationSteps: [
        `Build ${country}-optimized website with local payment options`,
        `Set up ${country} business profiles (Google My Business, local directories)`,
        `Create ${country}-focused social media presence on relevant platforms`,
        'Develop content addressing local customer pain points',
        `Run targeted ads in ${country} using local language and imagery`,
        'Implement email marketing with local segmentation',
        'Track and optimize based on ${country} customer behavior'
      ],
      localConsiderations: `${country} digital landscape: Preferred platforms vary (${country === 'China' ? 'WeChat, Baidu, Douyin' : country === 'Japan' ? 'LINE, Yahoo Japan' : 'Google, Facebook, Instagram'}), mobile-first crucial in ${country}, data privacy laws (${country === 'Germany' ? 'strict GDPR' : country === 'United States' ? 'CCPA in California' : country}-specific}), and ${locationInfo.timezone} optimal posting times.`,
      pros: [
        'Scalable customer acquisition',
        'Measurable ROI',
        'Reaches customers where they are',
        '24/7 marketing presence'
      ],
      cons: [
        'Competitive online space',
        'Requires consistent effort',
        'Platform algorithm changes',
        'Takes 2-3 months for momentum'
      ],
      expectedOutcome: `3-6 months: 100-300% increase in online visibility, 30-60 qualified leads monthly, ${formatBudgetWithCurrency(20000, currency)}-${formatBudgetWithCurrency(80000, currency)} additional revenue, and sustainable growth engine for ${country}.`
    }
  ];
}

function getComplementarySolutions(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  analysis: ProblemAnalysis,
  existingSolutions: Solution[]
): Solution[] {
  // Add solutions that complement what's already recommended
  const complementary: Solution[] = [];
  
  complementary.push({
    title: `Customer Referral Program for ${country}`,
    description: `Launch a structured referral program that rewards existing customers for bringing new business. Leverage ${country} social networks and cultural trust patterns to drive word-of-mouth growth.`,
    difficulty: 'Low',
    timeline: '2-3 weeks to launch',
    estimatedCost: `${formatBudgetWithCurrency(500, currency)} - ${formatBudgetWithCurrency(2000, currency)} + rewards`,
    resources: 'Simple tracking system',
    implementationSteps: [
      `Design incentive: "${formatBudgetWithCurrency(20, currency)} for you, ${formatBudgetWithCurrency(20, currency)} for friend" or similar`,
      `Choose tracking method suitable for ${country} (app, codes, manual)`,
      'Create easy sharing mechanism (WhatsApp, email, social)',
      `Train team to ask for referrals at key moments in ${country} customer journey`,
      'Promote program to existing customers',
      'Track and reward promptly',
      'Optimize based on participation rates'
    ],
    localConsiderations: `${country} referral dynamics: Cultural norms around recommendations (${country === 'Japan' || country === 'China' ? 'personal reputation very important' : 'varies'}), gift-giving customs affect reward design, ${country} privacy laws regarding data sharing, and ${country} tax treatment of rewards (${locationInfo.taxRate}).`,
    pros: [
      'Low-cost customer acquisition',
      'High-quality referred customers',
      'Strengthens existing customer relationships',
      'Scalable and measurable'
    ],
    cons: [
      'Dependent on customer satisfaction',
      'Reward costs accumulate',
      'Requires promotion to work',
      'Can be gamed if poorly designed'
    ],
    expectedOutcome: `3-6 months: 20-35% of new customers from referrals, ${formatBudgetWithCurrency(30, currency)}-${formatBudgetWithCurrency(70, currency)} cost per acquisition (vs. ${formatBudgetWithCurrency(100, currency)}-${formatBudgetWithCurrency(300, currency)} paid ads), and self-sustaining growth loop in ${country}.`
  });
  
  return complementary;
}

function generateMarketContext(country: string, analysis: ProblemAnalysis, locationInfo: any): string {
  const contexts: { [key: string]: string } = {
    'United States': `The US market is highly competitive with sophisticated consumers and mature digital infrastructure. Success requires clear differentiation, excellent execution, and often significant marketing spend. ${locationInfo.gdpGrowthRate}% GDP growth creates opportunities, but customer acquisition costs are rising across all channels.`,
    'United Kingdom': `The UK market values quality, sustainability, and brand heritage. Post-Brexit regulatory independence creates both opportunities and complexities. London offers global reach; regional markets offer lower competition. ${locationInfo.gdpGrowthRate}% GDP growth with strong fintech and professional services sectors.`,
    'Canada': `Canada's market combines North American business practices with distinct cultural identity. Government support for innovation is strong (SR&ED tax credits, grants). Bilingual requirements in some provinces. ${locationInfo.gdpGrowthRate}% GDP growth, stable regulatory environment, and resource-rich economy.`,
    'India': `India is one of the world's fastest-growing markets (${locationInfo.gdpGrowthRate}% GDP growth) with massive scale opportunity but execution complexity. Digital India initiatives transformed accessibility. Price sensitivity high, but middle class growing rapidly. Mobile-first essential. Government's Make in India and PLI schemes support domestic production.`,
    'China': `China offers massive scale but requires deep local expertise, partnerships, and regulatory navigation. ${locationInfo.gdpGrowthRate}% GDP growth with sophisticated digital ecosystem (WeChat, Alipay). Government policy significantly influences sectors. Local partners often essential. Consumer sophistication very high in tier-1 cities.`,
    'Germany': `Germany values engineering excellence, precision, and sustainability. Mittelstand culture supports SME success. ${locationInfo.gdpGrowthRate}% GDP growth with strong manufacturing and industrial base. Regulatory compliance important. Works councils and labor protections influence operations.`,
    'Japan': `Japan's market rewards quality, consistency, and patience. Relationship-building essential. Aging population creates opportunities in healthcare, automation. ${locationInfo.gdpGrowthRate}% GDP growth, extremely sophisticated consumers, and strong IP protection. Distribution channels can be complex.`,
    'Australia': `Australia combines developed market sophistication with proximity to Asia-Pacific. ${locationInfo.gdpGrowthRate}% GDP growth, high quality of life, and stable regulatory environment. Geographic spread creates logistics challenges. Strong in fintech, mining, education.`,
    'Brazil': `Brazil's large domestic market (${locationInfo.gdpGrowthRate}% GDP growth) offers significant opportunities despite economic volatility. Complex tax system (multiple levels). Strong local players in most sectors. Digital adoption growing rapidly. Currency fluctuations impact pricing.`,
    'Singapore': `Singapore is a highly sophisticated, business-friendly market serving as Asia-Pacific hub. ${locationInfo.gdpGrowthRate}% GDP growth, excellent infrastructure, and strong government support for innovation. High costs but excellent rule of law. Gateway to Southeast Asia.`,
  };
  
  return contexts[country] || `${country} presents unique market opportunities with ${locationInfo.gdpGrowthRate}% GDP growth. Success requires understanding local business culture, regulatory environment, and customer preferences. Research local competitors and adapt proven business models to ${country} context.`;
}

function generatePriorityRecommendation(solutions: Solution[], analysis: ProblemAnalysis): string {
  const urgency = analysis.urgency;
  const topSolution = solutions[0];
  
  if (urgency === 'Critical' || urgency === 'High') {
    return `⚠️ URGENT: Given the ${urgency.toLowerCase()} nature of your situation, implement "${topSolution.title}" IMMEDIATELY (within next 7-14 days). This addresses your core challenge directly and can show results fastest. Simultaneously, begin planning ${solutions[1]?.title} as your medium-term strategy. Don't try to do everything at once - focus creates results.`;
  } else {
    return `🎯 RECOMMENDED APPROACH: Start with "${topSolution.title}" as your primary strategy over next 60-90 days. This offers the best balance of impact, feasibility, and cost for your situation. Once showing results, layer in "${solutions[1]?.title}" to diversify your growth engines. The solutions are ordered by priority - implement sequentially for best results.`;
  }
}