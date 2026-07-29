// @ts-nocheck
import { getLocationKey, getLocationInfo, formatBudgetAmount } from './locationData';
import { getRealCompetitors } from './realCompaniesData';
import { analyzeMarketReality, MarketReality } from './marketRealityAnalyzer';

export interface BusinessPlanFormData {
  businessIdea: string;
  targetRevenue: string;
  country: string;
  currency: string;
}

export interface BusinessPlanData {
  businessIdea: string;
  country: string;
  currency: string;
  targetRevenue: string;
  generatedDate: string;
  realityCheck: {
    isViable: boolean;
    viabilityScore: number;
    honestAssessment: string;
    redFlags: string[];
    greenFlags: string[];
    truthBombs: string[];
  };
  executiveSummary: {
    businessConcept: string;
    missionStatement: string;
    keysToSuccess: string[];
    financialHighlights: {
      targetRevenue: string;
      projectedProfit: string;
      breakEvenPoint: string;
      initialInvestment: string;
    };
  };
  companyDescription: {
    businessName: string;
    legalStructure: string;
    location: string;
    ownership: string;
    businessModel: string;
    valueProposition: string;
  };
  marketAnalysis: {
    industryOverview: string;
    targetMarket: string;
    marketSize: string;
    marketGrowthRate: string;
    targetCustomers: Array<{
      segment: string;
      description: string;
      size: string;
      needs: string[];
    }>;
    competitiveAnalysis: {
      directCompetitors: Array<{
        name: string;
        location: string;
        foundedYear: number;
        annualRevenue: string;
        employeeCount: string;
        strengths: string[];
        weaknesses: string[];
        marketShare: string;
        keyProducts: string[];
        recentProjects: string[];
        customerBase: string;
        pricingModel: string;
        marketingApproach: string[];
      }>;
      competitiveAdvantage: string[];
      differentiationStrategies: Array<{
        strategy: string;
        description: string;
        implementation: string;
        expectedImpact: string;
        timeline: string;
      }>;
      marketGaps: string[];
      competitivePositioning: string;
    };
  };
  organizationManagement: {
    organizationalStructure: string;
    managementTeam: Array<{
      role: string;
      responsibilities: string[];
      qualifications: string;
      compensation: string;
    }>;
    advisoryBoard: string[];
    staffingPlan: {
      year1: number;
      year2: number;
      year3: number;
      keyPositions: string[];
    };
  };
  productsServices: {
    offerings: Array<{
      name: string;
      description: string;
      features: string[];
      pricing: string;
      profitMargin: string;
    }>;
    productDevelopment: {
      currentStage: string;
      developmentTimeline: string;
      rdBudget: string;
    };
    intellectualProperty: string[];
  };
  marketingStrategy: {
    brandingStrategy: string;
    pricingStrategy: string;
    distributionChannels: string[];
    promotionalStrategy: Array<{
      channel: string;
      budget: string;
      expectedROI: string;
      timeline: string;
    }>;
    salesStrategy: {
      salesProcess: string[];
      salesTargets: {
        year1: string;
        year2: string;
        year3: string;
      };
      customerAcquisitionCost: string;
      customerLifetimeValue: string;
    };
  };
  operationsPlan: {
    facilities: {
      type: string;
      location: string;
      size: string;
      cost: string;
    };
    equipment: Array<{
      item: string;
      cost: string;
      quantity: number;
    }>;
    suppliers: Array<{
      category: string;
      supplier: string;
      terms: string;
      backup: string;
    }>;
    productionProcess: string[];
    qualityControl: string[];
  };
  financialProjections: {
    startupCosts: {
      categories: Array<{
        category: string;
        amount: string;
        description: string;
      }>;
      total: string;
    };
    fundingRequirements: {
      totalNeeded: string;
      sources: Array<{
        source: string;
        amount: string;
        terms: string;
      }>;
    };
    revenueProjections: Array<{
      year: number;
      revenue: string;
      cogs: string;
      grossProfit: string;
      grossMargin: string;
      operatingExpenses: string;
      netProfit: string;
      netMargin: string;
    }>;
    detailedYearlyBreakdown: Array<{
      year: number;
      quarters: Array<{
        quarter: string;
        revenue: string;
        expenses: string;
        profit: string;
        cashFlow: string;
        customerCount: number;
        averageOrderValue: string;
      }>;
      keyMetrics: {
        totalCustomers: number;
        customerGrowthRate: string;
        averageRevenuePerCustomer: string;
        churnRate: string;
        employeeCount: number;
        revenuePerEmployee: string;
        operatingCashFlow: string;
        freeCashFlow: string;
        ebitda: string;
        ebitdaMargin: string;
      };
    }>;
    fiveYearProjections: Array<{
      year: number;
      revenue: string;
      netProfit: string;
      cashReserves: string;
      totalAssets: string;
      totalLiabilities: string;
      equity: string;
      returnOnEquity: string;
      returnOnAssets: string;
    }>;
    monthlyYear1Breakdown: Array<{
      month: string;
      revenue: string;
      expenses: string;
      netIncome: string;
      cumulativeCashFlow: string;
      burnRate: string;
      runwayMonths: number;
    }>;
    cashFlowProjection: {
      year1Monthly: boolean;
      breakEvenMonth: number;
      minimumCashBalance: string;
    };
    financialAssumptions: {
      revenueGrowthRate: string;
      cogsPercentage: string;
      operatingExpenseGrowth: string;
      corporateTaxRate: string;
      inflationRate: string;
      gdpGrowthRate: string;
    };
  };
  riskAnalysis: {
    risks: Array<{
      category: string;
      description: string;
      likelihood: string;
      impact: string;
      mitigation: string;
    }>;
    contingencyPlans: string[];
    insurance: Array<{
      type: string;
      coverage: string;
      annualCost: string;
    }>;
  };
  implementationTimeline: {
    phases: Array<{
      phase: string;
      duration: string;
      milestones: Array<{
        milestone: string;
        deadline: string;
        owner: string;
        status: string;
      }>;
    }>;
  };
  exitStrategy: {
    options: Array<{
      strategy: string;
      timeline: string;
      expectedReturn: string;
      conditions: string[];
    }>;
  };
}

