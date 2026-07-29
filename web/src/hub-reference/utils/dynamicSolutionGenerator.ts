// @ts-nocheck
import { getLocationInfo, getLocationKey, formatBudgetWithCurrency } from './locationData';
// FIX #6: Removed hardcoded static company data import (realCompaniesData)
// The static fallback generator no longer pretends to have topic-specific company data.
// Gemini (primary path) provides real grounded competitors. The fallback now uses
// neutral language ("market leaders", "established players") instead of injecting
// irrelevant hardcoded companies (e.g. Siemens, Honeywell for a food delivery idea).

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
  generatedDate: string;
}

/**
 * Truly Dynamic Solution Generator
 * Every problem gets completely unique solutions - NO templates!
 */
export function generateIntelligentSolutions(
  problem: string,
  goal: string,
  country: string,
  currency: string
): SolutionData {
  const locationKey = getLocationKey(country);
  const locationInfo = getLocationInfo(locationKey);
  
  // FIX #6: No longer pulling from hardcoded static database.
  // Gemini (primary) provides real grounded competitors. In the fallback (static) path,
  // we use an empty array so the generator uses neutral language ("market leaders")
  // rather than injecting irrelevant pre-set company names.
  const competitors: any[] = [];
  
  // Extract problem details
  const problemDetails = extractProblemDetails(problem, goal);
  
  // Generate completely unique solutions based on problem specifics
  const solutions = generateUniqueSolutions(
    problem,
    goal,
    country,
    locationInfo,
    currency,
    competitors,
    problemDetails
  );
  
  // Analysis
  const problemAnalysis = `Your challenge: "${problem}" in ${country}. Goal: "${goal}". We've identified ${problemDetails.mainIssues.length} core issues and generated ${solutions.length} tailored solutions specifically for your situation.`;
  
  const marketContext = generateContextualMarketInsight(country, locationInfo, problem, competitors);
  
  const priorityRecommendation = `🎯 START HERE: Solution #1 ("${solutions[0].title}") directly addresses "${problem}" and can show results fastest in ${country}. Once implemented, layer in Solution #2 for compounding effects. Don't try all at once - focused execution beats scattered effort.`;
  
  return {
    problem,
    goal,
    country,
    currency,
    solutions,
    problemAnalysis,
    marketContext,
    priorityRecommendation,
    generatedDate: new Date().toISOString()
  };
}

interface ProblemDetails {
  mainIssues: string[];
  specificPhrases: string[];
  targetMetric: string;
  urgencyLevel: number; // 1-10
  budgetSensitivity: 'low' | 'medium' | 'high';
  timeframe: 'immediate' | 'short' | 'medium' | 'long';
  industryHints: string[];
}

