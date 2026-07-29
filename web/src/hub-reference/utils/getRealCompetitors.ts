// @ts-nocheck
/**
 * Enhanced Competitor Discovery Service
 * Ensures industry-specific, location-specific, and topic-specific competitors
 */

import { callWithGrounding } from './geminiService';

/**
 * Extract industry keywords from business idea/topic
 */
function extractIndustryKeywords(topic: string): string[] {
  const words = topic.toLowerCase().split(' ');
  
  // Industry-specific keywords to look for
  const industryTerms = [
    'ecommerce', 'e-commerce', 'marketplace', 'platform', 'app', 'software', 'saas',
    'delivery', 'food', 'restaurant', 'grocery', 'retail', 'shopping',
    'fitness', 'health', 'wellness', 'medical', 'healthcare',
    'education', 'learning', 'training', 'course', 'teaching',
    'fintech', 'finance', 'banking', 'payment', 'insurance',
    'travel', 'booking', 'hotel', 'tourism', 'transportation',
    'consulting', 'agency', 'service', 'solutions',
    'ai', 'ml', 'blockchain', 'iot', 'cloud', 'analytics',
    'fashion', 'clothing', 'apparel', 'beauty', 'cosmetics',
    'real estate', 'property', 'rental', 'housing',
    'entertainment', 'media', 'streaming', 'content', 'gaming',
    'social', 'networking', 'community', 'dating',
    'manufacturing', 'logistics', 'supply chain', 'warehouse'
  ];
  
  const keywords: string[] = [];
  
  // Extract matching industry terms
  for (const term of industryTerms) {
    if (topic.toLowerCase().includes(term)) {
      keywords.push(term);
    }
  }
  
  // If no industry terms found, use first 2-3 meaningful words
  if (keywords.length === 0) {
    const stopWords = ['a', 'an', 'the', 'for', 'to', 'in', 'on', 'at', 'with', 'by', 'from', 'of', 'and', 'or'];
    const meaningfulWords = words.filter(w => !stopWords.includes(w) && w.length > 2);
    keywords.push(...meaningfulWords.slice(0, 3));
  }
  
  return keywords.slice(0, 5); // Return top 5 keywords max
}

/**
 * Get real, industry-specific competitors for a topic and location
 */
