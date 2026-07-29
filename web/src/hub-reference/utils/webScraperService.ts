// @ts-nocheck
/**
 * Web Scraper Service - Real-time Google Search Integration
 * Uses Gemini API v1beta with Google Search Grounding
 */

import { callWithGrounding } from './geminiService';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ScrapedEntity {
  id: string;
  name: string;
  website?: string;
  description: string;
  revenue?: string;
  employees?: string;
  founded?: string;
  address?: string;
  phone?: string;
  email?: string;
  linkedIn?: string;
  category?: string;
  type: 'vendor' | 'competitor' | 'solution';
  source: 'google_live' | 'ai_research';
  googleSearchUrl: string;
  sourceUrls: { title: string; url: string }[];
}

// ─── Utilities ────────────────────────────────────────────────────────────────

function makeGoogleUrl(query: string): string {
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

function extractJson(text: string): any {
  try {
    let jsonText = text.trim();

    // Remove markdown code blocks
    if (jsonText.includes('```json')) {
      jsonText = jsonText.replace(/```json\s*/g, '').replace(/```/g, '');
    } else if (jsonText.includes('```')) {
      jsonText = jsonText.replace(/```\s*/g, '');
    }

    // Find JSON object boundaries
    const firstBrace = jsonText.indexOf('{');
    const lastBrace = jsonText.lastIndexOf('}');
    if (firstBrace !== -1 && lastBrace !== -1) {
      jsonText = jsonText.substring(firstBrace, lastBrace + 1);
    }

    return JSON.parse(jsonText);
  } catch (error) {
    console.error('[webScraper] JSON parse error:', error);
    console.error('[webScraper] Raw text:', text.substring(0, 500));
    throw new Error('Failed to parse JSON response');
  }
}

function buildSourcesFromGrounding(grounding: any): { title: string; url: string }[] {
  if (!grounding?.groundingChunks) return [];

  return grounding.groundingChunks
    .filter((chunk: any) => chunk.web?.uri && chunk.web?.title)
    .map((chunk: any) => ({
      title: chunk.web.title,
      url: chunk.web.uri,
    }))
    .slice(0, 8);
}

// ─── Competitor Search ────────────────────────────────────────────────────────

export async function searchCompetitors(
  topic: string,
  location: string
): Promise<{ entities: ScrapedEntity[]; sources: { title: string; url: string }[]; status: string; queries?: string[] }> {
  // Parse location into city, state, country for better targeting
  const locationParts = location.split(',').map(p => p.trim());
  const primaryLocation = locationParts[locationParts.length - 1] || location; // Country is last
  const city = locationParts.length >= 3 ? locationParts[2] : '';
  const state = locationParts.length >= 2 ? locationParts[1] : locationParts.length === 2 ? locationParts[0] : '';
  
  const locationContext = locationParts.length >= 2 
    ? `${locationParts.join(', ')}` 
    : location;
  
  // Extract industry keywords from the business idea
  const industryKeywords = extractIndustryKeywords(topic);
  const timestamp = new Date().toISOString();
  
  const prompt = `You are a business intelligence researcher with real-time Google Search access. Your task is to find the TOP 8-12 REAL companies that are DIRECT COMPETITORS to a business described as: "${topic}"

**🎯 BUSINESS IDEA CONTEXT:**
The user wants to start: "${topic}"
Location: ${locationContext}
Industry Keywords: ${industryKeywords.join(', ')}
Search Timestamp: ${timestamp}

**🔍 CRITICAL SEARCH REQUIREMENTS:**

1. **INDUSTRY RELEVANCE IS MANDATORY:**
   - Companies MUST operate in the SAME INDUSTRY as "${topic}"
   - If the idea is "e-commerce platform for handmade crafts" → Find ONLY e-commerce/craft marketplace companies
   - If the idea is "food delivery app" → Find ONLY food delivery companies
   - If the idea is "AI chatbot SaaS" → Find ONLY AI/SaaS companies
   - If the idea is "fitness app" → Find ONLY fitness/health tech companies
   - DO NOT return generic IT consulting firms (TCS, Infosys, Wipro) unless the idea is specifically about IT consulting
   - DO NOT return unrelated companies from other industries

2. **GOOGLE SEARCH STRATEGY:**
   Execute these Google searches IN ORDER and use results:
   1. "${topic} companies ${primaryLocation} 2025 2026"
   2. "${industryKeywords[0]} ${industryKeywords[1]} startups ${primaryLocation}"
   3. "top ${industryKeywords[0]} businesses ${state || city || primaryLocation}"
   4. "${topic} competitors market leaders ${locationContext}"
   5. "best ${industryKeywords.join(' ')} companies ${primaryLocation}"

3. **LOCATION REQUIREMENTS:**
   - ALL companies MUST have operations in ${locationContext}
   - PRIORITIZE companies headquartered in ${primaryLocation}
   - Include international companies ONLY if they actively serve ${primaryLocation} market
   - For India: ONLY companies with Indian operations (can be Indian or international with India presence)
   - For UAE: ONLY companies operating in UAE/Middle East
   - For United States: ONLY companies with verified US operations

4. **VALIDATION RULES:**
   - Each company MUST be relevant to "${topic}" industry
   - Each company MUST be verifiable via Google search
   - Each company MUST have a real website and business presence
   - NO generic consulting firms unless consulting is the business idea
   - NO companies from unrelated industries
   - Companies should be actual competitors or similar businesses

**📋 REQUIRED JSON FORMAT (return ONLY this, no markdown):**
{
  "competitors": [
    {
      "name": "Exact Legal Company Name",
      "website": "https://verified-website.com",
      "description": "Precise description of how this company competes with '${topic}' in ${locationContext} (2-3 sentences focusing on similar products/services)",
      "revenue": "USD X million" or "INR X crore" or "Not public",
      "employees": "X-Y range" or "X+",
      "founded": "YYYY",
      "address": "${city ? city + ', ' : ''}${state ? state + ', ' : ''}${primaryLocation}",
      "phone": "+XX-XXX-XXX-XXXX" or null,
      "linkedIn": "https://linkedin.com/company/exact-slug" or null,
      "category": "Direct Competitor" | "Indirect Competitor" | "Emerging Rival"
    }
  ]
}

**❌ FORBIDDEN RESULTS:**
- Generic IT consulting companies (TCS, Infosys, Wipro, Accenture) UNLESS the idea is specifically IT consulting
- Companies from unrelated industries
- Made-up or fictional company names
- Companies that don't operate in ${locationContext}
- Companies that don't compete in the same market as "${topic}"

**✅ SUCCESS CRITERIA:**
- Each competitor operates in the SAME industry as "${topic}"
- Each competitor can be found via Google search for "${topic} ${primaryLocation}"
- Each competitor offers similar products/services to what "${topic}" describes
- Descriptions explain HOW each company competes with the proposed business

Return ONLY the JSON object. No explanations, no markdown blocks, just pure JSON.`;

  try {
    console.log(`🔍 [Competitors] Searching for businesses similar to "${topic}" in ${locationContext}...`);
    console.log(`🏷️ [Competitors] Industry keywords: ${industryKeywords.join(', ')}`);
    
    const groundingResult = await callWithGrounding(prompt);
    if (!groundingResult) {
      console.log('ℹ️ [Competitors] callWithGrounding returned null (Gemini unavailable) — returning empty');
      return { entities: [], sources: [], status: 'error' };
    }
    const { text, grounding } = groundingResult;
    console.log('📝 [Competitors] Raw response received, parsing...');
    
    const parsed = extractJson(text);
    const sources = buildSourcesFromGrounding(grounding);

    if (!parsed.competitors || !Array.isArray(parsed.competitors)) {
      console.warn('⚠️ [Competitors] No competitors array in response');
      return { entities: [], sources, status: 'error' };
    }

    const entities: ScrapedEntity[] = parsed.competitors.map((c: any, idx: number) => ({
      id: `comp-${Date.now()}-${idx}`, // Unique ID with timestamp
      name: c.name || 'Unknown',
      website: c.website || undefined,
      description: c.description || '',
      revenue: c.revenue && c.revenue !== 'null' ? c.revenue : undefined,
      employees: c.employees && c.employees !== 'null' ? c.employees : undefined,
      founded: c.founded && c.founded !== 'null' ? String(c.founded) : undefined,
      address: c.address || undefined,
      phone: c.phone && c.phone !== 'null' ? c.phone : undefined,
      linkedIn: c.linkedIn && c.linkedIn !== 'null' ? c.linkedIn : undefined,
      category: c.category || 'Competitor',
      type: 'competitor',
      source: grounding ? 'google_live' : 'ai_research',
      googleSearchUrl: makeGoogleUrl(`${c.name} ${locationContext} ${topic}`),
      sourceUrls: sources.slice(0, 4),
    }));

    console.log(`✅ [Competitors] Found ${entities.length} competitors (${grounding ? 'LIVE Google' : 'AI research'})`);
    console.log(`🏢 [Competitors] Companies: ${entities.map(e => e.name).join(', ')}`);
    
    if (grounding?.webSearchQueries) {
      console.log('🔎 [Competitors] Search queries used:', grounding.webSearchQueries.join(' | '));
    }

    // Validate relevance
    validateCompetitorRelevance(entities, topic);

    return {
      entities,
      sources,
      status: grounding ? 'google_live' : 'ai_research',
      queries: grounding?.webSearchQueries,
    };
  } catch (err) {
    console.error('[webScraper] Competitor search error:', err);
    console.error('[webScraper] Error details:', err instanceof Error ? err.message : String(err));
    return { entities: [], sources: [], status: 'error' };
  }
}

/**
 * Extract industry keywords from business idea
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
 * Validate that competitors are relevant to the business idea
 */
function validateCompetitorRelevance(competitors: ScrapedEntity[], topic: string): void {
  // Generic IT companies that should NOT appear unless the idea is IT consulting
  const genericITCompanies = [
    'tata consultancy', 'tcs', 'infosys', 'wipro', 'hcl', 'tech mahindra',
    'accenture', 'cognizant', 'capgemini', 'ibm', 'deloitte'
  ];
  
  const isITConsulting = topic.toLowerCase().includes('consulting') || 
                        topic.toLowerCase().includes('it services') ||
                        topic.toLowerCase().includes('software consulting');
  
  if (!isITConsulting) {
    const irrelevantCompetitors = competitors.filter(c => 
      genericITCompanies.some(generic => c.name.toLowerCase().includes(generic))
    );
    
    if (irrelevantCompetitors.length > 0) {
      console.warn('⚠️ [VALIDATION] Found potentially irrelevant IT consulting companies for non-IT business:');
      irrelevantCompetitors.forEach(c => {
        console.warn(`   - ${c.name} (may not be relevant to "${topic}")`);
      });
    }
  }
}

// ─── Vendor Search ────────────────────────────────────────────────────────────

export async function searchVendors(
  topic: string,
  location: string
): Promise<{ entities: ScrapedEntity[]; sources: { title: string; url: string }[]; status: string; queries?: string[] }> {
  // Parse location for better targeting
  const locationParts = location.split(',').map(p => p.trim());
  const primaryLocation = locationParts[locationParts.length - 1] || location;
  const state = locationParts.length >= 2 ? locationParts[1] : '';
  const city = locationParts.length >= 3 ? locationParts[2] : '';
  
  const locationContext = locationParts.length >= 2 
    ? `${locationParts.join(', ')}` 
    : location;

  const prompt = `You are a business intelligence researcher with real-time Google Search access. Find the TOP 10-12 REAL vendors/suppliers that provide services or products related to \"${topic}\" specifically in ${locationContext} as of 2025-2026.

**🔍 GOOGLE SEARCH STRATEGY:**
Use these exact search queries:
1. \"${topic} suppliers ${locationContext} 2025\"
2. \"${topic} vendors ${primaryLocation} 2026\"
3. \"best ${topic} service providers ${state || city || primaryLocation}\"
4. \"${topic} wholesale distributors ${locationContext}\"

**🌍 CRITICAL LOCATION RULES:**
- ALL vendors MUST have operations/serve customers in ${locationContext}
- PRIORITIZE local vendors in ${state || city || primaryLocation}
- Include national/international vendors ONLY if they serve ${locationContext}
- Verify each vendor has ${locationContext} delivery/service availability

**📋 REQUIRED JSON FORMAT (return ONLY this, no markdown):**
{
  "vendors": [
    {
      "name": "Exact Company Name",
      "website": "https://verified-website.com",
      "description": "What they supply for ${topic} in ${locationContext} (2-3 sentences)",
      "services": ["Service 1", "Service 2", "Service 3"],
      "priceRange": "Low/Medium/High or specific range",
      "minimumOrder": "MOQ details or 'None'",
      "deliveryArea": "${locationContext} coverage details",
      "address": "${city ? city + ', ' : ''}${state ? state + ', ' : ''}${primaryLocation}",
      "phone": "+XX-XXX-XXX-XXXX" or null,
      "email": "contact@vendor.com" or null,
      "linkedIn": "https://linkedin.com/company/exact-slug" or null,
      "category": "Primary Supplier" | "Secondary Supplier" | "Specialized Vendor"
    }
  ]
}

**✅ VERIFICATION CHECKLIST:**
1. Vendor name appears in Google search for ${locationContext}
2. Vendor serves/delivers to ${locationContext}
3. Vendor provides products/services related to ${topic}
4. Contact information is verifiable
5. Vendor is currently operational (2025-2026)

Return ONLY the JSON object. No explanations, no markdown blocks, just pure JSON.`;

  try {
    console.log(`🔍 [Vendors] Searching for \"${topic}\" vendors in ${locationContext}...`);
    const vendorGrounding = await callWithGrounding(prompt);
    if (!vendorGrounding) {
      console.log('ℹ️ [Vendors] callWithGrounding returned null — returning empty');
      return { entities: [], sources: [], status: 'error' };
    }
    const { text: vendorText, grounding: vendorGroundingData } = vendorGrounding;
    console.log('📝 [Vendors] Raw response received, parsing...');

    const parsed = extractJson(vendorText);
    const sources = buildSourcesFromGrounding(vendorGroundingData);

    if (!parsed.vendors || !Array.isArray(parsed.vendors)) {
      console.warn('⚠️ [Vendors] No vendors array in response');
      return { entities: [], sources, status: 'error' };
    }

    const entities: ScrapedEntity[] = parsed.vendors.map((v: any, idx: number) => ({
      id: `vendor-${idx}`,
      name: v.name || 'Unknown',
      website: v.website || undefined,
      description: v.description || '',
      address: v.address || undefined,
      phone: v.phone && v.phone !== 'null' ? v.phone : undefined,
      email: v.email && v.email !== 'null' ? v.email : undefined,
      linkedIn: v.linkedIn && v.linkedIn !== 'null' ? v.linkedIn : undefined,
      category: v.category || 'Vendor',
      type: 'vendor',
      source: vendorGroundingData ? 'google_live' : 'ai_research',
      googleSearchUrl: makeGoogleUrl(`${v.name} ${locationContext} ${topic}`),
      sourceUrls: sources.slice(0, 4),
    }));

    console.log(`✅ [Vendors] Found ${entities.length} vendors (${vendorGroundingData ? 'LIVE Google' : 'AI research'})`);
    if (vendorGroundingData?.webSearchQueries) {
      console.log('🔎 [Vendors] Search queries used:', vendorGroundingData.webSearchQueries.join(' | '));
    }

    return {
      entities,
      sources,
      status: vendorGroundingData ? 'google_live' : 'ai_research',
      queries: vendorGroundingData?.webSearchQueries,
    };
  } catch (err) {
    console.error('[webScraper] Vendor search error:', err);
    return { entities: [], sources: [], status: 'error' };
  }
}

// ─── Solution Search ──────────────────────────────────────────────────────────

export async function searchSolutions(
  topic: string,
  location: string
): Promise<{ entities: ScrapedEntity[]; sources: { title: string; url: string }[]; status: string; queries?: string[] }> {
  const locationParts = location.split(',').map(p => p.trim());
  const primaryLocation = locationParts[locationParts.length - 1] || location;
  const state = locationParts.length >= 2 ? locationParts[1] : '';
  const city = locationParts.length >= 3 ? locationParts[2] : '';
  
  const locationContext = locationParts.length >= 2 
    ? `${locationParts.join(', ')}` 
    : location;

  const prompt = `You are a business intelligence researcher with real-time Google Search access. Find the TOP 8-10 REAL solution providers, consultants, or service companies that help businesses with \"${topic}\" specifically in ${locationContext} as of 2025-2026.

**🔍 GOOGLE SEARCH STRATEGY:**
Use these exact search queries:
1. \"${topic} solution providers ${locationContext} 2025\"
2. \"${topic} consulting services ${primaryLocation} 2026\"
3. \"best ${topic} experts ${state || city || primaryLocation}\"
4. \"${topic} implementation partners ${locationContext}\"

**🌍 CRITICAL LOCATION RULES:**
- ALL solution providers MUST serve clients in ${locationContext}
- PRIORITIZE companies with offices in ${state || city || primaryLocation}
- Include global providers ONLY if they have ${locationContext} presence
- Verify active service delivery in ${locationContext}

**📋 REQUIRED JSON FORMAT (return ONLY this, no markdown):**
{
  "solutions": [
    {
      "name": "Exact Company Name",
      "website": "https://verified-website.com",
      "description": "How they help with ${topic} in ${locationContext} (2-3 sentences)",
      "services": ["Service 1", "Service 2", "Service 3"],
      "expertise": ["Expertise area 1", "Expertise area 2"],
      "clientTypes": ["Client type 1", "Client type 2"],
      "pricingModel": "Hourly/Project-based/Retainer/etc.",
      "address": "${city ? city + ', ' : ''}${state ? state + ', ' : ''}${primaryLocation}",
      "phone": "+XX-XXX-XXX-XXXX" or null,
      "email": "contact@company.com" or null,
      "linkedIn": "https://linkedin.com/company/exact-slug" or null,
      "category": "Full-Service Provider" | "Specialized Consultant" | "Implementation Partner"
    }
  ]
}

**✅ VERIFICATION CHECKLIST:**
1. Company appears in Google search for ${locationContext}
2. Company serves clients in ${locationContext}
3. Company specializes in ${topic} solutions
4. Company is currently active (2025-2026)
5. Contact information is verifiable

Return ONLY the JSON object. No explanations, no markdown blocks, just pure JSON.`;

  try {
    console.log(`🔍 [Solutions] Searching for \"${topic}\" solutions in ${locationContext}...`);
    const solGrounding = await callWithGrounding(prompt);
    if (!solGrounding) {
      console.log('ℹ️ [Solutions] callWithGrounding returned null — returning empty');
      return { entities: [], sources: [], status: 'error' };
    }
    const { text: solText, grounding: solGroundingData } = solGrounding;
    console.log('📝 [Solutions] Raw response received, parsing...');

    const parsed = extractJson(solText);
    const sources = buildSourcesFromGrounding(solGroundingData);

    if (!parsed.solutions || !Array.isArray(parsed.solutions)) {
      console.warn('⚠️ [Solutions] No solutions array in response');
      return { entities: [], sources, status: 'error' };
    }

    const entities: ScrapedEntity[] = parsed.solutions.map((s: any, idx: number) => ({
      id: `solution-${idx}`,
      name: s.name || 'Unknown',
      website: s.website || undefined,
      description: s.description || '',
      address: s.address || undefined,
      phone: s.phone && s.phone !== 'null' ? s.phone : undefined,
      email: s.email && s.email !== 'null' ? s.email : undefined,
      linkedIn: s.linkedIn && s.linkedIn !== 'null' ? s.linkedIn : undefined,
      category: s.category || 'Solution Provider',
      type: 'solution',
      source: solGroundingData ? 'google_live' : 'ai_research',
      googleSearchUrl: makeGoogleUrl(`${s.name} ${locationContext} ${topic}`),
      sourceUrls: sources.slice(0, 4),
    }));

    console.log(`✅ [Solutions] Found ${entities.length} solutions (${solGroundingData ? 'LIVE Google' : 'AI research'})`);
    if (solGroundingData?.webSearchQueries) {
      console.log('🔎 [Solutions] Search queries used:', solGroundingData.webSearchQueries.join(' | '));
    }

    return {
      entities,
      sources,
      status: solGroundingData ? 'google_live' : 'ai_research',
      queries: solGroundingData?.webSearchQueries,
    };
  } catch (err) {
    console.error('[webScraper] Solution search error:', err);
    return { entities: [], sources: [], status: 'error' };
  }
}