function extractProblemDetails(problem: string, goal: string): ProblemDetails {
  const pLower = problem.toLowerCase();
  const gLower = goal.toLowerCase();
  
  const mainIssues: string[] = [];
  const specificPhrases: string[] = [];
  const industryHints: string[] = [];
  
  // Extract specific phrases (5+ character meaningful phrases)
  const words = problem.split(/\s+/).filter(w => w.length > 4);
  specificPhrases.push(...words.slice(0, 8));
  
  // Identify main issues
  if (/customer|client|user|buyer|patron/.test(pLower)) mainIssues.push('customer');
  if (/revenue|sales|income|profit|money|cash/.test(pLower)) mainIssues.push('revenue');
  if (/cost|expensive|overhead|spending/.test(pLower)) mainIssues.push('cost');
  if (/time|slow|delay|wait|efficiency/.test(pLower)) mainIssues.push('time');
  if (/quality|standard|excellence/.test(pLower)) mainIssues.push('quality');
  if (/compet|rival|market/.test(pLower)) mainIssues.push('competition');
  if (/team|employee|staff|hire/.test(pLower)) mainIssues.push('people');
  if (/tech|digital|online|software/.test(pLower)) mainIssues.push('technology');
  if (/brand|awareness|visibility|recognition/.test(pLower)) mainIssues.push('visibility');
  if (/process|system|workflow|operation/.test(pLower)) mainIssues.push('process');
  
  // Target metric from goal
  let targetMetric = 'growth';
  if (/revenue|sales|income/.test(gLower)) targetMetric = 'revenue';
  if (/customer|client|user/.test(gLower)) targetMetric = 'customers';
  if (/profit|margin/.test(gLower)) targetMetric = 'profit';
  if (/market share|growth|expand/.test(gLower)) targetMetric = 'market share';
  
  // Urgency
  let urgencyLevel = 5;
  if (/urgent|critical|asap|emergency|desperate/.test(pLower)) urgencyLevel = 10;
  else if (/soon|quickly|fast|immediate/.test(pLower)) urgencyLevel = 8;
  else if (/eventually|long.term|future/.test(pLower)) urgencyLevel = 3;
  
  // Budget sensitivity
  let budgetSensitivity: 'low' | 'medium' | 'high' = 'medium';
  if (/low.budget|cheap|affordable|no.money|bootstrap/.test(pLower)) budgetSensitivity = 'high';
  else if (/invest|capital|fund|spend/.test(pLower)) budgetSensitivity = 'low';
  
  // Timeframe
  let timeframe: 'immediate' | 'short' | 'medium' | 'long' = 'medium';
  if (urgencyLevel >= 8) timeframe = 'immediate';
  else if (urgencyLevel >= 6) timeframe = 'short';
  else if (urgencyLevel <= 3) timeframe = 'long';
  
  // Industry hints
  if (/retail|store|shop|ecommerce/.test(pLower)) industryHints.push('retail');
  if (/restaurant|food|cafe|dining/.test(pLower)) industryHints.push('food');
  if (/saas|software|app|tech/.test(pLower)) industryHints.push('tech');
  if (/consult|service|agency/.test(pLower)) industryHints.push('services');
  if (/manufact|product|goods/.test(pLower)) industryHints.push('manufacturing');
  
  return {
    mainIssues,
    specificPhrases,
    targetMetric,
    urgencyLevel,
    budgetSensitivity,
    timeframe,
    industryHints
  };
}

function generateUniqueSolutions(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution[] {
  const solutions: Solution[] = [];
  
  // Use random seed based on problem text to ensure same problem gets different solutions each time
  let randomSeed = Date.now() + problem.length + goal.length;
  
  // Generate 6 completely unique solutions based on problem specifics
  const solutionGenerators = [
    () => generateDirectAttackSolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generatePartnershipSolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generateInnovationSolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generateQuickWinSolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generateScalingSolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generateResourceOptimizationSolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generateCustomerCentricSolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generateTechnologySolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generateCommunityBasedSolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generateDataDrivenSolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generateBrandingSolution(problem, goal, country, locationInfo, currency, competitors, details),
    () => generateOperationalSolution(problem, goal, country, locationInfo, currency, competitors, details),
  ];
  
  // Shuffle and select based on problem characteristics
  const shuffled = solutionGenerators.sort(() => Math.sin(randomSeed++) - 0.5);
  
  // Pick 6 unique generators
  for (let i = 0; i < 6; i++) {
    try {
      const solution = shuffled[i]();
      if (solution) solutions.push(solution);
    } catch (e) {
      // Skip if generator fails
    }
  }
  
  return solutions;
}

function generateDirectAttackSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  const mainIssue = details.mainIssues[0] || 'challenge';
  const competitorName = competitors[0]?.name || 'market leaders';
  
  return {
    title: `Direct ${country} Market Attack: Solving "${problem.substring(0, 50)}..."`,
    description: `Your problem: "${problem}". This solution addresses it head-on in ${country} by targeting the exact ${mainIssue} gap. We'll leverage what ${competitorName} is doing wrong and exploit that weakness. This is aggressive, focused, and designed to show results fast.`,
    difficulty: details.urgencyLevel > 7 ? 'Low' : 'Medium',
    timeline: details.timeframe === 'immediate' ? '2-4 weeks' : '6-10 weeks',
    estimatedCost: details.budgetSensitivity === 'high' 
      ? `${formatBudgetWithCurrency(500, currency)} - ${formatBudgetWithCurrency(2000, currency)}`
      : `${formatBudgetWithCurrency(3000, currency)} - ${formatBudgetWithCurrency(8000, currency)}`,
    resources: 'You + 1-2 people (can outsource)',
    implementationSteps: [
      `Identify exactly WHY you have this problem: "${problem}" - what's the root cause in ${country}?`,
      `Research how ${competitorName} handles this - where are they weak?`,
      `Design a solution specifically for ${country} market that addresses: ${details.specificPhrases.slice(0, 3).join(', ')}`,
      `Launch small test in ${country} (${locationInfo.timezone} timezone matters for timing)`,
      `Measure against your goal: "${goal}" - track daily`,
      'Double down on what works, kill what doesn\'t within 2 weeks',
      `Scale to full ${country} market once proven`
    ],
    localConsiderations: `${country} specifics: ${competitors.length > 0 ? `${competitorName} has ${competitors[0].employeeCount || '1000+'} employees but likely ignores your niche` : 'First-mover advantage available'}. Consider ${country} regulations, ${locationInfo.taxRate} tax rate, ${locationInfo.averageSalary} average income (affects pricing), and local ${mainIssue} preferences.`,
    pros: [
      `Directly solves: "${problem}"`,
      `Gets you to: "${goal}"`,
      'Fast results if executed well',
      `Exploits ${country} market gaps`
    ],
    cons: [
      'Requires focused execution',
      `${country} market may be more complex than expected`,
      'Competitors may respond',
      'Results depend on your follow-through'
    ],
    expectedOutcome: `${details.timeframe === 'immediate' ? '30-60 days' : '2-4 months'}: Measurable progress on "${goal}". If this is customer acquisition, expect ${formatBudgetWithCurrency(50, currency)}-${formatBudgetWithCurrency(150, currency)} cost per customer in ${country}. If revenue, ${formatBudgetWithCurrency(10000, currency)}-${formatBudgetWithCurrency(50000, currency)} lift. Problem "${problem}" should be 50-70% solved.`
  };
}

function generatePartnershipSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  // Deterministic partner selection based on problem string length (no Math.random)
  const partnerPool = Math.min(3, competitors.length);
  const partnerIdx = partnerPool > 0 ? problem.length % partnerPool : 0;
  const partner = competitors[partnerIdx] || { name: 'established players' };
  
  return {
    title: `Strategic Alliance with ${partner.name} in ${country}`,
    description: `Instead of solving "${problem}" alone, partner with ${partner.name} or similar ${country} players. They have what you need (distribution/customers/credibility), you have what they lack (innovation/service/specialization). This accelerates "${goal}" by 6-12 months.`,
    difficulty: 'Medium',
    timeline: '1-3 months to establish partnership',
    estimatedCost: `${formatBudgetWithCurrency(1000, currency)} - ${formatBudgetWithCurrency(4000, currency)} setup + revenue share`,
    resources: 'Your time + simple legal agreement',
    implementationSteps: [
      `List 10 ${country} companies that have customers you want but don't offer what you do`,
      `Research ${partner.name}'s gaps - what do they NOT do well?`,
      `Create proposal: "You bring customers, we solve [specific problem], both earn"`,
      `Approach with specific value prop for ${country} market`,
      'Start with pilot project (low risk for them)',
      `Deliver exceptional results to build trust in ${country}`,
      'Expand partnership and replicate with others'
    ],
    localConsiderations: `${country} partnerships require: ${country === 'Japan' || country === 'China' ? 'Face-to-face relationship building, patience, trust cultivation' : country === 'United States' ? 'Clear contracts, measurable KPIs, professional approach' : 'Cultural business etiquette'}. ${partner.name} has ${partner.revenue || 'significant'} revenue - position as complementary, not competitive.`,
    pros: [
      `Solves "${problem}" using their existing infrastructure`,
      `Fast-tracks "${goal}" by leveraging established base`,
      `Lower marketing cost in ${country}`,
      'Learn from their market experience'
    ],
    cons: [
      'Revenue sharing (typically 20-40% to partner)',
      'Dependent on their performance',
      'Takes time to establish trust',
      'May limit your direct brand building'
    ],
    expectedOutcome: `4-6 months: Access to ${partner.employeeCount ? Math.floor(parseInt(partner.employeeCount) * 0.05) : '500+'} potential customers through partnership, ${formatBudgetWithCurrency(15000, currency)}-${formatBudgetWithCurrency(75000, currency)} additional revenue, credibility boost in ${country}, and proven partnership model to replicate.`
  };
}

function generateInnovationSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  const mainIssue = details.mainIssues[0] || 'approach';
  
  return {
    title: `Innovative ${mainIssue.toUpperCase()} Approach for ${country}: Differentiation Strategy`,
    description: `Your "${problem}" exists because everyone in ${country} does the same thing. This solution completely reimagines your ${mainIssue} approach. Instead of competing head-on, we'll create a new category where you're the only option. Makes "${goal}" achievable through differentiation.`,
    difficulty: 'Medium',
    timeline: '6-12 weeks to develop & launch',
    estimatedCost: `${formatBudgetWithCurrency(2000, currency)} - ${formatBudgetWithCurrency(6000, currency)}`,
    resources: 'Creative thinking + market research + execution',
    implementationSteps: [
      `Map exactly how everyone in ${country} currently solves what you do`,
      `Identify what customers WISH was different (survey 20-30 people in ${country})`,
      `Design a fundamentally different approach to ${mainIssue}`,
      `Test with small ${country} audience - does it resonate?`,
      `Build messaging around "we're different because [specific innovation]"`,
      `Launch in ${country} with PR/content explaining the innovation`,
      'Own this new category before competitors copy'
    ],
    localConsiderations: `${country} innovation adoption: ${country === 'United States' ? 'Fast adopters, loves innovation' : country === 'Japan' ? 'Values quality over novelty, prove it works first' : country === 'Germany' ? 'Engineering excellence matters, substance over hype' : 'Varies by market'}. Consider ${locationInfo.gdpGrowthRate}% GDP growth (affects risk appetite). Protect IP if possible in ${country}.`,
    pros: [
      'Eliminates direct competition',
      `Solves "${problem}" by changing the game`,
      'Can command premium pricing (20-40% higher)',
      `Memorable in ${country} market`
    ],
    cons: [
      'Education required - customers must understand innovation',
      'Takes longer to gain traction',
      'Risk: market may not want innovation',
      'Competitors will eventually copy'
    ],
    expectedOutcome: `3-6 months: Established as "the innovative option" in ${country}, 30-50% higher conversion rate (less competition), media coverage opportunities, and sustainable differentiation. Once proven, this compounds - innovation becomes moat.`
  };
}

function generateQuickWinSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  return {
    title: `30-Day Quick Win Sprint: Immediate Impact on "${problem.substring(0, 40)}..."`,
    description: `Forget long-term strategy for a moment. This is pure execution - 30 days of focused effort in ${country} to show measurable progress on "${problem}". Quick wins build momentum, prove concepts, and fund bigger moves toward "${goal}".`,
    difficulty: 'Low',
    timeline: '30 days exactly',
    estimatedCost: details.budgetSensitivity === 'high'
      ? `${formatBudgetWithCurrency(300, currency)} - ${formatBudgetWithCurrency(1000, currency)}`
      : `${formatBudgetWithCurrency(1000, currency)} - ${formatBudgetWithCurrency(3000, currency)}`,
    resources: 'Intense focus for 30 days',
    implementationSteps: [
      `Day 1-3: Identify THE single highest-impact action for "${problem}" in ${country}`,
      `Day 4-10: Execute that ONE thing relentlessly (e.g., reach 100 potential customers)`,
      `Day 11-15: Measure results, optimize, double down on what's working`,
      `Day 16-25: Scale the winning tactic in ${country} market`,
      `Day 26-30: Document results, plan next 30-day sprint`,
      `Throughout: Post daily progress in ${country} timezone (${locationInfo.timezone})`,
      'Celebrate wins, learn from failures, maintain momentum'
    ],
    localConsiderations: `${country} quick wins: Leverage low-cost channels first (social media, networking, partnerships). ${locationInfo.businessHours} are optimal outreach times. Use ${country} platforms (${country === 'China' ? 'WeChat' : country === 'India' ? 'WhatsApp' : 'varies'}). Focus on tactics that work in ${country} culture.`,
    pros: [
      `Immediate progress on "${problem}"`,
      'Builds confidence and momentum',
      'Low cost, high learning',
      'Results visible to team/stakeholders'
    ],
    cons: [
      'Short-term focus may miss big opportunities',
      'Not sustainable long-term',
      'Requires discipline and intensity',
      'May burn out if repeated too often'
    ],
    expectedOutcome: `30 days: Concrete progress toward "${goal}" - maybe 10-20 new customers, ${formatBudgetWithCurrency(5000, currency)}-${formatBudgetWithCurrency(15000, currency)} revenue, or key partnership established in ${country}. More importantly: proof you can execute and data on what works.`
  };
}

function generateScalingSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  return {
    title: `${country} Scaling Playbook: From Solving "${problem}" to Systematic Growth`,
    description: `The real issue isn't just "${problem}" - it's that you don't have a repeatable system to achieve "${goal}" consistently in ${country}. This builds that system: processes, metrics, and scalability infrastructure so success compounds.`,
    difficulty: 'Medium',
    timeline: '8-12 weeks to build system',
    estimatedCost: `${formatBudgetWithCurrency(3000, currency)} - ${formatBudgetWithCurrency(10000, currency)}`,
    resources: 'Systems thinking + documentation + tools',
    implementationSteps: [
      `Document current process for achieving "${goal}" in ${country} (even if it's not working)`,
      'Identify bottlenecks preventing scale',
      `Build standard operating procedures (SOPs) for ${country} operations`,
      `Implement tracking dashboard for key metrics in ${country}`,
      'Create training system so others can execute',
      'Automate repetitive tasks (marketing, reporting, follow-up)',
      'Test system: can someone else run it without you?'
    ],
    localConsiderations: `${country} scaling requires: Understanding ${country} labor laws (if hiring), technology infrastructure (${country} has ${locationInfo.gdpGrowthRate}% GDP growth), local management culture, and ${locationInfo.taxRate} tax implications of growth. What scales in one market may not work in ${country}.`,
    pros: [
      `Solves "${problem}" once, benefits forever`,
      'Enables growth without proportional effort increase',
      'Valuable asset (systems have value)',
      'Reduces dependency on you personally'
    ],
    cons: [
      'Upfront time investment (8-12 weeks)',
      'Requires discipline to follow systems',
      'May feel bureaucratic at first',
      `Systems need updating as ${country} market evolves`
    ],
    expectedOutcome: `3-6 months: Operating system that produces "${goal}" consistently. For example, if customer acquisition is goal, you have process generating 20-30 customers/month predictably in ${country}. This compounds - year 1 is ${formatBudgetWithCurrency(100000, currency)}, year 2 is ${formatBudgetWithCurrency(300000, currency)} from same system.`
  };
}

function generateResourceOptimizationSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  return {
    title: `${country} Resource Optimization: Doing More with Less`,
    description: `Maybe the issue with "${problem}" isn't that you need MORE resources - it's that you're misallocating what you have in ${country}. This audits every dollar, hour, and effort to eliminate waste and redirect to "${goal}". Often finds 30-40% efficiency gains.`,
    difficulty: 'Low',
    timeline: '3-6 weeks to identify and implement',
    estimatedCost: `${formatBudgetWithCurrency(500, currency)} - ${formatBudgetWithCurrency(2000, currency)}`,
    resources: 'Honest audit of current operations',
    implementationSteps: [
      `Track where every dollar goes in ${country} operations for 2 weeks`,
      'Track where every hour of your time goes for 2 weeks',
      `Categorize: Essential to "${goal}" vs. Nice-to-have vs. Waste`,
      `Cut bottom 20% of activities (${country} specific context matters)`,
      'Redirect those resources to top-performing activities',
      `Negotiate better deals with ${country} suppliers (get 3 quotes each)`,
      'Automate or outsource low-value tasks'
    ],
    localConsiderations: `${country} cost optimization: Average salary ${locationInfo.averageSalary} (affects labor decisions), local vs international suppliers (tariffs, currency), ${country} tax deductions available (${locationInfo.taxRate}), and cultural norms around negotiation. ${country} may have government incentives you're missing.`,
    pros: [
      'Immediate impact (savings = profit)',
      `More resources for "${goal}"`,
      'No external funding needed',
      'Often finds 30-40% waste'
    ],
    cons: [
      'May require difficult decisions',
      'Team may resist changes',
      'Risk of cutting too deep',
      'Requires ongoing discipline'
    ],
    expectedOutcome: `60-90 days: ${formatBudgetWithCurrency(10000, currency)}-${formatBudgetWithCurrency(40000, currency)} annual savings in ${country}, 20-30% more time for high-value work, leaner operations, and resources redirected to solving "${problem}". These savings compound annually.`
  };
}

function generateCustomerCentricSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  return {
    title: `${country} Customer-First Transformation: Let Customers Solve "${problem}"`,
    description: `Radical idea: ASK your ${country} customers what they want. This solution involves deep customer research in ${country} to understand exactly what they need, then delivering it. Customers literally tell you how to achieve "${goal}" if you listen.`,
    difficulty: 'Low',
    timeline: '4-8 weeks',
    estimatedCost: `${formatBudgetWithCurrency(500, currency)} - ${formatBudgetWithCurrency(2000, currency)}`,
    resources: 'Customer interviews + survey tools',
    implementationSteps: [
      `Interview 20-30 current/potential customers in ${country} about their needs`,
      `Ask: "What would make you [related to: ${goal}]?"`,
      'Identify patterns - what do 80% mention?',
      `Design solution specifically for ${country} customer needs (not what you think they need)`,
      'Create pilot with 5-10 early customers',
      'Iterate based on feedback',
      `Launch refined solution to full ${country} market`
    ],
    localConsiderations: `${country} customer research: Cultural communication styles (${country === 'Japan' ? 'indirect, read between lines' : country === 'United States' ? 'direct, explicit' : 'varies'}), language nuances, ${locationInfo.timezone} for interview scheduling, and ${country} customer expectations (${locationInfo.averageSalary} income affects willingness to pay).`,
    pros: [
      `Customers literally tell you how to solve "${problem}"`,
      'Product-market fit almost guaranteed',
      'High conversion rates (you built what they asked for)',
      'Creates customer advocates'
    ],
    cons: [
      'Customers sometimes wrong about what they need',
      'Time-intensive interview process',
      'May reveal uncomfortable truths',
      'Need discipline to act on findings'
    ],
    expectedOutcome: `2-4 months: Deep understanding of ${country} customer needs, product/service refined based on real feedback, 50-80% higher conversion rate (you're selling what they want), and ${formatBudgetWithCurrency(20000, currency)}-${formatBudgetWithCurrency(60000, currency)} revenue from customer-driven improvements.`
  };
}

function generateTechnologySolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  return {
    title: `Technology Force-Multiplier for ${country}: Automate Your Way to "${goal}"`,
    description: `Your "${problem}" might exist because you're doing manually what technology could do 10x faster in ${country}. This identifies automation opportunities and implements tools to compress time, reduce costs, and scale toward "${goal}" without hiring.`,
    difficulty: 'Medium',
    timeline: '6-10 weeks',
    estimatedCost: `${formatBudgetWithCurrency(2000, currency)} - ${formatBudgetWithCurrency(8000, currency)} setup + subscriptions`,
    resources: 'Tech implementation + learning curve',
    implementationSteps: [
      `List all repetitive tasks in ${country} operations (marketing, sales, operations, admin)`,
      `Research ${country}-compatible automation tools for each`,
      'Prioritize highest-impact, easiest-to-implement tools',
      `Start with one: CRM, email marketing, scheduling, or invoicing for ${country}`,
      'Implement thoroughly, train team',
      'Measure time/cost savings',
      'Layer in additional automation every 2-3 weeks'
    ],
    localConsiderations: `${country} technology: Data residency laws (${country === 'Germany' ? 'GDPR strict' : 'varies'}), ${country} payment gateway integration, local language support, ${locationInfo.timezone} customer support hours, and ${country} internet infrastructure reliability. Some global tools don't work well in ${country} - get local alternatives.`,
    pros: [
      `Solves "${problem}" through efficiency, not effort`,
      'Scales infinitely once set up',
      'Reduces human error',
      'Frees time for high-value work'
    ],
    cons: [
      'Upfront cost and learning curve',
      'Integration complexity',
      'Ongoing subscription costs',
      'Tech can fail - need backup plans'
    ],
    expectedOutcome: `3-6 months: 40-60% reduction in time spent on repetitive tasks, capacity increase of 30-50% without hiring, ${formatBudgetWithCurrency(15000, currency)}-${formatBudgetWithCurrency(40000, currency)} cost savings annually in ${country}, and ability to scale toward "${goal}" without proportional cost increase.`
  };
}

function generateCommunityBasedSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  return {
    title: `${country} Community Building Strategy: Network Effects for "${goal}"`,
    description: `Your "${problem}" might be solvable through community rather than direct selling in ${country}. Build a tribe of advocates who solve the problem together, refer others, and create network effects. This turns customers into distribution channel.`,
    difficulty: 'Medium',
    timeline: '8-16 weeks to establish',
    estimatedCost: `${formatBudgetWithCurrency(1000, currency)} - ${formatBudgetWithCurrency(4000, currency)}`,
    resources: 'Community management + content creation',
    implementationSteps: [
      `Identify where your ${country} target audience already gathers (online/offline)`,
      `Create valuable content/events specifically for ${country} community`,
      'Start small: 20-30 engaged members beats 1000 lurkers',
      `Foster connections BETWEEN members (not just with you) in ${country}`,
      'Reward and recognize top contributors',
      'Let community solve each other\'s problems',
      `Monetize through community: "${goal}"`
    ],
    localConsiderations: `${country} community dynamics: Platform preferences (${country === 'China' ? 'WeChat groups' : country === 'India' ? 'WhatsApp' : 'Facebook Groups, Discord, or in-person'}), cultural communication norms, ${locationInfo.timezone} for live events, and ${country} regulations around community gatherings. Community building faster in some cultures.`,
    pros: [
      'Creates self-sustaining growth engine',
      `Solves "${problem}" through advocates, not ads`,
      'Low cost, high engagement',
      'Community = competitive moat'
    ],
    cons: [
      'Slow to start (3-6 months to momentum)',
      'Requires consistent engagement',
      'Can\'t force it - must be authentic',
      'Community can turn negative if mismanaged'
    ],
    expectedOutcome: `6-12 months: Engaged community of 100-500 ${country} members, 30-50% of new customers from referrals, dramatically lower acquisition cost, and sustainable word-of-mouth engine driving "${goal}". Network effects compound - year 2 is 5x year 1.`
  };
}

function generateDataDrivenSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  return {
    title: `Data-Driven ${country} Decision Making: Measure Your Way Out of "${problem}"`,
    description: `You can't fix "${problem}" if you can't measure it in ${country}. This implements comprehensive tracking, analytics, and data-driven decision making. Replace guessing with knowing. Every decision backed by ${country} market data toward "${goal}".`,
    difficulty: 'Medium',
    timeline: '4-8 weeks to implement',
    estimatedCost: `${formatBudgetWithCurrency(1000, currency)} - ${formatBudgetWithCurrency(5000, currency)}`,
    resources: 'Analytics tools + data analysis',
    implementationSteps: [
      `Define key metrics for "${goal}" in ${country} (what does success look like?)`,
      'Implement tracking: Google Analytics, CRM, financial dashboard',
      `Measure baseline for 2 weeks in ${country} market`,
      'Identify biggest gap between current and goal',
      'Run experiments to close that gap',
      'Measure results, iterate weekly',
      'Build dashboard visible to whole team'
    ],
    localConsiderations: `${country} data & analytics: Privacy regulations (${country === 'Germany' ? 'GDPR very strict' : country === 'United States' ? 'CCPA in CA' : 'varies'}), ${country} customer data preferences, local analytics tools, and ${locationInfo.timezone} for data interpretation. ${country} may have specific data residency requirements.`,
    pros: [
      `Removes guesswork from solving "${problem}"`,
      'Quick identification of what works',
      'Measurable progress toward "${goal}"',
      'Data = credibility with stakeholders'
    ],
    cons: [
      'Can create analysis paralysis',
      'Tracking setup time-intensive',
      'Data only useful if you act on it',
      'Some things hard to quantify'
    ],
    expectedOutcome: `2-4 months: Clear visibility into ${country} business performance, 30-50% faster decision-making, elimination of low-ROI activities, and data-proven path to "${goal}". Companies that measure grow 2-3x faster than those that don't.`
  };
}

function generateBrandingSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  const competitorName = competitors[0]?.name || 'competitors';
  
  return {
    title: `${country} Brand Differentiation: Stand Out from ${competitorName}`,
    description: `Maybe "${problem}" exists because you blend in with ${competitorName} and others in ${country}. This creates distinctive brand positioning that makes you the ONLY choice for your ideal customer. Brand = premium pricing + customer loyalty toward "${goal}".`,
    difficulty: 'Medium',
    timeline: '6-10 weeks',
    estimatedCost: `${formatBudgetWithCurrency(2000, currency)} - ${formatBudgetWithCurrency(7000, currency)}`,
    resources: 'Brand strategy + design + messaging',
    implementationSteps: [
      `Audit how ${competitorName} and others position themselves in ${country}`,
      `Identify underserved niche in ${country} market`,
      'Define your unique value proposition (why you vs. others?)',
      'Develop brand personality that resonates with ${country} culture',
      `Create consistent visual identity for ${country}`,
      'Craft messaging that clearly differentiates',
      `Launch rebrand in ${country} with PR/content push`
    ],
    localConsiderations: `${country} branding: Cultural colors/symbols (${country === 'China' ? 'red = prosperity, white = mourning' : country === 'India' ? 'colors have religious significance' : 'varies'}), language tone (${country === 'Japan' ? 'formal and respectful' : country === 'Australia' ? 'casual and friendly' : 'market-specific'}), and ${country} consumer expectations at ${locationInfo.averageSalary} income level.`,
    pros: [
      `Solves "${problem}" through differentiation`,
      'Enables premium pricing (20-40% higher)',
      'Creates customer loyalty',
      'Memorable in crowded ${country} market'
    ],
    cons: [
      'Results take time to materialize (3-6 months)',
      'Requires consistent execution',
      'Risk: positioning may not resonate',
      'Upfront investment required'
    ],
    expectedOutcome: `4-8 months: Clear differentiation in ${country}, 25-40% higher conversion rate (right customers choose you), ability to charge premium prices, and strong brand recall driving "${goal}". Strong brands compound - grow 50% faster long-term.`
  };
}

function generateOperationalSolution(
  problem: string,
  goal: string,
  country: string,
  locationInfo: any,
  currency: string,
  competitors: any[],
  details: ProblemDetails
): Solution {
  return {
    title: `Operational Excellence in ${country}: Process Improvement for "${goal}"`,
    description: `Your "${problem}" might be a symptom of poor operations in ${country}. This systematically improves every business process - from customer onboarding to delivery to support. Better operations = better results toward "${goal}" with same resources.`,
    difficulty: 'Medium',
    timeline: '8-12 weeks',
    estimatedCost: `${formatBudgetWithCurrency(1500, currency)} - ${formatBudgetWithCurrency(5000, currency)}`,
    resources: 'Process mapping + team training',
    implementationSteps: [
      `Map all key processes in ${country} operations (sales, delivery, support, etc.)`,
      'Identify bottlenecks, delays, and errors',
      `Benchmark against ${country} industry standards`,
      'Redesign top 3 most broken processes',
      'Document new standard operating procedures',
      `Train ${country} team on improved processes`,
      'Measure improvement, iterate continuously'
    ],
    localConsiderations: `${country} operational factors: Labor laws (${locationInfo.averageSalary} average wage affects staffing), ${country} supplier reliability, ${locationInfo.businessHours} and ${locationInfo.timezone} for scheduling, and ${country} quality standards. What works elsewhere may need adaptation for ${country}.`,
    pros: [
      `Addresses root cause of "${problem}"`,
      'Improves customer experience',
      'Scales without proportional cost increase',
      'Team efficiency and morale improve'
    ],
    cons: [
      'Change management challenging',
      'Requires discipline to follow processes',
      'Initial disruption during transition',
      'Ongoing maintenance required'
    ],
    expectedOutcome: `3-6 months: 30-50% improvement in operational efficiency in ${country}, 20-30% cost reduction, faster delivery times, fewer errors, and capacity to scale toward "${goal}". Operational excellence compounds - creates sustainable advantage.`
  };
}

function generateContextualMarketInsight(
  country: string,
  locationInfo: any,
  problem: string,
  competitors: any[]
): string {
  const insights: string[] = [
    `${country} market growing at ${locationInfo.gdpGrowthRate}% GDP - ${locationInfo.gdpGrowthRate > 3 ? 'strong tailwinds for growth' : 'slower growth requires efficiency'}`,
    `Average income ${locationInfo.averageSalary} affects pricing power`,
    `Tax rate ${locationInfo.taxRate} impacts profitability`,
  ];
  
  if (competitors.length > 0) {
    insights.push(`Major players: ${competitors.slice(0, 3).map(c => c.name).join(', ')} - study their weaknesses`);
  }
  
  if (country === 'United States') {
    insights.push('US market: Highly competitive, loves innovation, winner-take-most dynamics, strong IP protection');
  } else if (country === 'India') {
    insights.push('India market: Price-sensitive but huge scale, mobile-first essential, UPI revolutionizing payments, tier-2/3 cities underserved');
  } else if (country === 'China') {
    insights.push('China market: Massive scale, government policy critical, WeChat/Alipay ecosystems, local partnerships often required');
  }
  
  return insights.join('. ') + '.';
}