export async function getRealCompetitorsWithGemini(
  topic: string,
  location: string,
  currency: string
): Promise<any[]> {
  console.log(`🏢 [COMPETITOR SEARCH] Topic: "${topic}" | Location: ${location}`);
  
  // Extract industry keywords
  const industryKeywords = extractIndustryKeywords(topic);
  console.log(`🏷️ [COMPETITOR SEARCH] Industry keywords: ${industryKeywords.join(', ')}`);
  
  // Parse location
  const locationParts = location.split(',').map(p => p.trim());
  const country = locationParts[locationParts.length - 1] || location;
  const state = locationParts.length >= 2 ? locationParts[1] : '';
  const city = locationParts.length >= 3 ? locationParts[2] : '';
  
  const timestamp = new Date().toISOString();
  
  const prompt = `You are a market research analyst with real-time Google Search access. Find the TOP 8-12 REAL companies that are DIRECT COMPETITORS in the "${topic}" industry operating in ${location} as of Q1 2026 (January–March 2026).

**🎯 BUSINESS CONTEXT:**
Topic/Industry: "${topic}"
Industry Keywords: ${industryKeywords.join(', ')}
Location: ${location}
Search Timestamp: ${timestamp}
⚠️ ALL DATA MUST BE CURRENT AS OF Q1 2026. Include the most recent funding rounds, product launches, acquisitions, and market moves from 2025–2026.

**🔍 CRITICAL SEARCH REQUIREMENTS:**

1. **INDUSTRY RELEVANCE IS MANDATORY:**
   - Companies MUST operate in the SAME INDUSTRY as "${topic}"
   - If topic is "food delivery app" → Find ONLY food delivery companies (Zomato, Swiggy, Uber Eats, DoorDash, etc.)
   - If topic is "e-commerce platform" → Find ONLY e-commerce/marketplace companies (Amazon, Flipkart, Etsy, etc.)
   - If topic is "fitness app" → Find ONLY fitness/health tech companies (MyFitnessPal, Strava, Peloton, etc.)
   - If topic is "AI chatbot SaaS" → Find ONLY AI/SaaS companies (Intercom, Drift, ChatGPT, etc.)
   - If topic is "real estate platform" → Find ONLY real estate tech companies (Zillow, Housing.com, 99acres, etc.)
   - DO NOT return generic IT consulting firms (TCS, Infosys, Wipro) unless topic is specifically "IT consulting"
   - DO NOT return unrelated companies from other industries

2. **GOOGLE SEARCH STRATEGY - Execute ALL these searches:**
   a. "${topic} companies ${country} 2025 2026"
   b. "${industryKeywords[0]} ${industryKeywords[1]} market leaders ${country}"
   c. "top ${topic} businesses ${state || city || country}"
   d. "${topic} competitors ${location}"
   e. "best ${industryKeywords.join(' ')} companies ${country}"
   f. "${topic} market share ${country} 2026"
   g. "${topic} funding round 2025 2026 ${country}"
   h. "${topic} acquisition merger ${country} 2025 2026"

3. **LOCATION REQUIREMENTS:**
   - ALL companies MUST have operations in ${location}
   - PRIORITIZE companies headquartered in ${country}
   - Include international companies ONLY if they actively serve ${location} market
   - For ${country}: Focus on ${country}-based companies or verified ${country} operations
   - If a company doesn't serve ${location}, DO NOT include it

4. **VALIDATION RULES:**
   - Each company MUST be relevant to "${topic}" industry
   - Each company MUST be verifiable via Google search
   - Each company MUST compete in the same market as "${topic}"
   - Companies should offer similar products/services to what "${topic}" describes

**📋 REQUIRED JSON FORMAT - Return ONLY this array:**

[
  {
    "name": "Exact Company Name",
    "tier": "Market Leader" | "Major Challenger" | "Growing Competitor" | "Niche Player",
    "marketShare": "X.X%",
    "marketShareTrend": "Growing" | "Stable" | "Declining",
    "revenue": "${currency} XXX million",
    "employeeCount": "X,XXX or X-Y range",
    "headquarters": "City, ${country}",
    "founded": 2015,
    "strengths": ["Real strength 1 specific to ${topic} industry", "Strength 2", "Strength 3"],
    "weaknesses": ["Real weakness 1", "Weakness 2"],
    "keyProducts": ["Product/service 1 in ${topic} space", "Product 2"],
    "recentNews": "Real development from 2024–2026 (funding, expansion, product launch)",
    "recentMoves": "Most significant verified event from Q4 2025 or Q1 2026: e.g. 'Raised Series C of $120M in January 2026 led by Sequoia Capital', 'Acquired [Company] for $85M in November 2025', 'Launched [Feature/Product] in [Month] 2025', 'Expanded to [City/Region] in Q1 2026'. Be specific with months and dollar amounts where known.",
    "pricingStrategy": "Actual pricing model: e.g. 'Subscription: $29/mo basic, $99/mo pro, $299/mo enterprise', 'Commission-based: 15-20% per transaction', 'Freemium with paid tiers starting at $49/mo', 'Usage-based per API call', etc.",
    "customerBase": "Specific description: who they sell to, typical company size/demographics, key verticals served, approximate customer count if known",
    "threatLevel": "High" | "Medium" | "Low",
    "position": "Market Leader" | "Challenger" | "Follower" | "Niche Player",
    "website": "https://actual-website.com",
    "relevanceExplanation": "Brief explanation of HOW this company competes in ${topic} industry in ${location}"
  }
]

**❌ ABSOLUTELY FORBIDDEN:**
- Generic IT consulting companies (TCS, Infosys, Wipro, Accenture) UNLESS topic is specifically IT consulting
- Companies from unrelated industries
- Made-up or fictional company names
- Companies that don't operate in ${location}
- Companies that don't compete in the "${topic}" market
- Stale data: do not describe any company's status as of 2022 or earlier
- Companies that have shut down, been fully acquired, or pivoted out of this market

**✅ SUCCESS CRITERIA:**
- Each competitor operates in the SAME industry as "${topic}"
- Each competitor can be found via Google search for "${topic} ${country}"
- Each competitor offers similar products/services to what "${topic}" describes
- Descriptions explain HOW each company competes with the proposed business
- At least 60% of companies should be ${country}-based or have major ${country} presence
- recentMoves field MUST reference something from 2025 or 2026

**EXAMPLE VALIDATION:**
- Topic: "food delivery app" in "India" → ✅ Zomato, Swiggy, Uber Eats India ❌ TCS, Infosys
- Topic: "AI chatbot SaaS" in "United States" → ✅ Intercom, Drift, ChatGPT ❌ General IT companies
- Topic: "e-commerce for crafts" in "United States" → ✅ Etsy, Amazon Handmade ❌ Generic retailers

Return ONLY the JSON array. No explanations, no markdown, just pure JSON.`;

  try {
    console.log('🔍 [COMPETITOR SEARCH] Using Google Search Grounding (v1beta)...');
    const { text, grounding } = await callWithGrounding(prompt);
    
    if (grounding?.webSearchQueries) {
      console.log('🔎 [COMPETITOR SEARCH] Search queries executed:', grounding.webSearchQueries.join(' | '));
    }
    
    // Parse JSON
    let jsonText = text.replace(/```json\n?/g, '').replace(/```\n?/g, '');
    const arrayMatch = jsonText.match(/\[\s*\{[\s\S]*\}\s*\]/);
    if (arrayMatch) jsonText = arrayMatch[0];
    
    const competitors = JSON.parse(jsonText.trim());
    
    if (Array.isArray(competitors) && competitors.length > 0) {
      console.log(`✅ [COMPETITOR SEARCH] Found ${competitors.length} competitors`);
      console.log(`🏢 [COMPETITOR SEARCH] Companies:`, competitors.map((c: any) => c.name).join(', '));
      
      // Validate relevance
      validateCompetitorRelevance(competitors, topic, industryKeywords);
      
      return competitors;
    } else {
      console.warn('⚠️ [COMPETITOR SEARCH] No competitors found in response');
      return [];
    }
  } catch (error) {
    console.error('❌ [COMPETITOR SEARCH] Error:', error);
    throw error;
  }
}

