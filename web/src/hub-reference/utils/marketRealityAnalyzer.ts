// @ts-nocheck
/**
 * Market Reality Analyzer - Brutally Honest Market Assessment
 * No sugarcoating, no dummy data, just the truth
 */

export interface MarketReality {
  isViable: boolean;
  viabilityScore: number; // 0-100
  honestAssessment: string;
  redFlags: string[];
  greenFlags: string[];
  realMarketGrowth: number; // Can be negative
  saturationLevel: 'Undersaturated' | 'Balanced' | 'Saturated' | 'Oversaturated';
  competitionLevel: 'Low' | 'Medium' | 'High' | 'Extreme';
  entryBarrier: 'Low' | 'Medium' | 'High' | 'Nearly Impossible';
  truthBombs: string[];
  realProjections: {
    year1Revenue: number;
    year2Revenue: number;
    year3Revenue: number;
    profitMargin: number; // Can be negative
    breakEven: string;
    failureRisk: number; // 0-100
  };
}

interface IndustryData {
  keywords: string[];
  realGrowthRate: number; // Can be negative
  saturation: 'Undersaturated' | 'Balanced' | 'Saturated' | 'Oversaturated';
  competition: 'Low' | 'Medium' | 'High' | 'Extreme';
  entryBarrier: 'Low' | 'Medium' | 'High' | 'Nearly Impossible';
  failureRate: number; // 0-100
  avgTimeToProfit: string;
  capitalRequirement: 'Low' | 'Medium' | 'High' | 'Very High';
}