export function generateBusinessPlan(formData: BusinessPlanFormData): BusinessPlanData {
  const locationKey = getLocationKey(formData.country.toLowerCase());
  const locationInfo = getLocationInfo(locationKey);
  
  const targetRevenueNum = parseFloat(formData.targetRevenue) || 1000000;
  
  // Get real competitors first
  const competitors = getRealCompetitors(formData.country, formData.businessIdea, targetRevenueNum);
  
  // BRUTALLY HONEST MARKET ANALYSIS
  const marketReality = analyzeMarketReality(
    formData.businessIdea,
    formData.country,
    targetRevenueNum,
    competitors
  );
  
  // Use REAL projections, not dummy data
  const year1Revenue = marketReality.realProjections.year1Revenue;
  const year2Revenue = marketReality.realProjections.year2Revenue;
  const year3Revenue = marketReality.realProjections.year3Revenue;
  const profitMargin = marketReality.realProjections.profitMargin;
  const breakEven = marketReality.realProjections.breakEven;
  
  const initialInvestment = targetRevenueNum * 0.3;
  
  const marketGrowthMultiplier = locationInfo.marketGrowthMultiplier || 1.0;

  // ─── Scenario-driven P&L ratios ─────────────────────────────────────────
  // Driven by viability score so ALL downstream numbers are mathematically consistent.
  // Formula invariant: COGS% + opexCash% + D&A% + netMargin% = 100%
  const viability = marketReality.viabilityScore;

  // Net margin trajectories per viability band
  let y1NM: number, y2NM: number, y3NM: number;
  if (viability >= 60)      { y1NM = 8;   y2NM = 15;  y3NM = 20; }
  else if (viability >= 40) { y1NM = -3;  y2NM = 5;   y3NM = 10; }
  else if (viability >= 25) { y1NM = -10; y2NM = -5;  y3NM = -1; }
  else                      { y1NM = -20; y2NM = -12; y3NM = -6; }

  // Per-year rate objects — every rate is a fraction of revenue (0-1)
  function makeYearRates(netMarginPct: number) {
    const nm  = netMarginPct / 100;   // net margin as fraction
    const da  = 0.05;                 // D&A ~5% of revenue
    const cogs = 0.35 - Math.max(0, netMarginPct * 0.001); // COGS: slightly improves with profit
    const grossMarginFrac = 1 - cogs;
    // Operating expenses (cash, excl D&A) = what remains after COGS, D&A, net margin
    const opexCash = Math.max(0.05, grossMarginFrac - da - nm);
    // EBITDA = gross profit - opex_cash = nm + da (by construction)
    const ebitda = nm + da;
    // OCF ≈ EBITDA × 0.80 (account for taxes and WC movements)
    const ocf = ebitda >= 0 ? ebitda * 0.80 : ebitda * 1.10; // losses burn slightly more cash
    const capex = 0.08;               // capex always 8% of revenue
    const fcf = ocf - capex;
    return { nm, da, cogs, grossMarginFrac, opexRate: opexCash + da, opexCash, ebitda, ocf, capex, fcf };
  }

  const R1 = makeYearRates(y1NM);
  const R2 = makeYearRates(y2NM);
  const R3 = makeYearRates(y3NM);

  // Year 4 & 5 extrapolation
  const mktGrowth = marketReality.realMarketGrowth;
  const y4Rev = year3Revenue * (1 + Math.max(mktGrowth / 100, 0) + 0.05);
  const y5Rev = y4Rev       * (1 + Math.max(mktGrowth / 100, 0) + 0.05);
  const y4NM = Math.min(y3NM + 3, 30);
  const y5NM = Math.min(y4NM + 2, 32);
  const R4 = makeYearRates(y4NM);
  const R5 = makeYearRates(y5NM);

  // ─── Balance sheet helper ─────────────────────────────────────────────────
  // Builds a simple balance sheet snapshot for a given year
  const bankLoan = initialInvestment * 0.25; // 25% bank-financed
  const loanRepayPerYear = bankLoan / 5;

  let cumulNI = 0; // Running cumulative net income
  function buildBS(rev: number, rates: ReturnType<typeof makeYearRates>, yearNum: number) {
    cumulNI += rev * rates.nm;
    const cashReserves = Math.max(0, initialInvestment * 0.30 + cumulNI * 0.50 + rev * Math.max(rates.fcf, 0));
    const ar           = rev * 0.06;  // Accounts receivable (~30-day DSO)
    const fixedAssets  = Math.max(0, initialInvestment * 0.25 * (1 - yearNum * 0.15)); // Depreciated
    const totalAssets  = Math.max(cashReserves + ar + fixedAssets, initialInvestment * 0.50);
    const remainingLoan = Math.max(0, bankLoan - loanRepayPerYear * yearNum);
    const payables     = rev * 0.04;
    const totalLiabilities = remainingLoan + payables;
    const equity       = totalAssets - totalLiabilities;
    const netIncome    = rev * rates.nm;
    const roe = equity   > 1 ? (netIncome / equity   * 100) : 0;
    const roa = totalAssets > 1 ? (netIncome / totalAssets * 100) : 0;
    return { cashReserves, totalAssets, totalLiabilities, equity, roe, roa };
  }

  const bs1 = buildBS(year1Revenue, R1, 1);
  const bs2 = buildBS(year2Revenue, R2, 2);
  const bs3 = buildBS(year3Revenue, R3, 3);
  const bs4 = buildBS(y4Rev, R4, 4);
  const bs5 = buildBS(y5Rev, R5, 5);

  // ─── Monthly Year-1 ramp ──────────────────────────────────────────────────
  // Revenue builds from ~35% to ~145% of monthly average across 12 months
  const MONTH_NAMES = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const MONTH_FACTORS = [0.35,0.45,0.55,0.65,0.75,0.85,0.95,1.05,1.15,1.25,1.35,1.45];
  const FACTOR_SUM = MONTH_FACTORS.reduce((s, f) => s + f, 0); // = 10.8 → ensures sum = year1Revenue
  let cumulMonthOCF = -(initialInvestment * 0.70); // After deploying ~70% of investment in setup
  const monthlyYear1Breakdown = MONTH_NAMES.map((month, m) => {
    const mRev      = (MONTH_FACTORS[m] / FACTOR_SUM) * year1Revenue;
    const mExpenses = mRev * (R1.cogs + R1.opexRate); // total cash out
    const mNetInc   = mRev * R1.nm;
    const mOCF      = mRev * R1.ocf;
    cumulMonthOCF  += mOCF;
    const cashPool  = initialInvestment * 0.30 + Math.max(0, cumulMonthOCF);
    const runwayMos = mExpenses > 0 ? Math.min(36, Math.max(0, Math.round(cashPool / mExpenses))) : 24;
    return {
      month,
      revenue: formatBudgetAmount(mRev, locationKey),
      expenses: formatBudgetAmount(mExpenses, locationKey),
      netIncome: formatBudgetAmount(mNetInc, locationKey),
      cumulativeCashFlow: formatBudgetAmount(cumulMonthOCF, locationKey),
      burnRate: formatBudgetAmount(mExpenses, locationKey),
      runwayMonths: runwayMos,
    };
  });

  // ─── Quarterly helper ─────────────────────────────────────────────────────
  function buildQ(rev: number, rates: ReturnType<typeof makeYearRates>, quarter: string, customers: number) {
    const qRev  = rev * 0.25;
    const qExp  = qRev * (rates.cogs + rates.opexRate);
    const qNI   = qRev * rates.nm;
    const qOCF  = qRev * rates.ocf; // Operating cash flow for the quarter
    const aov   = customers > 0 ? qRev / customers : 0;
    return {
      quarter,
      revenue: formatBudgetAmount(qRev, locationKey),
      expenses: formatBudgetAmount(qExp, locationKey),
      profit: formatBudgetAmount(qNI, locationKey),
      cashFlow: formatBudgetAmount(qOCF, locationKey),
      customerCount: customers,
      averageOrderValue: formatBudgetAmount(aov, locationKey),
    };
  }

  // Customer counts
  const aov = Math.max(targetRevenueNum * 0.005, 1);
  const y1Cust = Math.max(10, Math.round(year1Revenue / aov));
  const y2Cust = Math.max(y1Cust + 1, Math.round(year2Revenue / (aov * 1.10)));
  const y3Cust = Math.max(y2Cust + 1, Math.round(year3Revenue / (aov * 1.20)));

  // Realistic churn rates
  const y1Churn = viability >= 60 ? '8%' : viability >= 40 ? '12%' : '18%';
  const y2Churn = viability >= 60 ? '6%' : viability >= 40 ? '10%' : '15%';
  const y3Churn = viability >= 60 ? '5%' : viability >= 40 ? '8%'  : '12%';

  // Customer growth rates (Y2 vs Y1, Y3 vs Y2)
  const cgr2 = y1Cust > 0 ? `${Math.round((y2Cust - y1Cust) / y1Cust * 100)}%` : 'N/A';
  const cgr3 = y2Cust > 0 ? `${Math.round((y3Cust - y2Cust) / y2Cust * 100)}%` : 'N/A';

  return {
    businessIdea: formData.businessIdea,
    country: formData.country,
    currency: formData.currency,
    targetRevenue: formatBudgetAmount(targetRevenueNum, locationKey),
    generatedDate: new Date().toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    }),
    
    // REALITY CHECK - SHOWN FIRST
    realityCheck: {
      isViable: marketReality.isViable,
      viabilityScore: marketReality.viabilityScore,
      honestAssessment: marketReality.honestAssessment,
      redFlags: marketReality.redFlags,
      greenFlags: marketReality.greenFlags,
      truthBombs: marketReality.truthBombs,
    },
    
    executiveSummary: {
      businessConcept: `${formData.businessIdea}. This venture aims to capitalize on market opportunities in ${formData.country}, leveraging local economic conditions including ${locationInfo.gdpGrowthRate}% GDP growth and a ${locationInfo.marketMaturity.toLowerCase()} market environment.`,
      missionStatement: `To deliver exceptional value to customers in ${formData.country} by ${formData.businessIdea.toLowerCase()}, while building a sustainable and profitable business that contributes to the local economy.`,
      keysToSuccess: [
        `Understanding and adapting to ${formData.country}'s regulatory environment (${locationInfo.regulatoryComplexity} complexity)`,
        'Strong market positioning and differentiation',
        'Efficient operations and cost management',
        `Leveraging ${formData.country}'s ${locationInfo.marketMaturity.toLowerCase()} market dynamics`,
        'Customer-centric approach and continuous innovation',
      ],
      financialHighlights: {
        targetRevenue: formatBudgetAmount(targetRevenueNum, locationKey),
        projectedProfit: y3NM >= 0
          ? formatBudgetAmount(year3Revenue * R3.nm, locationKey)
          : `LOSS: ${formatBudgetAmount(Math.abs(year3Revenue * R3.nm), locationKey)}`,
        breakEvenPoint: breakEven,
        initialInvestment: formatBudgetAmount(initialInvestment, locationKey),
      },
    },

    companyDescription: {
      businessName: 'Your Business Name',
      legalStructure: locationKey === 'usa' ? 'LLC' : locationKey === 'uk' ? 'Limited Company' : 'Corporation',
      location: formData.country,
      ownership: 'Founder-owned with potential for investor participation',
      businessModel: generateBusinessModel(formData.businessIdea),
      valueProposition: `We provide unique value through innovation, quality, and customer service, tailored specifically for the ${formData.country} market with its ${locationInfo.marketMaturity.toLowerCase()} characteristics and ${locationInfo.gdpGrowthRate}% growth trajectory.`,
    },

    marketAnalysis: {
      industryOverview: marketReality.realMarketGrowth < 0 
        ? `⚠️ DECLINING INDUSTRY: Market shrinking at ${Math.abs(marketReality.realMarketGrowth)}% annually in ${formData.country}. ${marketReality.saturationLevel} market with ${marketReality.competitionLevel.toLowerCase()} competition. This is a challenging environment.`
        : marketReality.realMarketGrowth > 15
        ? `🚀 GROWTH MARKET: Industry expanding at ${marketReality.realMarketGrowth}% annually in ${formData.country}. Market is ${marketReality.saturationLevel.toLowerCase()} with ${marketReality.competitionLevel.toLowerCase()} competition. ${marketReality.entryBarrier} barriers to entry.`
        : `The industry in ${formData.country} is growing at ${marketReality.realMarketGrowth}% annually (${marketReality.realMarketGrowth > locationInfo.gdpGrowthRate ? 'above' : 'below'} GDP growth of ${locationInfo.gdpGrowthRate}%). Market saturation: ${marketReality.saturationLevel}. Competition: ${marketReality.competitionLevel}. Entry barriers: ${marketReality.entryBarrier}.`,
      targetMarket: `${formData.country} market - ${marketReality.saturationLevel.toLowerCase()} with ${marketReality.competitionLevel.toLowerCase()} competition`,
      marketSize: formatBudgetAmount(targetRevenueNum * 50, locationKey),
      marketGrowthRate: marketReality.realMarketGrowth < 0 
        ? `${marketReality.realMarketGrowth}% annually (DECLINING)`
        : `${marketReality.realMarketGrowth}% annually`,
      targetCustomers: [
        {
          segment: 'Primary Market Segment',
          description: 'Core customers most aligned with our value proposition',
          size: formatBudgetAmount(targetRevenueNum * 20, locationKey),
          needs: [
            'Quality products/services',
            'Competitive pricing',
            'Excellent customer service',
            'Local market understanding',
          ],
        },
        {
          segment: 'Secondary Market Segment',
          description: 'Growth opportunities with adjacent customer needs',
          size: formatBudgetAmount(targetRevenueNum * 15, locationKey),
          needs: [
            'Innovation and differentiation',
            'Reliability and trust',
            'Value for money',
            'Convenience and accessibility',
          ],
        },
        {
          segment: 'Tertiary Market Segment',
          description: 'Emerging segment with long-term potential',
          size: formatBudgetAmount(targetRevenueNum * 10, locationKey),
          needs: [
            'Customization options',
            'Premium features',
            'Sustainability focus',
            'Technology integration',
          ],
        },
      ],
      competitiveAnalysis: {
        directCompetitors: competitors.slice(0, 3).map(comp => ({
          ...comp,
          annualRevenue: formatBudgetAmount(comp.annualRevenue * 1000000, locationKey),
        })),
        competitiveAdvantage: marketReality.viabilityScore < 40
          ? [
              `⚠️ REALITY CHECK: With ${marketReality.competitionLevel.toLowerCase()} competition and ${competitors.length} established players, advantages are limited`,
              `Need exceptional execution - ${marketReality.realProjections.failureRisk}% of businesses in this space fail`,
              'Must differentiate significantly or face commoditization',
              competitors.length > 5 ? `${competitors.length} competitors is too many - market consolidation likely` : 'Established competitors have significant resource advantages',
            ]
          : marketReality.viabilityScore < 60
          ? [
              `Understanding ${formData.country} market dynamics (${marketReality.saturationLevel.toLowerCase()} market)`,
              'Agility and customer focus vs. larger competitors',
              `Timing advantage in ${marketReality.realMarketGrowth}% growth market`,
              `Must overcome ${marketReality.entryBarrier.toLowerCase()} entry barriers and ${marketReality.competitionLevel.toLowerCase()} competition`,
            ]
          : [
              `Strong market opportunity with ${marketReality.realMarketGrowth}% growth in ${formData.country}`,
              `${marketReality.saturationLevel} market provides room for new entrants`,
              'First-mover or fast-follower advantage possible',
              'Customer-centric innovation in growing market',
              `Manageable ${marketReality.competitionLevel.toLowerCase()} competition`,
            ],
        differentiationStrategies: [
          {
            strategy: 'Customer Experience',
            description: 'Enhancing customer service and support',
            implementation: 'Training staff, improving processes',
            expectedImpact: 'Increased customer satisfaction and loyalty',
            timeline: '6 months',
          },
          {
            strategy: 'Product Innovation',
            description: 'Continuously improving and adding new features',
            implementation: 'R&D investment, customer feedback',
            expectedImpact: 'Higher market share and customer retention',
            timeline: '12 months',
          },
          {
            strategy: 'Marketing Campaigns',
            description: 'Launching targeted marketing initiatives',
            implementation: 'Budget allocation, creative content',
            expectedImpact: 'Increased brand awareness and sales',
            timeline: '3 months',
          },
        ],
        marketGaps: [
          'Lack of specialized products for niche markets',
          'Limited presence in rural areas',
          'Insufficient digital marketing efforts',
        ],
        competitivePositioning: 'Positioned as a leader in innovation and customer service, with a focus on niche markets and digital marketing.',
      },
    },

    organizationManagement: {
      organizationalStructure: 'Lean startup structure evolving to functional organization',
      managementTeam: [
        {
          role: 'CEO / Founder',
          responsibilities: [
            'Overall strategy and vision',
            'Investor relations and fundraising',
            'Key partnerships and business development',
            'Company culture and values',
          ],
          qualifications: 'Industry experience and entrepreneurial background',
          compensation: formatBudgetAmount(80000 * (locationInfo.marketMaturity === 'Mature' ? 1.2 : locationInfo.marketMaturity === 'Emerging' ? 0.7 : 1.0), locationKey),
        },
        {
          role: 'COO / Operations Manager',
          responsibilities: [
            'Day-to-day operations management',
            'Process optimization and efficiency',
            'Supply chain and vendor management',
            'Quality control and compliance',
          ],
          qualifications: 'Operations management experience in similar industry',
          compensation: formatBudgetAmount(70000 * (locationInfo.marketMaturity === 'Mature' ? 1.2 : locationInfo.marketMaturity === 'Emerging' ? 0.7 : 1.0), locationKey),
        },
        {
          role: 'Marketing Director',
          responsibilities: [
            'Brand strategy and positioning',
            'Customer acquisition and retention',
            'Digital marketing and social media',
            'Market research and analytics',
          ],
          qualifications: 'Marketing experience with proven track record',
          compensation: formatBudgetAmount(65000 * (locationInfo.marketMaturity === 'Mature' ? 1.2 : locationInfo.marketMaturity === 'Emerging' ? 0.7 : 1.0), locationKey),
        },
        {
          role: 'Finance Manager',
          responsibilities: [
            'Financial planning and analysis',
            'Budgeting and cash flow management',
            'Compliance and tax optimization',
            'Financial reporting to stakeholders',
          ],
          qualifications: 'Accounting/finance background with local tax knowledge',
          compensation: formatBudgetAmount(60000 * (locationInfo.marketMaturity === 'Mature' ? 1.2 : locationInfo.marketMaturity === 'Emerging' ? 0.7 : 1.0), locationKey),
        },
      ],
      advisoryBoard: [
        'Industry expert with 15+ years experience',
        'Serial entrepreneur with successful exits',
        `Local business leader with ${formData.country} market expertise`,
        'Financial advisor specializing in growth-stage companies',
      ],
      staffingPlan: {
        year1: 8,
        year2: 15,
        year3: 25,
        keyPositions: [
          'Customer service representatives',
          'Sales team members',
          'Technical/operational staff',
          'Administrative support',
        ],
      },
    },

    productsServices: {
      offerings: generateOfferings(formData.businessIdea, locationKey),
      productDevelopment: {
        currentStage: 'MVP development with customer validation',
        developmentTimeline: '6-12 months for full product suite',
        rdBudget: formatBudgetAmount(initialInvestment * 0.15, locationKey), // 15% of initial investment
      },
      intellectualProperty: [
        'Trademark registration for brand name and logo',
        'Domain names and digital assets',
        'Proprietary processes and methodologies',
        'Trade secrets and competitive know-how',
      ],
    },

    marketingStrategy: {
      brandingStrategy: `Position as a trusted, innovative provider in ${formData.country} with emphasis on quality, customer service, and local market expertise`,
      pricingStrategy: `Value-based pricing strategy considering ${formData.country}'s economic conditions (inflation: ${locationInfo.inflationRate}%), competitive landscape, and perceived value`,
      distributionChannels: [
        'Direct sales through company website and e-commerce platform',
        'Physical location/storefront (if applicable)',
        'Strategic partnerships with local distributors',
        'Online marketplaces and aggregator platforms',
        'B2B sales through account management team',
      ],
      promotionalStrategy: [
        {
          channel: 'Digital Marketing (SEO, SEM, Social Media)',
          budget: formatBudgetAmount(initialInvestment * 0.20, locationKey),
          expectedROI: '300-400%',
          timeline: 'Ongoing from launch',
        },
        {
          channel: 'Content Marketing & PR',
          budget: formatBudgetAmount(initialInvestment * 0.08, locationKey),
          expectedROI: '250-350%',
          timeline: 'Months 1-12',
        },
        {
          channel: 'Partnerships & Referrals',
          budget: formatBudgetAmount(initialInvestment * 0.05, locationKey),
          expectedROI: '400-500%',
          timeline: 'Months 3-24',
        },
        {
          channel: 'Events & Networking',
          budget: formatBudgetAmount(initialInvestment * 0.04, locationKey),
          expectedROI: '200-300%',
          timeline: 'Quarterly events',
        },
      ],
      salesStrategy: {
        salesProcess: [
          'Lead generation through marketing and referrals',
          'Initial contact and needs assessment',
          'Product demonstration and proposal',
          'Negotiation and closing',
          'Onboarding and relationship management',
          'Upselling and cross-selling',
        ],
        salesTargets: {
          year1: formatBudgetAmount(year1Revenue, locationKey),
          year2: formatBudgetAmount(year2Revenue, locationKey),
          year3: formatBudgetAmount(year3Revenue, locationKey),
        },
        customerAcquisitionCost: formatBudgetAmount(aov * (viability >= 60 ? 0.30 : viability >= 40 ? 0.50 : 0.80), locationKey),
        customerLifetimeValue: formatBudgetAmount(aov * (viability >= 60 ? 3.5 : viability >= 40 ? 2.0 : 1.2), locationKey),
      },
    },

    operationsPlan: {
      facilities: {
        type: determineFacilityType(formData.businessIdea),
        location: `Strategic location in ${formData.country}`,
        size: '2,000-3,000 sq ft',
        cost: formatBudgetAmount(initialInvestment * 0.12, locationKey),
      },
      equipment: [
        {
          item: 'Computer systems and software',
          cost: formatBudgetAmount(15000, locationKey),
          quantity: 8,
        },
        {
          item: 'Office furniture and fixtures',
          cost: formatBudgetAmount(8000, locationKey),
          quantity: 1,
        },
        {
          item: 'Industry-specific equipment',
          cost: formatBudgetAmount(25000, locationKey),
          quantity: 3,
        },
        {
          item: 'Communication systems',
          cost: formatBudgetAmount(5000, locationKey),
          quantity: 1,
        },
      ],
      suppliers: [
        {
          category: 'Primary Materials/Services',
          supplier: `Local ${formData.country} supplier`,
          terms: 'Net 30 payment terms',
          backup: 'Secondary supplier identified',
        },
        {
          category: 'Technology & Software',
          supplier: 'Cloud-based SaaS providers',
          terms: 'Monthly subscription',
          backup: 'Alternative platforms evaluated',
        },
        {
          category: 'Professional Services',
          supplier: 'Legal, accounting, consulting firms',
          terms: 'As-needed basis',
          backup: 'Multiple providers on retainer',
        },
      ],
      productionProcess: [
        'Order/request received and validated',
        'Resource allocation and scheduling',
        'Production/service delivery execution',
        'Quality control checkpoints',
        'Final delivery and customer confirmation',
        'Feedback collection and improvement',
      ],
      qualityControl: [
        'Standard operating procedures (SOPs) for all processes',
        'Regular quality audits and inspections',
        'Customer satisfaction surveys and NPS tracking',
        `Compliance with ${formData.country} industry standards and regulations`,
        'Continuous improvement based on data and feedback',
      ],
    },

    financialProjections: {
      startupCosts: {
        categories: [
          {
            category: 'Legal & Registration',
            amount: formatBudgetAmount(initialInvestment * 0.05, locationKey),
            description: `Business registration, licenses, permits in ${formData.country}`,
          },
          {
            category: 'Facilities & Equipment',
            amount: formatBudgetAmount(initialInvestment * 0.25, locationKey),
            description: 'Office/retail space, furniture, equipment, technology',
          },
          {
            category: 'Initial Inventory/Materials',
            amount: formatBudgetAmount(initialInvestment * 0.15, locationKey),
            description: 'Starting inventory, raw materials, supplies',
          },
          {
            category: 'Marketing & Branding',
            amount: formatBudgetAmount(initialInvestment * 0.20, locationKey),
            description: 'Website, branding, initial marketing campaigns',
          },
          {
            category: 'Professional Services',
            amount: formatBudgetAmount(initialInvestment * 0.08, locationKey),
            description: 'Legal, accounting, consulting fees',
          },
          {
            category: 'Working Capital',
            amount: formatBudgetAmount(initialInvestment * 0.22, locationKey),
            description: 'Operating expenses for first 3-6 months',
          },
          {
            category: 'Contingency Reserve',
            amount: formatBudgetAmount(initialInvestment * 0.05, locationKey),
            description: 'Emergency fund for unexpected expenses',
          },
        ],
        total: formatBudgetAmount(initialInvestment, locationKey),
      },
      fundingRequirements: {
        totalNeeded: formatBudgetAmount(initialInvestment, locationKey),
        sources: [
          {
            source: 'Founder Investment',
            amount: formatBudgetAmount(initialInvestment * 0.30, locationKey),
            terms: 'Equity ownership',
          },
          {
            source: 'Angel Investors / VC',
            amount: formatBudgetAmount(initialInvestment * 0.45, locationKey),
            terms: '20-30% equity stake',
          },
          {
            source: 'Bank Loan / Line of Credit',
            amount: formatBudgetAmount(initialInvestment * 0.25, locationKey),
            terms: `${locationInfo.interestRate}% interest, 5-year term`,
          },
        ],
      },
      revenueProjections: [
        {
          year: 1,
          revenue: formatBudgetAmount(year1Revenue, locationKey),
          cogs: formatBudgetAmount(year1Revenue * R1.cogs, locationKey),
          grossProfit: formatBudgetAmount(year1Revenue * R1.grossMarginFrac, locationKey),
          grossMargin: `${Math.round(R1.grossMarginFrac * 100)}%`,
          operatingExpenses: formatBudgetAmount(year1Revenue * R1.opexRate, locationKey),
          netProfit: formatBudgetAmount(year1Revenue * R1.nm, locationKey),
          netMargin: `${y1NM}%`,
        },
        {
          year: 2,
          revenue: formatBudgetAmount(year2Revenue, locationKey),
          cogs: formatBudgetAmount(year2Revenue * R2.cogs, locationKey),
          grossProfit: formatBudgetAmount(year2Revenue * R2.grossMarginFrac, locationKey),
          grossMargin: `${Math.round(R2.grossMarginFrac * 100)}%`,
          operatingExpenses: formatBudgetAmount(year2Revenue * R2.opexRate, locationKey),
          netProfit: formatBudgetAmount(year2Revenue * R2.nm, locationKey),
          netMargin: `${y2NM}%`,
        },
        {
          year: 3,
          revenue: formatBudgetAmount(year3Revenue, locationKey),
          cogs: formatBudgetAmount(year3Revenue * R3.cogs, locationKey),
          grossProfit: formatBudgetAmount(year3Revenue * R3.grossMarginFrac, locationKey),
          grossMargin: `${Math.round(R3.grossMarginFrac * 100)}%`,
          operatingExpenses: formatBudgetAmount(year3Revenue * R3.opexRate, locationKey),
          netProfit: formatBudgetAmount(year3Revenue * R3.nm, locationKey),
          netMargin: `${y3NM}%`,
        },
      ],
      detailedYearlyBreakdown: [
        {
          year: 1,
          quarters: [
            buildQ(year1Revenue, R1, 'Q1', Math.round(y1Cust * 0.18)),
            buildQ(year1Revenue, R1, 'Q2', Math.round(y1Cust * 0.22)),
            buildQ(year1Revenue, R1, 'Q3', Math.round(y1Cust * 0.27)),
            buildQ(year1Revenue, R1, 'Q4', Math.round(y1Cust * 0.33)),
          ],
          keyMetrics: {
            totalCustomers: y1Cust,
            customerGrowthRate: 'N/A (Year 1)',
            averageRevenuePerCustomer: formatBudgetAmount(year1Revenue / Math.max(y1Cust, 1), locationKey),
            churnRate: y1Churn,
            employeeCount: 8,
            revenuePerEmployee: formatBudgetAmount(year1Revenue / 8, locationKey),
            operatingCashFlow: formatBudgetAmount(year1Revenue * R1.ocf, locationKey),
            freeCashFlow: formatBudgetAmount(year1Revenue * R1.fcf, locationKey),
            ebitda: formatBudgetAmount(year1Revenue * R1.ebitda, locationKey),
            ebitdaMargin: `${Math.round(R1.ebitda * 100)}%`,
          },
        },
        {
          year: 2,
          quarters: [
            buildQ(year2Revenue, R2, 'Q1', Math.round(y2Cust * 0.20)),
            buildQ(year2Revenue, R2, 'Q2', Math.round(y2Cust * 0.24)),
            buildQ(year2Revenue, R2, 'Q3', Math.round(y2Cust * 0.27)),
            buildQ(year2Revenue, R2, 'Q4', Math.round(y2Cust * 0.29)),
          ],
          keyMetrics: {
            totalCustomers: y2Cust,
            customerGrowthRate: cgr2,
            averageRevenuePerCustomer: formatBudgetAmount(year2Revenue / Math.max(y2Cust, 1), locationKey),
            churnRate: y2Churn,
            employeeCount: 15,
            revenuePerEmployee: formatBudgetAmount(year2Revenue / 15, locationKey),
            operatingCashFlow: formatBudgetAmount(year2Revenue * R2.ocf, locationKey),
            freeCashFlow: formatBudgetAmount(year2Revenue * R2.fcf, locationKey),
            ebitda: formatBudgetAmount(year2Revenue * R2.ebitda, locationKey),
            ebitdaMargin: `${Math.round(R2.ebitda * 100)}%`,
          },
        },
        {
          year: 3,
          quarters: [
            buildQ(year3Revenue, R3, 'Q1', Math.round(y3Cust * 0.21)),
            buildQ(year3Revenue, R3, 'Q2', Math.round(y3Cust * 0.24)),
            buildQ(year3Revenue, R3, 'Q3', Math.round(y3Cust * 0.27)),
            buildQ(year3Revenue, R3, 'Q4', Math.round(y3Cust * 0.28)),
          ],
          keyMetrics: {
            totalCustomers: y3Cust,
            customerGrowthRate: cgr3,
            averageRevenuePerCustomer: formatBudgetAmount(year3Revenue / Math.max(y3Cust, 1), locationKey),
            churnRate: y3Churn,
            employeeCount: 25,
            revenuePerEmployee: formatBudgetAmount(year3Revenue / 25, locationKey),
            operatingCashFlow: formatBudgetAmount(year3Revenue * R3.ocf, locationKey),
            freeCashFlow: formatBudgetAmount(year3Revenue * R3.fcf, locationKey),
            ebitda: formatBudgetAmount(year3Revenue * R3.ebitda, locationKey),
            ebitdaMargin: `${Math.round(R3.ebitda * 100)}%`,
          },
        },
      ],
      fiveYearProjections: [
        {
          year: 1,
          revenue: formatBudgetAmount(year1Revenue, locationKey),
          netProfit: y1NM >= 0
            ? formatBudgetAmount(year1Revenue * R1.nm, locationKey)
            : `LOSS: ${formatBudgetAmount(Math.abs(year1Revenue * R1.nm), locationKey)}`,
          cashReserves: formatBudgetAmount(bs1.cashReserves, locationKey),
          totalAssets: formatBudgetAmount(bs1.totalAssets, locationKey),
          totalLiabilities: formatBudgetAmount(bs1.totalLiabilities, locationKey),
          equity: formatBudgetAmount(bs1.equity, locationKey),
          returnOnEquity: `${bs1.roe.toFixed(1)}%`,
          returnOnAssets: `${bs1.roa.toFixed(1)}%`,
        },
        {
          year: 2,
          revenue: formatBudgetAmount(year2Revenue, locationKey),
          netProfit: y2NM >= 0
            ? formatBudgetAmount(year2Revenue * R2.nm, locationKey)
            : `LOSS: ${formatBudgetAmount(Math.abs(year2Revenue * R2.nm), locationKey)}`,
          cashReserves: formatBudgetAmount(bs2.cashReserves, locationKey),
          totalAssets: formatBudgetAmount(bs2.totalAssets, locationKey),
          totalLiabilities: formatBudgetAmount(bs2.totalLiabilities, locationKey),
          equity: formatBudgetAmount(bs2.equity, locationKey),
          returnOnEquity: `${bs2.roe.toFixed(1)}%`,
          returnOnAssets: `${bs2.roa.toFixed(1)}%`,
        },
        {
          year: 3,
          revenue: formatBudgetAmount(year3Revenue, locationKey),
          netProfit: y3NM >= 0
            ? formatBudgetAmount(year3Revenue * R3.nm, locationKey)
            : `LOSS: ${formatBudgetAmount(Math.abs(year3Revenue * R3.nm), locationKey)}`,
          cashReserves: formatBudgetAmount(bs3.cashReserves, locationKey),
          totalAssets: formatBudgetAmount(bs3.totalAssets, locationKey),
          totalLiabilities: formatBudgetAmount(bs3.totalLiabilities, locationKey),
          equity: formatBudgetAmount(bs3.equity, locationKey),
          returnOnEquity: `${bs3.roe.toFixed(1)}%`,
          returnOnAssets: `${bs3.roa.toFixed(1)}%`,
        },
        {
          year: 4,
          revenue: formatBudgetAmount(y4Rev, locationKey),
          netProfit: y4NM >= 0
            ? formatBudgetAmount(y4Rev * R4.nm, locationKey)
            : `LOSS: ${formatBudgetAmount(Math.abs(y4Rev * R4.nm), locationKey)}`,
          cashReserves: formatBudgetAmount(bs4.cashReserves, locationKey),
          totalAssets: formatBudgetAmount(bs4.totalAssets, locationKey),
          totalLiabilities: formatBudgetAmount(bs4.totalLiabilities, locationKey),
          equity: formatBudgetAmount(bs4.equity, locationKey),
          returnOnEquity: `${bs4.roe.toFixed(1)}%`,
          returnOnAssets: `${bs4.roa.toFixed(1)}%`,
        },
        {
          year: 5,
          revenue: formatBudgetAmount(y5Rev, locationKey),
          netProfit: y5NM >= 0
            ? formatBudgetAmount(y5Rev * R5.nm, locationKey)
            : `LOSS: ${formatBudgetAmount(Math.abs(y5Rev * R5.nm), locationKey)}`,
          cashReserves: formatBudgetAmount(bs5.cashReserves, locationKey),
          totalAssets: formatBudgetAmount(bs5.totalAssets, locationKey),
          totalLiabilities: formatBudgetAmount(bs5.totalLiabilities, locationKey),
          equity: formatBudgetAmount(bs5.equity, locationKey),
          returnOnEquity: `${bs5.roe.toFixed(1)}%`,
          returnOnAssets: `${bs5.roa.toFixed(1)}%`,
        },
      ],
      monthlyYear1Breakdown,
      cashFlowProjection: {
        year1Monthly: true,
        breakEvenMonth: locationInfo.marketMaturity === 'Mature'
          ? (viability >= 60 ? 8 : viability >= 40 ? 12 : 20)
          : locationInfo.marketMaturity === 'Emerging'
          ? (viability >= 60 ? 12 : viability >= 40 ? 18 : 30)
          : (viability >= 60 ? 10 : viability >= 40 ? 15 : 24),
        minimumCashBalance: formatBudgetAmount(initialInvestment * 0.12, locationKey),
      },
      financialAssumptions: {
        revenueGrowthRate: year1Revenue > 0
          ? `${((year2Revenue - year1Revenue) / year1Revenue * 100).toFixed(1)}% year 1→2, ${year2Revenue > 0 ? ((year3Revenue - year2Revenue) / year2Revenue * 100).toFixed(1) : 'N/A'}% year 2→3`
          : 'Insufficient revenue base in Year 1',
        cogsPercentage: `${Math.round(R1.cogs * 100)}-${Math.round(R3.cogs * 100)}% of revenue (improves with operational scale)`,
        operatingExpenseGrowth: `${(locationInfo.inflationRate + 2).toFixed(1)}% annually (${locationInfo.inflationRate}% inflation + 2% efficiency overhead)`,
        corporateTaxRate: `${locationInfo.corporateTaxRate}% (${formData.country} statutory rate)`,
        inflationRate: `${locationInfo.inflationRate}% (${formData.country})`,
        gdpGrowthRate: `${locationInfo.gdpGrowthRate}% (${formData.country})`,
      },
    },

    riskAnalysis: {
      risks: [
        {
          category: 'Market Risk',
          description: `Economic downturn in ${formData.country} affecting customer spending`,
          likelihood: locationInfo.riskLevel === 'High' ? 'High' : 'Medium',
          impact: 'High',
          mitigation: 'Diversify customer base, build cash reserves, flexible cost structure',
        },
        {
          category: 'Competitive Risk',
          description: 'Increased competition from established or new entrants',
          likelihood: 'Medium',
          impact: 'Medium',
          mitigation: 'Strong differentiation, customer loyalty programs, continuous innovation',
        },
        {
          category: 'Regulatory Risk',
          description: `Changes in ${formData.country} regulations (complexity: ${locationInfo.regulatoryComplexity})`,
          likelihood: locationInfo.regulatoryComplexity === 'High' ? 'High' : 'Medium',
          impact: 'Medium',
          mitigation: 'Legal counsel on retainer, industry association membership, proactive compliance',
        },
        {
          category: 'Operational Risk',
          description: 'Supply chain disruptions or key personnel loss',
          likelihood: 'Medium',
          impact: 'High',
          mitigation: 'Multiple suppliers, documented processes, succession planning, insurance',
        },
        {
          category: 'Financial Risk',
          description: 'Cash flow challenges or inability to secure additional funding',
          likelihood: 'Medium',
          impact: 'High',
          mitigation: 'Conservative financial planning, strong investor relationships, credit facilities',
        },
        {
          category: 'Technology Risk',
          description: 'System failures or cybersecurity breaches',
          likelihood: 'Low',
          impact: 'High',
          mitigation: 'Regular backups, cybersecurity measures, disaster recovery plan',
        },
      ],
      contingencyPlans: [
        'Emergency cash reserve of 6 months operating expenses',
        'Flexible staffing arrangements to adjust costs quickly',
        'Pre-negotiated credit line for unexpected needs',
        'Scalable business model that can grow or contract',
        'Regular scenario planning and stress testing',
      ],
      insurance: [
        {
          type: 'General Liability Insurance',
          coverage: formatBudgetAmount(2000000, locationKey),
          annualCost: formatBudgetAmount(5000, locationKey),
        },
        {
          type: 'Professional Liability / E&O',
          coverage: formatBudgetAmount(1000000, locationKey),
          annualCost: formatBudgetAmount(3500, locationKey),
        },
        {
          type: 'Property Insurance',
          coverage: formatBudgetAmount(500000, locationKey),
          annualCost: formatBudgetAmount(2000, locationKey),
        },
        {
          type: 'Business Interruption',
          coverage: formatBudgetAmount(750000, locationKey),
          annualCost: formatBudgetAmount(2500, locationKey),
        },
      ],
    },

    implementationTimeline: {
      phases: [
        {
          phase: 'Phase 1: Foundation (Months 0-3)',
          duration: '3 months',
          milestones: [
            {
              milestone: 'Business registration and legal setup',
              deadline: 'Month 1',
              owner: 'Founder/Legal Team',
              status: 'Pending',
            },
            {
              milestone: 'Secure initial funding',
              deadline: 'Month 1',
              owner: 'Founder/CFO',
              status: 'Pending',
            },
            {
              milestone: 'Location selection and lease negotiation',
              deadline: 'Month 2',
              owner: 'COO',
              status: 'Pending',
            },
            {
              milestone: 'Hire core team members',
              deadline: 'Month 3',
              owner: 'Founder/HR',
              status: 'Pending',
            },
            {
              milestone: 'Brand development and website launch',
              deadline: 'Month 3',
              owner: 'Marketing Director',
              status: 'Pending',
            },
          ],
        },
        {
          phase: 'Phase 2: Development (Months 3-6)',
          duration: '3 months',
          milestones: [
            {
              milestone: 'Product/service development complete',
              deadline: 'Month 5',
              owner: 'COO',
              status: 'Pending',
            },
            {
              milestone: 'Operations systems and processes established',
              deadline: 'Month 5',
              owner: 'COO',
              status: 'Pending',
            },
            {
              milestone: 'Initial marketing campaigns launched',
              deadline: 'Month 4',
              owner: 'Marketing Director',
              status: 'Pending',
            },
            {
              milestone: 'Beta testing with pilot customers',
              deadline: 'Month 6',
              owner: 'Founder/COO',
              status: 'Pending',
            },
            {
              milestone: 'Supplier agreements finalized',
              deadline: 'Month 5',
              owner: 'COO',
              status: 'Pending',
            },
          ],
        },
        {
          phase: 'Phase 3: Launch (Months 6-9)',
          duration: '3 months',
          milestones: [
            {
              milestone: 'Official business launch',
              deadline: 'Month 7',
              owner: 'Founder',
              status: 'Pending',
            },
            {
              milestone: 'First 100 customers acquired',
              deadline: 'Month 8',
              owner: 'Sales Team',
              status: 'Pending',
            },
            {
              milestone: 'Full team hired and onboarded',
              deadline: 'Month 8',
              owner: 'HR/Management',
              status: 'Pending',
            },
            {
              milestone: 'Customer feedback loop established',
              deadline: 'Month 9',
              owner: 'Marketing/Operations',
              status: 'Pending',
            },
          ],
        },
        {
          phase: 'Phase 4: Growth (Months 9-18)',
          duration: '9 months',
          milestones: [
            {
              milestone: 'Break-even achieved',
              deadline: `Month ${locationInfo.marketMaturity === 'Mature' ? '14' : '16'}`,
              owner: 'CFO',
              status: 'Pending',
            },
            {
              milestone: 'Scale marketing and sales efforts',
              deadline: 'Month 12',
              owner: 'Marketing/Sales',
              status: 'Pending',
            },
            {
              milestone: 'Product/service expansion',
              deadline: 'Month 15',
              owner: 'Product Team',
              status: 'Pending',
            },
            {
              milestone: 'Series A funding (if applicable)',
              deadline: 'Month 18',
              owner: 'Founder/CFO',
              status: 'Pending',
            },
          ],
        },
        {
          phase: 'Phase 5: Scaling (Months 18-36)',
          duration: '18 months',
          milestones: [
            {
              milestone: 'Geographic expansion planning',
              deadline: 'Month 24',
              owner: 'Executive Team',
              status: 'Pending',
            },
            {
              milestone: 'Achieve target revenue',
              deadline: 'Month 36',
              owner: 'CEO/CFO',
              status: 'Pending',
            },
            {
              milestone: 'Build strategic partnerships',
              deadline: 'Month 30',
              owner: 'BD Team',
              status: 'Pending',
            },
            {
              milestone: 'Evaluate exit opportunities',
              deadline: 'Month 36',
              owner: 'Founder/Board',
              status: 'Pending',
            },
          ],
        },
      ],
    },

    exitStrategy: {
      options: [
        {
          strategy: 'Acquisition by Strategic Buyer',
          timeline: '3-5 years',
          expectedReturn: `${formatBudgetAmount(targetRevenueNum * 3, locationKey)} - ${formatBudgetAmount(targetRevenueNum * 5, locationKey)}`,
          conditions: [
            'Proven business model with consistent revenue',
            'Strong customer base and market position',
            'Attractive to larger industry players',
            'Clean financials and legal standing',
          ],
        },
        {
          strategy: 'Merger with Competitor',
          timeline: '4-6 years',
          expectedReturn: `${formatBudgetAmount(targetRevenueNum * 2.5, locationKey)} - ${formatBudgetAmount(targetRevenueNum * 4, locationKey)}`,
          conditions: [
            'Complementary capabilities and market presence',
            'Synergies that create value for both parties',
            'Cultural alignment and compatible visions',
            'Win-win negotiation outcome',
          ],
        },
        {
          strategy: 'Management Buyout',
          timeline: '5-7 years',
          expectedReturn: `${formatBudgetAmount(targetRevenueNum * 2, locationKey)} - ${formatBudgetAmount(targetRevenueNum * 3, locationKey)}`,
          conditions: [
            'Strong management team with financial capacity',
            'Stable and profitable business operations',
            'Owner ready to transition out',
            'Financing arranged for buyout',
          ],
        },
        {
          strategy: 'IPO (Public Listing)',
          timeline: '7-10 years',
          expectedReturn: `${formatBudgetAmount(targetRevenueNum * 5, locationKey)} - ${formatBudgetAmount(targetRevenueNum * 10, locationKey)}`,
          conditions: [
            'Significant scale and market position',
            'Strong growth trajectory and profitability',
            'Professional management and governance',
            'Favorable market conditions',
          ],
        },
      ],
    },
  };
}