/**
 * Validate that competitors are relevant to the topic
 */
function validateCompetitorRelevance(competitors: any[], topic: string, industryKeywords: string[]): void {
  // Generic IT companies that should NOT appear unless the topic is IT consulting
  const genericITCompanies = [
    'tata consultancy', 'tcs', 'infosys', 'wipro', 'hcl', 'tech mahindra',
    'accenture', 'cognizant', 'capgemini', 'ibm', 'deloitte'
  ];
  
  const isITConsulting = topic.toLowerCase().includes('consulting') || 
                        topic.toLowerCase().includes('it services') ||
                        topic.toLowerCase().includes('software consulting');
  
  if (!isITConsulting) {
    const irrelevantCompetitors = competitors.filter((c: any) => 
      genericITCompanies.some(generic => c.name.toLowerCase().includes(generic))
    );
    
    if (irrelevantCompetitors.length > 0) {
      console.warn('⚠️ [VALIDATION] Found potentially irrelevant IT consulting companies for non-IT business:');
      irrelevantCompetitors.forEach((c: any) => {
        console.warn(`   - ${c.name} (may not be relevant to "${topic}")`);
      });
    }
  }
  
  // Check if competitors have relevance explanations
  const withoutExplanation = competitors.filter((c: any) => !c.relevanceExplanation);
  if (withoutExplanation.length > 0) {
    console.warn(`⚠️ [VALIDATION] ${withoutExplanation.length} competitors missing relevance explanation`);
  }
}