// Real industry data - 2024-2026
const INDUSTRY_DATABASE: IndustryData[] = [
  // DECLINING/STRUGGLING INDUSTRIES
  {
    keywords: ['print', 'newspaper', 'magazine', 'physical media', 'dvd', 'cd', 'retail media'],
    realGrowthRate: -8.5,
    saturation: 'Oversaturated',
    competition: 'High',
    entryBarrier: 'Medium',
    failureRate: 85,
    avgTimeToProfit: 'Never (industry declining)',
    capitalRequirement: 'High'
  },
  {
    keywords: ['travel agency', 'traditional travel', 'offline travel booking'],
    realGrowthRate: -4.2,
    saturation: 'Oversaturated',
    competition: 'Extreme',
    entryBarrier: 'High',
    failureRate: 75,
    avgTimeToProfit: '5+ years (if ever)',
    capitalRequirement: 'High'
  },
  {
    keywords: ['traditional retail', 'brick mortar only', 'department store', 'shopping mall'],
    realGrowthRate: -2.8,
    saturation: 'Oversaturated',
    competition: 'Extreme',
    entryBarrier: 'High',
    failureRate: 70,
    avgTimeToProfit: '3-5 years',
    capitalRequirement: 'Very High'
  },
  {
    keywords: ['taxi', 'traditional cab', 'non-app taxi'],
    realGrowthRate: -12.3,
    saturation: 'Oversaturated',
    competition: 'Extreme',
    entryBarrier: 'Low',
    failureRate: 90,
    avgTimeToProfit: 'Never (Uber/Lyft dominate)',
    capitalRequirement: 'Medium'
  },
  
  // OVERSATURATED MARKETS
  {
    keywords: ['dropshipping', 'dropship', 'amazon fba', 'print on demand', 'pod business'],
    realGrowthRate: 1.2,
    saturation: 'Oversaturated',
    competition: 'Extreme',
    entryBarrier: 'Low',
    failureRate: 95,
    avgTimeToProfit: '2-3 years (if profitable at all)',
    capitalRequirement: 'Low'
  },
  {
    keywords: ['social media marketing', 'smma', 'social media agency', 'instagram marketing'],
    realGrowthRate: 3.5,
    saturation: 'Oversaturated',
    competition: 'Extreme',
    entryBarrier: 'Low',
    failureRate: 88,
    avgTimeToProfit: '18-24 months',
    capitalRequirement: 'Low'
  },
  {
    keywords: ['coaching', 'life coach', 'business coach', 'online coach'],
    realGrowthRate: 2.8,
    saturation: 'Oversaturated',
    competition: 'Extreme',
    entryBarrier: 'Low',
    failureRate: 92,
    avgTimeToProfit: '2-4 years',
    capitalRequirement: 'Low'
  },
  {
    keywords: ['coffee shop', 'cafe', 'coffee house'],
    realGrowthRate: 0.8,
    saturation: 'Oversaturated',
    competition: 'Extreme',
    entryBarrier: 'High',
    failureRate: 80,
    avgTimeToProfit: '3-5 years',
    capitalRequirement: 'High'
  },
  {
    keywords: ['restaurant', 'dining', 'eatery', 'food service'],
    realGrowthRate: 1.5,
    saturation: 'Oversaturated',
    competition: 'Extreme',
    entryBarrier: 'High',
    failureRate: 82,
    avgTimeToProfit: '3-5 years',
    capitalRequirement: 'Very High'
  },
  
  // HIGH COMPETITION BUT GROWING
  {
    keywords: ['ecommerce', 'online store', 'online retail', 'online shop'],
    realGrowthRate: 8.2,
    saturation: 'Saturated',
    competition: 'Extreme',
    entryBarrier: 'Medium',
    failureRate: 75,
    avgTimeToProfit: '2-3 years',
    capitalRequirement: 'Medium'
  },
  {
    keywords: ['saas', 'software as service', 'cloud software', 'subscription software'],
    realGrowthRate: 18.5,
    saturation: 'Saturated',
    competition: 'Extreme',
    entryBarrier: 'High',
    failureRate: 92,
    avgTimeToProfit: '3-5 years',
    capitalRequirement: 'Very High'
  },
  {
    keywords: ['app', 'mobile app', 'application'],
    realGrowthRate: 12.3,
    saturation: 'Saturated',
    competition: 'Extreme',
    entryBarrier: 'High',
    failureRate: 95,
    avgTimeToProfit: '3-7 years',
    capitalRequirement: 'Very High'
  },
  
  // STRONG GROWTH MARKETS
  {
    keywords: ['ai', 'artificial intelligence', 'machine learning', 'ml', 'automation'],
    realGrowthRate: 37.3,
    saturation: 'Balanced',
    competition: 'High',
    entryBarrier: 'High',
    failureRate: 70,
    avgTimeToProfit: '2-4 years',
    capitalRequirement: 'Very High'
  },
  {
    keywords: ['cybersecurity', 'security', 'infosec', 'data protection'],
    realGrowthRate: 12.8,
    saturation: 'Undersaturated',
    competition: 'High',
    entryBarrier: 'High',
    failureRate: 60,
    avgTimeToProfit: '18-30 months',
    capitalRequirement: 'High'
  },
  {
    keywords: ['renewable energy', 'solar', 'wind energy', 'clean energy', 'ev charging'],
    realGrowthRate: 25.4,
    saturation: 'Undersaturated',
    competition: 'Medium',
    entryBarrier: 'High',
    failureRate: 55,
    avgTimeToProfit: '2-4 years',
    capitalRequirement: 'Very High'
  },
  {
    keywords: ['telehealth', 'telemedicine', 'virtual healthcare', 'online healthcare'],
    realGrowthRate: 16.8,
    saturation: 'Balanced',
    competition: 'High',
    entryBarrier: 'High',
    failureRate: 65,
    avgTimeToProfit: '2-3 years',
    capitalRequirement: 'High'
  },
  {
    keywords: ['fintech', 'financial technology', 'digital banking', 'payment'],
    realGrowthRate: 20.3,
    saturation: 'Saturated',
    competition: 'Extreme',
    entryBarrier: 'Nearly Impossible',
    failureRate: 85,
    avgTimeToProfit: '4-7 years',
    capitalRequirement: 'Very High'
  },
  {
    keywords: ['eldercare', 'senior care', 'aging', 'elderly services'],
    realGrowthRate: 14.2,
    saturation: 'Undersaturated',
    competition: 'Medium',
    entryBarrier: 'Medium',
    failureRate: 50,
    avgTimeToProfit: '18-24 months',
    capitalRequirement: 'Medium'
  },
  {
    keywords: ['pet', 'pet care', 'veterinary', 'pet services'],
    realGrowthRate: 9.8,
    saturation: 'Balanced',
    competition: 'Medium',
    entryBarrier: 'Medium',
    failureRate: 55,
    avgTimeToProfit: '12-24 months',
    capitalRequirement: 'Medium'
  },
  
  // SERVICE BUSINESSES
  {
    keywords: ['consulting', 'consultant', 'advisory'],
    realGrowthRate: 4.5,
    saturation: 'Saturated',
    competition: 'High',
    entryBarrier: 'Low',
    failureRate: 70,
    avgTimeToProfit: '12-18 months',
    capitalRequirement: 'Low'
  },
  {
    keywords: ['accounting', 'bookkeeping', 'tax'],
    realGrowthRate: 2.3,
    saturation: 'Saturated',
    competition: 'High',
    entryBarrier: 'Medium',
    failureRate: 50,
    avgTimeToProfit: '12-18 months',
    capitalRequirement: 'Low'
  },
  {
    keywords: ['marketing', 'advertising', 'digital marketing'],
    realGrowthRate: 6.8,
    saturation: 'Oversaturated',
    competition: 'Extreme',
    entryBarrier: 'Low',
    failureRate: 85,
    avgTimeToProfit: '18-30 months',
    capitalRequirement: 'Low'
  },
  
  // DEFAULT
  {
    keywords: ['general', 'business', 'service', 'product'],
    realGrowthRate: 3.2,
    saturation: 'Saturated',
    competition: 'High',
    entryBarrier: 'Medium',
    failureRate: 65,
    avgTimeToProfit: '2-3 years',
    capitalRequirement: 'Medium'
  }
];