function generateBusinessModel(businessIdea: string): string {
  const idea = businessIdea.toLowerCase();
  
  if (idea.includes('subscription') || idea.includes('saas') || idea.includes('software')) {
    return 'Subscription-based SaaS model with recurring monthly/annual revenue';
  } else if (idea.includes('marketplace') || idea.includes('platform')) {
    return 'Two-sided marketplace platform earning commission on transactions';
  } else if (idea.includes('ecommerce') || idea.includes('e-commerce') || idea.includes('online store')) {
    return 'E-commerce retail model with direct-to-consumer sales';
  } else if (idea.includes('consulting') || idea.includes('service')) {
    return 'Professional services model with project-based and retainer fees';
  } else if (idea.includes('rental') || idea.includes('sharing')) {
    return 'Sharing economy model with usage-based pricing';
  } else {
    return 'Hybrid business model combining product sales with value-added services';
  }
}

function generateOfferings(businessIdea: string, locationKey: string): Array<any> {
  return [
    {
      name: 'Core Offering',
      description: `Primary product/service based on ${businessIdea}`,
      features: [
        'High quality and reliability',
        'Competitive pricing',
        'Excellent customer support',
        'Customization options available',
      ],
      pricing: formatBudgetAmount(199, locationKey),
      profitMargin: '60-70%',
    },
    {
      name: 'Premium Offering',
      description: 'Enhanced version with additional features and benefits',
      features: [
        'All core features included',
        'Priority support and service',
        'Advanced capabilities',
        'Dedicated account management',
      ],
      pricing: formatBudgetAmount(399, locationKey),
      profitMargin: '65-75%',
    },
    {
      name: 'Enterprise Solution',
      description: 'Fully customized solution for large organizations',
      features: [
        'Custom integration and setup',
        'Volume discounts available',
        'SLA guarantees',
        'Training and onboarding',
      ],
      pricing: 'Custom pricing based on requirements',
      profitMargin: '55-65%',
    },
  ];
}

function determineFacilityType(businessIdea: string): string {
  const idea = businessIdea.toLowerCase();
  
  if (idea.includes('restaurant') || idea.includes('cafe') || idea.includes('food')) {
    return 'Commercial kitchen and dining space';
  } else if (idea.includes('retail') || idea.includes('store')) {
    return 'Retail storefront with customer access';
  } else if (idea.includes('software') || idea.includes('tech') || idea.includes('digital')) {
    return 'Modern office space with collaborative work areas';
  } else if (idea.includes('manufacturing') || idea.includes('production')) {
    return 'Industrial facility with production floor';
  } else if (idea.includes('warehouse') || idea.includes('logistics')) {
    return 'Warehouse and distribution center';
  } else {
    return 'Professional office space';
  }
}