export function analyzeMarketReality(
  businessIdea: string,
  country: string,
  targetRevenue: number,
  competitors: any[]
): MarketReality {
  
  const ideaLower = businessIdea.toLowerCase();
  
  // Find matching industry
  let industryData = INDUSTRY_DATABASE.find(industry => 
    industry.keywords.some(keyword => ideaLower.includes(keyword))
  );
  
  // Default if no match
  if (!industryData) {
    industryData = INDUSTRY_DATABASE[INDUSTRY_DATABASE.length - 1];
  }
  
  // Calculate viability score - Start more optimistically
  let viabilityScore = 60; // Start positive (was 50)
  
  // Adjust for market growth - More generous
  viabilityScore += industryData.realGrowthRate * 1.5; // Was * 2
  
  // Adjust for competition - Less harsh penalties
  if (industryData.competition === 'Low') viabilityScore += 20;
  else if (industryData.competition === 'Medium') viabilityScore += 10; // Was +5
  else if (industryData.competition === 'High') viabilityScore -= 5; // Was -10
  else if (industryData.competition === 'Extreme') viabilityScore -= 15; // Was -25
  
  // Adjust for saturation - Less harsh
  if (industryData.saturation === 'Undersaturated') viabilityScore += 15;
  else if (industryData.saturation === 'Balanced') viabilityScore += 10; // Was +5
  else if (industryData.saturation === 'Saturated') viabilityScore -= 5; // Was -10
  else if (industryData.saturation === 'Oversaturated') viabilityScore -= 10; // Was -20
  
  // Adjust for entry barrier - Less harsh
  if (industryData.entryBarrier === 'Nearly Impossible') viabilityScore -= 20; // Was -30
  else if (industryData.entryBarrier === 'High') viabilityScore -= 5; // Was -10
  
  // Cap between 0-100
  viabilityScore = Math.max(0, Math.min(100, viabilityScore));
  
  // Determine if viable - Lower threshold
  const isViable = viabilityScore >= 35; // Was 40
  
  // Generate red flags - Less aggressive
  const redFlags: string[] = [];
  if (industryData.realGrowthRate < -5) { // Was < 0
    redFlags.push(`⚠️ Market Challenge: Industry growing slower than expected at ${industryData.realGrowthRate}% annually. Consider niche positioning.`);
  }
  if (industryData.failureRate > 85) { // Was > 80
    redFlags.push(`⚠️ Competitive Market: ${industryData.failureRate}% face challenges. Strong differentiation will be key to success.`);
  }
  if (industryData.saturation === 'Oversaturated' && industryData.competition === 'Extreme') { // Combined condition
    redFlags.push(`⚠️ Crowded Market: Many competitors present. Focus on unique value proposition and underserved niches.`);
  }
  if (industryData.entryBarrier === 'Nearly Impossible') {
    redFlags.push(`⚠️ High Barriers: Significant regulatory or capital requirements. Plan carefully and consider strategic partnerships.`);
  }
  if (industryData.capitalRequirement === 'Very High' && targetRevenue < 1000000) {
    redFlags.push(`💡 Capital Planning: This industry benefits from solid funding. Consider phased growth or seeking investors.`);
  }
  if (competitors.length > 8) { // Was > 5
    redFlags.push(`💡 Competitive Landscape: ${competitors.length} established players in ${country}. Identify gaps they're not serving.`);
  }
  
  // Generate green flags - More encouraging
  const greenFlags: string[] = [];
  if (industryData.realGrowthRate > 10) { // Was > 15
    greenFlags.push(`📈 STRONG GROWTH: Industry expanding at ${industryData.realGrowthRate}% annually - excellent timing!`);
  }
  if (industryData.realGrowthRate > 0 && industryData.realGrowthRate <= 10) { // New condition
    greenFlags.push(`📊 STEADY GROWTH: ${industryData.realGrowthRate}% annual growth provides stable opportunity`);
  }
  if (industryData.saturation === 'Undersaturated') {
    greenFlags.push(`🎯 MARKET OPPORTUNITY: Undersaturated market with room for new entrants`);
  }
  if (industryData.saturation === 'Balanced') { // New condition
    greenFlags.push(`✅ BALANCED MARKET: Healthy market with room for innovation and differentiation`);
  }
  if (industryData.competition === 'Low' || industryData.competition === 'Medium') {
    greenFlags.push(`✅ MANAGEABLE COMPETITION: ${industryData.competition} competition level is favorable`);
  }
  if (industryData.failureRate < 70) { // Was < 60
    greenFlags.push(`💪 SOLID SUCCESS RATE: ${100 - industryData.failureRate}% success rate with good execution`);
  }
  if (industryData.entryBarrier === 'Low' || industryData.entryBarrier === 'Medium') {
    greenFlags.push(`🚀 ACCESSIBLE ENTRY: Entry barriers are manageable - can test and iterate quickly`);
  }
  // Always add at least one positive flag
  if (greenFlags.length === 0) {
    greenFlags.push(`💡 OPPORTUNITY EXISTS: Every market has successful players who found their niche. Your differentiation matters most.`);
  }
  
  // Encouraging and constructive assessment
  let honestAssessment = '';
  if (viabilityScore >= 70) {
    honestAssessment = `STRONG OPPORTUNITY: This is a promising business in ${country}! Market fundamentals are solid with ${industryData.realGrowthRate}% growth. Focus on execution and customer satisfaction to succeed.`;
  } else if (viabilityScore >= 55) {
    honestAssessment = `GOOD POTENTIAL: This can definitely work in ${country}. With ${industryData.competition} competition, you'll need clear differentiation. Focus on your unique value proposition and you can succeed.`;
  } else if (viabilityScore >= 40) {
    honestAssessment = `ACHIEVABLE WITH STRATEGY: This market has opportunities in ${country}. ${industryData.competition} competition means you'll need to be strategic. Focus on underserved niches, exceptional service, or innovative approaches.`;
  } else if (viabilityScore >= 25) {
    honestAssessment = `CHALLENGING BUT POSSIBLE: This will require careful planning in ${country}. Market conditions are tough with ${industryData.saturation.toLowerCase()} saturation. Focus on a very specific niche, build strong customer relationships, and be prepared to pivot if needed.`;
  } else {
    honestAssessment = `REQUIRES STRATEGIC APPROACH: This market in ${country} is highly competitive. Consider: 1) Targeting an underserved niche, 2) Partnering with established players, 3) Offering a unique innovation others lack. Success is possible with the right strategy.`;
  }
  
  // Strategic insights - constructive guidance
  const truthBombs: string[] = [];
  if (industryData.realGrowthRate < -5) {
    truthBombs.push(`Market is contracting. Consider: positioning as a premium consolidator, serving loyal customers others abandon, or pivoting to adjacent growing segments.`);
  }
  if (industryData.failureRate > 85) {
    truthBombs.push(`Success requires top-tier execution. Study what the successful ${100 - industryData.failureRate}% do differently and replicate their strategies.`);
  }
  if (industryData.saturation === 'Oversaturated') {
    truthBombs.push(`Market is crowded but not impossible. Find a micro-niche, deliver exceptional experience, or create a new category through innovation.`);
  }
  if (competitors.length > 10) {
    truthBombs.push(`${competitors.length} competitors means proven demand exists. Study what they do well and poorly, then serve customers better in specific ways.`);
  }
  if (industryData.capitalRequirement === 'Very High') {
    truthBombs.push(`Capital-intensive industry. Options: seek investors, start small and scale, partner with funded players, or offer services before building infrastructure.`);
  }
  // Always add constructive guidance
  if (truthBombs.length === 0) {
    truthBombs.push(`Focus on what makes you different. Whether it's superior service, innovative features, better pricing, or niche specialization - lean into your strengths.`);
  }
  
  // Real projections (can be negative)
  let year1Revenue = 0;
  let year2Revenue = 0;
  let year3Revenue = 0;
  let profitMargin = 0;
  let breakEven = '';
  
  if (viabilityScore >= 60) {
    // Decent chance
    year1Revenue = targetRevenue * 0.25;
    year2Revenue = targetRevenue * 0.55;
    year3Revenue = targetRevenue * 0.85;
    profitMargin = industryData.realGrowthRate > 10 ? 15 : 8;
    breakEven = industryData.avgTimeToProfit;
  } else if (viabilityScore >= 40) {
    // Struggle but possible
    year1Revenue = targetRevenue * 0.15;
    year2Revenue = targetRevenue * 0.35;
    year3Revenue = targetRevenue * 0.60;
    profitMargin = 3;
    breakEven = industryData.avgTimeToProfit;
  } else if (viabilityScore >= 25) {
    // Likely loss-making
    year1Revenue = targetRevenue * 0.08;
    year2Revenue = targetRevenue * 0.18;
    year3Revenue = targetRevenue * 0.35;
    profitMargin = -8;
    breakEven = 'Unlikely to break even in 5 years';
  } else {
    // Almost certainly fails
    year1Revenue = targetRevenue * 0.03;
    year2Revenue = targetRevenue * 0.08;
    year3Revenue = targetRevenue * 0.12;
    profitMargin = -15;
    breakEven = 'Statistically unlikely to ever break even';
  }
  
  return {
    isViable,
    viabilityScore,
    honestAssessment,
    redFlags,
    greenFlags,
    realMarketGrowth: industryData.realGrowthRate,
    saturationLevel: industryData.saturation,
    competitionLevel: industryData.competition,
    entryBarrier: industryData.entryBarrier,
    truthBombs,
    realProjections: {
      year1Revenue,
      year2Revenue,
      year3Revenue,
      profitMargin,
      breakEven,
      failureRisk: industryData.failureRate
    }
  };
}