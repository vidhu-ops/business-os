// @ts-nocheck
// Real companies database organized by location and industry
// This provides actual competitor data for business plans based on location

interface CompanyData {
  name: string;
  location: string;
  foundedYear: number;
  annualRevenue: number; // in USD millions
  employeeCount: string;
  strengths: string[];
  weaknesses: string[];
  marketShare: string;
  keyProducts: string[];
  recentProjects: string[];
  customerBase: string;
  pricingModel: string;
  marketingApproach: string[];
}

interface IndustryCompanies {
  [key: string]: CompanyData[];
}

interface LocationCompanies {
  [key: string]: IndustryCompanies;
}

// Real company data by location and industry
export const realCompaniesDatabase: LocationCompanies = {
  'global': {
    'manufacturing': [
      {
        name: 'Siemens AG',
        location: 'Germany (Global Operations)',
        foundedYear: 1847,
        annualRevenue: 88000,
        employeeCount: '311K+',
        strengths: ['Industrial automation leadership', 'Digitalization (Siemens Xcelerator)', 'Energy transition expertise', 'Global service network'],
        weaknesses: ['Complexity of portfolio', 'Exposure to cyclical industrial markets', 'Software transition costs'],
        marketShare: '12%',
        keyProducts: ['SIMATIC PLCs', 'Sinumerik CNC', 'Xcelerator digital platform', 'Siemens Healthineers', 'Gas turbines'],
        recentProjects: ['Xcelerator digital business platform', 'Smart infrastructure expansion', 'Low-carbon energy systems', 'Rail automation'],
        customerBase: 'Industrial manufacturers, utilities, infrastructure operators',
        pricingModel: 'Enterprise licensing + long-term service contracts',
        marketingApproach: ['Direct enterprise sales', 'System integrator partnerships', 'Hannover Messe presence', 'Digital twin showcases']
      },
      {
        name: 'Honeywell International',
        location: 'United States (Global Operations)',
        foundedYear: 1906,
        annualRevenue: 36700,
        employeeCount: '99K+',
        strengths: ['Aerospace & defense portfolio', 'Building automation leadership', 'Software-industrial pivot', 'Recurring revenue streams'],
        weaknesses: ['Portfolio complexity post-spin-offs', 'Slower growth than pure-play software', 'Defense budget exposure'],
        marketShare: '8%',
        keyProducts: ['Aerospace components', 'Building management systems', 'Process control (DCS)', 'Safety products', 'Connected plant software'],
        recentProjects: ['Honeywell Forge IIoT platform', 'Sustainable aviation fuel', 'Carbon capture technology', 'Quantum computing'],
        customerBase: 'Aerospace OEMs, petrochemical plants, commercial buildings, defense contractors',
        pricingModel: 'Hardware + long-term service agreements + SaaS',
        marketingApproach: ['Direct sales to enterprises', 'Distributor network', 'Industry conferences', 'Digital transformation positioning']
      },
      {
        name: '3M Company',
        location: 'United States (Global Operations)',
        foundedYear: 1902,
        annualRevenue: 32700,
        employeeCount: '85K+',
        strengths: ['60,000+ product portfolio', 'R&D investment (6% of revenue)', 'Brand reputation', 'Material science expertise'],
        weaknesses: ['PFAS litigation exposure ($10B+ settlement)', 'Revenue growth stagnation', 'Portfolio complexity'],
        marketShare: '6%',
        keyProducts: ['Post-it Notes', 'Scotch tape', 'N95 respirators', 'Industrial abrasives', 'Automotive films'],
        recentProjects: ['PFAS remediation', 'Healthcare spin-off (Solventum)', 'Sustainability 2025 goals', 'Advanced electronics materials'],
        customerBase: 'Industrial manufacturers, healthcare systems, consumers, automotive OEMs',
        pricingModel: 'Premium product pricing + volume discounts',
        marketingApproach: ['B2B distributor network', 'Trade shows', 'Technical specialists', 'Digital platforms']
      },
      {
        name: 'Caterpillar Inc.',
        location: 'United States (Global Operations)',
        foundedYear: 1925,
        annualRevenue: 67060,
        employeeCount: '113K+',
        strengths: ['Construction equipment dominance', 'Dealer network (160 countries)', 'Cat Financial services', 'Mining and energy exposure'],
        weaknesses: ['Cyclical demand volatility', 'Exposure to commodity sectors', 'Electric transition challenges'],
        marketShare: '18%',
        keyProducts: ['Excavators', 'Bulldozers', 'Mining trucks', 'Gas turbines', 'Cat engines'],
        recentProjects: ['Zero-emission equipment line', 'Autonomous mining trucks', 'Cat Financial expansion', 'Digital solutions (Cat Central)'],
        customerBase: 'Construction companies, mining operators, utilities, oil & gas companies',
        pricingModel: 'Capital equipment sales + parts + service contracts',
        marketingApproach: ['Global dealer network', 'Industry shows (ConExpo)', 'Rental partnerships', 'Fleet management solutions']
      },
      {
        name: 'ABB Ltd',
        location: 'Switzerland (Global Operations)',
        foundedYear: 1988,
        annualRevenue: 32200,
        employeeCount: '105K+',
        strengths: ['Robotics leadership (ABB Robotics #1 globally)', 'Electrification expertise', 'Process automation', 'Motion systems'],
        weaknesses: ['Complex organizational structure', 'Competition from Fanuc and KUKA', 'Commodity exposure'],
        marketShare: '9%',
        keyProducts: ['Industrial robots', 'Low voltage products', 'Drives and motors', 'Power grids', 'Collaborative robots (YuMi)'],
        recentProjects: ['OmniCore robot controller', 'EV charging infrastructure', 'AI-powered process optimization', 'ABB Ability digital platform'],
        customerBase: 'Automotive OEMs, food & beverage, pharma, utilities, mining',
        pricingModel: 'System integration contracts + service agreements + subscriptions',
        marketingApproach: ['Direct sales to manufacturers', 'System integrator channel', 'Industry verticals approach', 'Trade exhibitions']
      },
    ]
  },
  'united-states': {
    'manufacturing': [
      {
        name: 'Caterpillar Inc.',
        location: 'United States',
        foundedYear: 1925,
        annualRevenue: 67060,
        employeeCount: '113K+',
        strengths: ['Construction equipment dominance', 'Dealer network (160 countries)', 'Cat Financial services', 'Mining and energy exposure'],
        weaknesses: ['Cyclical demand volatility', 'Exposure to commodity sectors', 'Electric equipment transition costs'],
        marketShare: '18%',
        keyProducts: ['Excavators', 'Bulldozers', 'Mining trucks', 'Gas turbines', 'Cat engines'],
        recentProjects: ['Zero-emission equipment line', 'Autonomous mining trucks', 'Cat Financial expansion', 'Digital solutions (Cat Central)'],
        customerBase: 'Construction companies, mining operators, utilities, oil & gas companies',
        pricingModel: 'Capital equipment sales + parts & service contracts',
        marketingApproach: ['Global dealer network', 'Industry shows (ConExpo)', 'Rental partnerships', 'Fleet management solutions']
      },
      {
        name: 'Honeywell International',
        location: 'United States',
        foundedYear: 1906,
        annualRevenue: 36700,
        employeeCount: '99K+',
        strengths: ['Aerospace & defense portfolio', 'Building automation leadership', 'Software-industrial pivot', 'Recurring revenue streams'],
        weaknesses: ['Portfolio complexity post-spin-offs', 'Slower growth vs pure-play software', 'Cyclical exposure'],
        marketShare: '8%',
        keyProducts: ['Aerospace components', 'Building management systems', 'Process control (DCS)', 'Safety products', 'Connected plant software'],
        recentProjects: ['Honeywell Forge IIoT platform', 'Sustainable aviation fuel', 'Carbon capture technology', 'Quantum computing division'],
        customerBase: 'Aerospace OEMs, petrochemical plants, commercial buildings, defense contractors',
        pricingModel: 'Hardware + long-term service agreements + SaaS subscriptions',
        marketingApproach: ['Direct enterprise sales', 'Distributor network', 'Industry conferences', 'Digital transformation partnerships']
      },
      {
        name: '3M Company',
        location: 'United States',
        foundedYear: 1902,
        annualRevenue: 32700,
        employeeCount: '85K+',
        strengths: ['60,000+ product portfolio', 'R&D investment (6% of revenue)', 'Brand reputation', 'Material science expertise'],
        weaknesses: ['PFAS litigation exposure ($10B+ settlement)', 'Revenue growth stagnation', 'Healthcare spin-off complexity'],
        marketShare: '6%',
        keyProducts: ['Industrial adhesives & abrasives', 'N95 respirators', 'Automotive films', 'Electronics materials', 'Post-it Notes'],
        recentProjects: ['PFAS remediation program', 'Solventum healthcare spin-off', 'Sustainability 2025 goals', 'Advanced electronics materials'],
        customerBase: 'Industrial manufacturers, healthcare systems, consumers, automotive OEMs',
        pricingModel: 'Premium product pricing + volume distributor discounts',
        marketingApproach: ['B2B distributor network', 'Trade shows (NPE, Pack Expo)', 'Technical specialists', 'E-commerce platforms']
      },
      {
        name: 'Parker Hannifin',
        location: 'United States',
        foundedYear: 1917,
        annualRevenue: 19960,
        employeeCount: '62K+',
        strengths: ['Motion & control breadth (480,000 part numbers)', 'Aerospace segment margins', 'Meggitt acquisition synergies', 'Aftermarket revenue'],
        weaknesses: ['Debt from acquisitions', 'Exposure to oil & gas capex cycles', 'Industrial distribution fragmentation'],
        marketShare: '7%',
        keyProducts: ['Hydraulic systems', 'Pneumatic components', 'Aerospace actuators', 'Filtration systems', 'Electromechanical drives'],
        recentProjects: ['Meggitt aerospace integration', 'Electrification of motion control', 'Industrial IoT connectivity', 'Hydrogen fuel cell systems'],
        customerBase: 'Aerospace OEMs, oil & gas, manufacturing, food & beverage, semiconductor',
        pricingModel: 'Component pricing + system integration + service contracts',
        marketingApproach: ['Distributor network (3,000+ distributors)', 'Direct OEM accounts', 'Engineering support teams', 'Industry trade shows']
      },
      {
        name: 'Illinois Tool Works (ITW)',
        location: 'United States',
        foundedYear: 1912,
        annualRevenue: 15900,
        employeeCount: '45K+',
        strengths: ['80/20 business simplification model', 'High operating margins (26%+)', 'Diverse end market exposure', '84 divisions with product leadership'],
        weaknesses: ['Organic revenue growth modest (3-5%)', 'Premium pricing limits market share', 'Niche focus limits addressable markets'],
        marketShare: '5%',
        keyProducts: ['Welding equipment (Miller, Hobart)', 'Test & measurement (Instron)', 'Food equipment (Vulcan)', 'Construction fasteners', 'Automotive components'],
        recentProjects: ['Enterprise initiatives for margin expansion', 'EV-related automotive components', 'Sustainablity reporting', 'Digital customer tools'],
        customerBase: 'Automotive, food service, construction, industrial MRO customers',
        pricingModel: 'Premium pricing strategy with high customer retention',
        marketingApproach: ['Direct sales to key OEM accounts', 'Distributor channel for MRO', 'Segment-specific digital marketing', 'Technical support']
      }
    ],
    'retail': [
      {
        name: 'Walmart',
        location: 'United States',
        foundedYear: 1962,
        annualRevenue: 611000,
        employeeCount: '2.3M+',
        strengths: ['Massive scale', 'Supply chain efficiency', 'Everyday low prices', 'Omnichannel presence'],
        weaknesses: ['Margin pressure', 'Labor relations', 'E-commerce catching up'],
        marketShare: '22%',
        keyProducts: ['Groceries', 'General merchandise', 'Electronics', 'Pharmacy'],
        recentProjects: ['Walmart+ subscription service', 'Automated fulfillment centers', 'Drone delivery pilots'],
        customerBase: 'Mass market consumers',
        pricingModel: 'Everyday low pricing',
        marketingApproach: ['TV advertising', 'Digital marketing', 'Local promotions', 'Email campaigns']
      },
      {
        name: 'Target Corporation',
        location: 'United States',
        foundedYear: 1902,
        annualRevenue: 109000,
        employeeCount: '450K+',
        strengths: ['Brand perception', 'Design partnerships', 'Store experience', 'Same-day delivery'],
        weaknesses: ['Higher prices vs Walmart', 'Limited international presence', 'Supply chain complexity'],
        marketShare: '8%',
        keyProducts: ['Apparel', 'Home goods', 'Groceries', 'Beauty products'],
        recentProjects: ['Store remodels', 'Shipt acquisition integration', 'Private label expansion'],
        customerBase: 'Middle-income families',
        pricingModel: 'Competitive with selective premium',
        marketingApproach: ['Social media', 'Influencer partnerships', 'Circular catalog', 'TV advertising']
      },
      {
        name: 'Costco Wholesale',
        location: 'United States',
        foundedYear: 1983,
        annualRevenue: 242000,
        employeeCount: '316K+',
        strengths: ['Member loyalty', 'Bulk pricing', 'Kirkland brand', 'Employee satisfaction'],
        weaknesses: ['Membership required', 'Limited product selection', 'Warehouse format'],
        marketShare: '6%',
        keyProducts: ['Bulk groceries', 'Electronics', 'Kirkland Signature', 'Gasoline'],
        recentProjects: ['E-commerce expansion', 'New warehouse openings', 'Renewable energy installations'],
        customerBase: 'Middle to upper-middle class families',
        pricingModel: 'Membership + low markup',
        marketingApproach: ['Word of mouth', 'Direct mail', 'Email marketing', 'Treasure hunt merchandising']
      }
    ],
    'technology': [
      {
        name: 'Microsoft Corporation',
        location: 'United States',
        foundedYear: 1975,
        annualRevenue: 211000,
        employeeCount: '221K+',
        strengths: ['Cloud computing (Azure)', 'Enterprise relationships', 'Recurring revenue', 'AI investment'],
        weaknesses: ['Mobile ecosystem', 'Gaming profitability', 'Antitrust scrutiny'],
        marketShare: '28%',
        keyProducts: ['Windows', 'Office 365', 'Azure', 'LinkedIn', 'Xbox'],
        recentProjects: ['OpenAI partnership', 'Activision Blizzard acquisition', 'Microsoft Copilot AI'],
        customerBase: 'Enterprises and consumers',
        pricingModel: 'Subscription and licensing',
        marketingApproach: ['Enterprise sales', 'Partner ecosystem', 'Digital advertising', 'Developer relations']
      },
      {
        name: 'Salesforce Inc.',
        location: 'United States',
        foundedYear: 1999,
        annualRevenue: 31000,
        employeeCount: '79K+',
        strengths: ['CRM market leadership', 'Platform ecosystem', 'Customer success', 'Innovation'],
        weaknesses: ['High costs', 'Complexity', 'Competition increasing'],
        marketShare: '23%',
        keyProducts: ['Sales Cloud', 'Service Cloud', 'Marketing Cloud', 'Tableau', 'Slack'],
        recentProjects: ['Einstein AI enhancement', 'Slack integration', 'Industry-specific solutions'],
        customerBase: 'B2B companies',
        pricingModel: 'Tiered subscription',
        marketingApproach: ['Dreamforce conference', 'Content marketing', 'Partner channels', 'AppExchange']
      },
      {
        name: 'Oracle Corporation',
        location: 'United States',
        foundedYear: 1977,
        annualRevenue: 50000,
        employeeCount: '164K+',
        strengths: ['Database dominance', 'Enterprise lock-in', 'Cloud infrastructure', 'Acquisitions'],
        weaknesses: ['Legacy perception', 'Customer satisfaction', 'Cloud catching up'],
        marketShare: '18%',
        keyProducts: ['Oracle Database', 'Oracle Cloud', 'NetSuite', 'Java'],
        recentProjects: ['Multi-cloud partnerships', 'Oracle MySQL HeatWave', 'Healthcare cloud'],
        customerBase: 'Large enterprises',
        pricingModel: 'Licensing and subscription',
        marketingApproach: ['Direct sales', 'Partner network', 'Industry events', 'Executive programs']
      }
    ],
    'restaurant': [
      {
        name: "McDonald's Corporation",
        location: 'United States',
        foundedYear: 1955,
        annualRevenue: 23000,
        employeeCount: '200K+',
        strengths: ['Global brand', 'Real estate portfolio', 'Franchise model', 'Supply chain'],
        weaknesses: ['Health concerns', 'Labor costs', 'Market saturation'],
        marketShare: '19%',
        keyProducts: ['Big Mac', 'McNuggets', 'Breakfast menu', 'McCafe'],
        recentProjects: ['Digital kiosks', 'Mobile ordering app', 'Delivery partnerships', 'Menu innovation'],
        customerBase: 'Mass market',
        pricingModel: 'Value pricing',
        marketingApproach: ['TV advertising', 'Mobile app', 'Sponsorships', 'Local marketing']
      },
      {
        name: 'Starbucks Corporation',
        location: 'United States',
        foundedYear: 1971,
        annualRevenue: 32000,
        employeeCount: '402K+',
        strengths: ['Brand loyalty', 'Premium positioning', 'Mobile payment', 'Store experience'],
        weaknesses: ['Higher prices', 'Union pressure', 'Market saturation'],
        marketShare: '38%',
        keyProducts: ['Coffee beverages', 'Food items', 'Packaged coffee', 'Merchandise'],
        recentProjects: ['Starbucks Rewards enhancement', 'Drive-thru expansion', 'Sustainability initiatives'],
        customerBase: 'Urban professionals and millennials',
        pricingModel: 'Premium pricing',
        marketingApproach: ['Mobile app', 'Social media', 'Loyalty program', 'Limited-time offers']
      },
      {
        name: 'Chipotle Mexican Grill',
        location: 'United States',
        foundedYear: 1993,
        annualRevenue: 9000,
        employeeCount: '110K+',
        strengths: ['Fresh ingredients', 'Fast casual model', 'Digital ordering', 'Brand perception'],
        weaknesses: ['Food safety history', 'Limited menu', 'Higher costs'],
        marketShare: '7%',
        keyProducts: ['Burritos', 'Bowls', 'Tacos', 'Quesadillas'],
        recentProjects: ['Chipotlanes (drive-thru)', 'Digital kitchen expansion', 'Sustainability programs'],
        customerBase: 'Young professionals and families',
        pricingModel: 'Premium fast casual',
        marketingApproach: ['Social media', 'Digital marketing', 'Influencer partnerships', 'Loyalty program']
      }
    ],
    'ecommerce': [
      {
        name: 'Amazon.com Inc.',
        location: 'United States',
        foundedYear: 1994,
        annualRevenue: 574000,
        employeeCount: '1.5M+',
        strengths: ['Market dominance', 'Prime ecosystem', 'AWS profits', 'Logistics network'],
        weaknesses: ['Regulatory pressure', 'Labor relations', 'Profitability of retail'],
        marketShare: '38%',
        keyProducts: ['E-commerce marketplace', 'Prime membership', 'AWS', 'Alexa', 'Kindle'],
        recentProjects: ['Amazon One palm payment', 'Amazon Pharmacy expansion', 'Climate Pledge'],
        customerBase: 'Mass market consumers',
        pricingModel: 'Dynamic pricing',
        marketingApproach: ['Prime Video', 'Sponsored products', 'Email marketing', 'Voice shopping']
      },
      {
        name: 'eBay Inc.',
        location: 'United States',
        foundedYear: 1995,
        annualRevenue: 10000,
        employeeCount: '11K+',
        strengths: ['Marketplace model', 'Collectibles expertise', 'Global reach', 'Managed payments'],
        weaknesses: ['Amazon competition', 'User experience', 'Growth slowdown'],
        marketShare: '4%',
        keyProducts: ['Auction marketplace', 'Buy It Now', 'Classified ads', 'Motors'],
        recentProjects: ['Authentication services', 'NFT marketplace', 'Recommerce initiatives'],
        customerBase: 'Value shoppers and collectors',
        pricingModel: 'Commission-based',
        marketingApproach: ['SEO', 'Email marketing', 'Seller tools', 'Category-specific campaigns']
      },
      {
        name: 'Shopify Inc.',
        location: 'Canada (serves US market)',
        foundedYear: 2006,
        annualRevenue: 7000,
        employeeCount: '11K+',
        strengths: ['SMB focus', 'Platform ecosystem', 'Easy setup', 'Multi-channel'],
        weaknesses: ['Enterprise limitations', 'Transaction fees', 'Competition'],
        marketShare: '29% (of US e-commerce platform market)',
        keyProducts: ['E-commerce platform', 'Shopify Payments', 'POS', 'Fulfillment network'],
        recentProjects: ['Shop app enhancement', 'Shopify Markets', 'B2B commerce'],
        customerBase: 'SMB and direct-to-consumer brands',
        pricingModel: 'Tiered subscription + transaction fees',
        marketingApproach: ['Content marketing', 'Partner ecosystem', 'Education programs', 'Events']
      }
    ],
    'healthcare': [
      {
        name: 'UnitedHealth Group',
        location: 'United States',
        foundedYear: 1977,
        annualRevenue: 324000,
        employeeCount: '440K+',
        strengths: ['Vertical integration', 'Scale', 'Data analytics', 'Optum services'],
        weaknesses: ['Regulatory challenges', 'Complexity', 'Customer satisfaction'],
        marketShare: '15%',
        keyProducts: ['Health insurance', 'Pharmacy benefits', 'Healthcare services', 'Technology solutions'],
        recentProjects: ['Value-based care expansion', 'AI diagnostics', 'Telehealth integration'],
        customerBase: 'Employers and individuals',
        pricingModel: 'Premium-based with cost-sharing',
        marketingApproach: ['B2B sales', 'Broker relationships', 'Digital advertising', 'Healthcare events']
      },
      {
        name: 'CVS Health',
        location: 'United States',
        foundedYear: 1963,
        annualRevenue: 322000,
        employeeCount: '300K+',
        strengths: ['Retail pharmacy network', 'Aetna integration', 'MinuteClinic', 'PBM business'],
        weaknesses: ['Amazon threat', 'Reimbursement pressure', 'Integration challenges'],
        marketShare: '24% (pharmacy)',
        keyProducts: ['Pharmacy services', 'Health insurance (Aetna)', 'Retail health', 'PBM services'],
        recentProjects: ['HealthHUB stores', 'Primary care expansion', 'Digital health tools'],
        customerBase: 'Consumers and employers',
        pricingModel: 'Fee-for-service and insurance premiums',
        marketingApproach: ['Store promotions', 'Digital marketing', 'Loyalty program', 'Healthcare partnerships']
      },
      {
        name: 'Kaiser Permanente',
        location: 'United States',
        foundedYear: 1945,
        annualRevenue: 95000,
        employeeCount: '305K+',
        strengths: ['Integrated model', 'Quality care', 'Technology adoption', 'Member satisfaction'],
        weaknesses: ['Regional limitations', 'Narrow networks', 'Cost structure'],
        marketShare: '8%',
        keyProducts: ['Health insurance', 'Hospital care', 'Physician services', 'Wellness programs'],
        recentProjects: ['Telehealth expansion', 'Mental health services', 'Risant Health venture'],
        customerBase: 'Individuals and employer groups',
        pricingModel: 'Prepaid integrated care',
        marketingApproach: ['Community engagement', 'Digital marketing', 'Employer partnerships', 'Member referrals']
      }
    ]
  },
  'united-kingdom': {
    'manufacturing': [
      {
        name: 'Rolls-Royce Holdings',
        location: 'United Kingdom',
        foundedYear: 1971,
        annualRevenue: 16500,
        employeeCount: '42K+',
        strengths: ['Trent engine family leadership', 'Long-term engine service agreements (40% of revenue)', 'Defense nuclear submarines', 'SMR nuclear potential'],
        weaknesses: ['COVID recovery still ongoing', 'Boeing/Airbus production delays impact', 'High R&D costs for next-gen engines'],
        marketShare: '28%',
        keyProducts: ['Trent XWB (A350)', 'Trent 7000 (A330neo)', 'Pearl 15 (business jets)', 'MT30 naval gas turbines', 'Defense products'],
        recentProjects: ['UltraFan demonstrator', 'Small Modular Reactor (SMR) program', 'Hydrogen combustion testing', 'Power Systems growth'],
        customerBase: 'Commercial airlines, defense ministries, business aviation, marine/energy',
        pricingModel: 'Aircraft engine sales + TotalCare long-term service agreements (per flying hour)',
        marketingApproach: ['OEM and airline direct relationships', 'Government defense contracts', 'Innovation showcases at Farnborough']
      },
      {
        name: 'BAE Systems',
        location: 'United Kingdom',
        foundedYear: 1999,
        annualRevenue: 27000,
        employeeCount: '105K+',
        strengths: ['Typhoon/F-35 program', 'Nuclear submarine manufacturing', 'US defense integration', 'Electronic systems expertise'],
        weaknesses: ['Government contract dependency', 'Long-cycle development programs', 'Export control limitations'],
        marketShare: '35%',
        keyProducts: ['Eurofighter Typhoon', 'F-35 components', 'Type 26 frigates', 'M88 engine work', 'Combat systems'],
        recentProjects: ['GCAP next-gen fighter (UK-Japan-Italy)', 'Type 31 frigate production', 'US Army combat vehicle', 'Cyber & Intelligence division growth'],
        customerBase: 'UK MoD, US DoD, Saudi Arabia, Australia, international defense ministries',
        pricingModel: 'Government fixed-price and cost-plus defense contracts',
        marketingApproach: ['Government relations', 'International defense exhibitions (DSEI)', 'Export credit agency partnerships']
      },
      {
        name: 'Unilever',
        location: 'United Kingdom',
        foundedYear: 1929,
        annualRevenue: 61800,
        employeeCount: '148K+',
        strengths: ['Prestige brand portfolio (Dove, Hellmann\'s, Knorr, Lynx)', 'Emerging market penetration', 'Sustainability leadership', 'Distribution network'],
        weaknesses: ['Portfolio complexity', 'Ice cream spinoff disruption', 'Margin pressure from discounters'],
        marketShare: '8%',
        keyProducts: ['Dove soap/skincare', 'Knorr food products', 'Hellmann\'s mayonnaise', 'Domestos', 'Magnum ice cream (being spun off)'],
        recentProjects: ['Ice cream business spin-off (Magnum, Ben & Jerry\'s)', 'Beauty & Wellbeing division growth', 'Prestige brands acquisitions', 'AI in marketing'],
        customerBase: 'Global consumers across 190+ countries',
        pricingModel: 'Mass-market to premium tiered product range',
        marketingApproach: ['Global brand management', 'Retail partnerships', 'Digital & social media', 'Influencer marketing']
      },
      {
        name: 'GKN Aerospace / Melrose Industries',
        location: 'United Kingdom',
        foundedYear: 2012,
        annualRevenue: 3400,
        employeeCount: '15K+',
        strengths: ['Aerostructures expertise (wing skins)', 'Engine systems capabilities', 'Long-term OEM contracts', 'Defense aftermarket'],
        weaknesses: ['Aerospace recovery exposure', 'Capital intensity', 'Brexit supply chain complexity'],
        marketShare: '12%',
        keyProducts: ['Composite aerostructures', 'Engine air systems', 'Nacelles', 'A350 wings', 'Boeing 787 components'],
        recentProjects: ['Sustainable aviation technology', 'A320 family production ramp', 'Defense refit programs', 'Electrification of aircraft systems'],
        customerBase: 'Airbus, Boeing, Safran, GE Aerospace, Rolls-Royce, defense primes',
        pricingModel: 'Long-term OEM supply contracts with escalation clauses',
        marketingApproach: ['OEM relationship management', 'Farnborough Airshow presence', 'Technical capability demonstrations']
      },
      {
        name: 'Smiths Group',
        location: 'United Kingdom',
        foundedYear: 1851,
        annualRevenue: 3200,
        employeeCount: '12K+',
        strengths: ['Detection technology leadership (airports)', 'Medical devices (Smiths Medical sold)', 'Interconnects for defense', 'Strong aftermarket'],
        weaknesses: ['Portfolio restructuring ongoing', 'Revenue concentration in detection', 'M&A integration risk'],
        marketShare: '14%',
        keyProducts: ['Ionscan explosives detection', 'Morpho Detection (airports)', 'Interconnect solutions', 'Flex-Tek tubing systems'],
        recentProjects: ['AI-enhanced detection systems', 'Space & defense interconnects', 'Industrial flex-tek growth', 'Digital service platforms'],
        customerBase: 'Airport operators, governments, defense contractors, industrial manufacturers',
        pricingModel: 'Equipment sales + service contracts + consumables',
        marketingApproach: ['Government procurement relationships', 'Trade shows (ISNR, Milipol)', 'OEM channel partnerships']
      }
    ],
    'retail': [
      {
        name: 'Tesco PLC',
        location: 'United Kingdom',
        foundedYear: 1919,
        annualRevenue: 73000,
        employeeCount: '340K+',
        strengths: ['Market leadership', 'Clubcard data', 'Multi-format stores', 'Online grocery'],
        weaknesses: ['Margin pressure', 'Discount competition', 'International retreat'],
        marketShare: '27%',
        keyProducts: ['Groceries', 'General merchandise', 'Financial services', 'Mobile services'],
        recentProjects: ['Tesco Express expansion', 'Clubcard Plus', 'Sustainability initiatives'],
        customerBase: 'UK mass market',
        pricingModel: 'Competitive with promotions',
        marketingApproach: ['Clubcard personalization', 'TV advertising', 'Digital marketing', 'Local campaigns']
      },
      {
        name: 'Sainsbury\'s',
        location: 'United Kingdom',
        foundedYear: 1869,
        annualRevenue: 34000,
        employeeCount: '189K+',
        strengths: ['Quality perception', 'Argos integration', 'Nectar loyalty', 'Convenience stores'],
        weaknesses: ['Higher prices', 'Market share decline', 'Profitability pressure'],
        marketShare: '15%',
        keyProducts: ['Quality groceries', 'General merchandise (Argos)', 'Habitat homeware', 'Tu clothing'],
        recentProjects: ['Store transformation', 'Online fulfillment centers', 'Nectar 360 data'],
        customerBase: 'Middle-class UK consumers',
        pricingModel: 'Quality-focused competitive',
        marketingApproach: ['Nectar partnership', 'Seasonal campaigns', 'Digital advertising', 'Jamie Oliver partnership']
      },
      {
        name: 'Marks & Spencer',
        location: 'United Kingdom',
        foundedYear: 1884,
        annualRevenue: 13000,
        employeeCount: '65K+',
        strengths: ['Brand heritage', 'Food quality', 'Percy Pig brand', 'Clothing reputation'],
        weaknesses: ['Premium pricing', 'Turnaround challenges', 'Store estate'],
        marketShare: '5%',
        keyProducts: ['Premium food', 'Clothing & home', 'M&S Collection', 'Plan A sustainability'],
        recentProjects: ['Store rotation program', 'Ocado partnership', 'Digital transformation'],
        customerBase: 'Affluent UK shoppers',
        pricingModel: 'Premium positioning',
        marketingApproach: ['TV campaigns', 'Social media', 'In-store experience', 'Quality messaging']
      }
    ],
    'technology': [
      {
        name: 'ARM Holdings',
        location: 'United Kingdom',
        foundedYear: 1990,
        annualRevenue: 3000,
        employeeCount: '6K+',
        strengths: ['IP licensing model', 'Mobile dominance', 'Energy efficiency', 'IoT growth'],
        weaknesses: ['China market risk', 'Revenue concentration', 'Competition'],
        marketShare: '95% (mobile processors)',
        keyProducts: ['Cortex processors', 'Mali GPUs', 'IP licensing', 'Design services'],
        recentProjects: ['Armv9 architecture', 'Total Design ecosystem', 'AI computing solutions'],
        customerBase: 'Technology companies globally',
        pricingModel: 'Licensing and royalties',
        marketingApproach: ['Technical conferences', 'Partner ecosystem', 'Developer relations', 'Industry events']
      },
      {
        name: 'Sage Group',
        location: 'United Kingdom',
        foundedYear: 1981,
        annualRevenue: 2500,
        employeeCount: '11K+',
        strengths: ['SMB focus', 'Accounting expertise', 'Cloud transition', 'Partner network'],
        weaknesses: ['Large enterprise penetration', 'Cloud migration pace', 'Competition'],
        marketShare: '7%',
        keyProducts: ['Sage Business Cloud', 'Sage 50', 'Sage Intacct', 'Sage Payroll'],
        recentProjects: ['AI-powered features', 'SageOne enhancements', 'Partner ecosystem'],
        customerBase: 'Small and medium businesses',
        pricingModel: 'Subscription-based',
        marketingApproach: ['Partner channel', 'Content marketing', 'Accountant partnerships', 'SMB events']
      },
      {
        name: 'Darktrace',
        location: 'United Kingdom',
        foundedYear: 2013,
        annualRevenue: 500,
        employeeCount: '2K+',
        strengths: ['AI innovation', 'Autonomous response', 'Enterprise adoption', 'Growth rate'],
        weaknesses: ['Profitability', 'Market education', 'Competition increasing'],
        marketShare: '3%',
        keyProducts: ['Enterprise Immune System', 'Antigena', 'Darktrace Cloud', 'Industrial protection'],
        recentProjects: ['PREVENT platform', 'Supply chain security', 'AI analyst features'],
        customerBase: 'Enterprises globally',
        pricingModel: 'Annual contracts',
        marketingApproach: ['Direct sales', 'Industry events', 'Thought leadership', 'Case studies']
      }
    ]
  },
  'canada': {
    'manufacturing': [
      {
        name: 'Bombardier Inc.',
        location: 'Canada',
        foundedYear: 1942,
        annualRevenue: 8100,
        employeeCount: '16K+',
        strengths: ['Business jet market (Challenger, Global series)', 'Strong aftermarket revenue', 'Defence track record', 'Transformation success post-rail divestiture'],
        weaknesses: ['Narrow product focus post-restructuring', 'Competition from Gulfstream (GD) and Dassault', 'Large debt burden'],
        marketShare: '18%',
        keyProducts: ['Global 7500 business jet', 'Challenger 350/650', 'Learjet legacy (production ended)', 'Defence services'],
        recentProjects: ['Global 8000 ultra-long-range jet', 'Aftermarket service network expansion', 'Sustainable aviation fuel certification', 'Defence MRO programs'],
        customerBase: 'Ultra-high-net-worth individuals, corporations, charter operators, governments',
        pricingModel: 'Premium aircraft pricing ($32-75M per aircraft) + long-term service plans',
        marketingApproach: ['NBAA Business Aviation Convention', 'Private client relationships', 'Completions center showcase', 'Fractional ownership partnerships']
      },
      {
        name: 'Magna International',
        location: 'Canada',
        foundedYear: 1957,
        annualRevenue: 42800,
        employeeCount: '172K+',
        strengths: ['World\'s largest auto parts maker', 'Complete vehicle manufacturing (Steyr)', 'Seating, vision, power & vision systems', 'EV systems growth'],
        weaknesses: ['Auto production cycle dependency', 'Customer concentration (GM, Ford, Stellantis)', 'EV transition uncertainty'],
        marketShare: '6%',
        keyProducts: ['Door systems', 'Seating systems (MARADA)', 'Exterior mirrors/cameras', 'eDrive EV motors', 'Complete vehicle assembly (BMW Z4, Jaguar I-Pace)'],
        recentProjects: ['EV architecture systems', 'Fisker Ocean manufacturing', 'LG Magna EV powertrain JV', 'Smart mirror/camera systems'],
        customerBase: 'All major global OEMs (Ford, GM, BMW, VW, Toyota, Mercedes)',
        pricingModel: 'OEM multi-year supply contracts with annual cost-down requirements',
        marketingApproach: ['OEM relationship management', 'NAIAS/IAA automotive shows', 'Technical capability presentations', 'EV solution marketing']
      },
      {
        name: 'Canfor Corporation',
        location: 'Canada',
        foundedYear: 1938,
        annualRevenue: 5200,
        employeeCount: '6K+',
        strengths: ['Largest Canadian lumber producer', 'US housing market exposure', 'Sustainable forestry certification', 'Engineering wood products'],
        weaknesses: ['US softwood lumber tariffs (15%)', 'Housing market cyclicality', 'Wildfire and climate risk to timber supply', 'Energy costs'],
        marketShare: '8%',
        keyProducts: ['Softwood lumber (SPF)', 'Engineered wood products', 'Pulp/paper (through partnerships)', 'Wood pellets'],
        recentProjects: ['Mass timber expansion', 'Carbon credit forest management', 'US mill investments', 'Sustainable wood building advocacy'],
        customerBase: 'US homebuilders, retail lumber yards, industrial manufacturers, export markets',
        pricingModel: 'Commodity Random Length pricing + value-added product premium',
        marketingApproach: ['Homebuilder relationships', 'Building codes advocacy', 'Sustainability certifications (FSC)', 'Distributor network']
      }
    ],
    'retail': [
      {
        name: 'Loblaw Companies Limited',
        location: 'Canada',
        foundedYear: 1956,
        annualRevenue: 39000,
        employeeCount: '200K+',
        strengths: ['Market leadership', 'PC Optimum', 'Pharmacy integration', 'Private label'],
        weaknesses: ['Digital catching up', 'Competition', 'Price perception'],
        marketShare: '29%',
        keyProducts: ['Groceries', 'President\'s Choice', 'Shoppers Drug Mart', 'Joe Fresh'],
        recentProjects: ['PC Express expansion', 'Store renovations', 'Sustainability programs'],
        customerBase: 'Canadian mass market',
        pricingModel: 'Competitive with premium private label',
        marketingApproach: ['PC Optimum personalization', 'TV advertising', 'Flyer', 'Digital campaigns']
      },
      {
        name: 'Canadian Tire Corporation',
        location: 'Canada',
        foundedYear: 1922,
        annualRevenue: 12000,
        employeeCount: '100K+',
        strengths: ['Brand loyalty', 'Triangle rewards', 'Multi-banner', 'Automotive expertise'],
        weaknesses: ['Amazon competition', 'Store format aging', 'Digital experience'],
        marketShare: '8%',
        keyProducts: ['Automotive', 'Hardware', 'Sports (Sport Chek)', 'Mark\'s apparel'],
        recentProjects: ['Store modernization', 'E-commerce enhancement', 'Triangle financial services'],
        customerBase: 'Canadian families',
        pricingModel: 'Promotional pricing',
        marketingApproach: ['Canadian Tire Money', 'Seasonal campaigns', 'Flyer marketing', 'Sponsorships']
      }
    ],
    'technology': [
      {
        name: 'Shopify Inc.',
        location: 'Canada',
        foundedYear: 2006,
        annualRevenue: 7000,
        employeeCount: '11K+',
        strengths: ['Platform ecosystem', 'Merchant focus', 'Innovation pace', 'Global reach'],
        weaknesses: ['Profitability volatility', 'Competition', 'SMB churn'],
        marketShare: '29%',
        keyProducts: ['Commerce platform', 'Shopify Payments', 'Point of Sale', 'Fulfillment'],
        recentProjects: ['Shopify Editions', 'B2B commerce', 'Markets expansion'],
        customerBase: 'Entrepreneurs and SMBs globally',
        pricingModel: 'Tiered subscription',
        marketingApproach: ['Content marketing', 'Partner ecosystem', 'Shopify Unite', 'Education']
      },
      {
        name: 'OpenText Corporation',
        location: 'Canada',
        foundedYear: 1991,
        annualRevenue: 4600,
        employeeCount: '25K+',
        strengths: ['Enterprise content management', 'Security solutions', 'Acquisitions', 'Customer base'],
        weaknesses: ['Cloud transition', 'Integration complexity', 'Market perception'],
        marketShare: '12%',
        keyProducts: ['OpenText Cloud', 'Content Server', 'Cybersecurity', 'Business Network'],
        recentProjects: ['Cloud Editions 23.4', 'AI enhancements', 'Micro Focus integration'],
        customerBase: 'Large enterprises',
        pricingModel: 'Licensing and subscription',
        marketingApproach: ['Enterprise sales', 'Partner channel', 'Industry conferences', 'Thought leadership']
      }
    ]
  },
  'germany': {
    'manufacturing': [
      {
        name: 'Siemens AG',
        location: 'Germany',
        foundedYear: 1847,
        annualRevenue: 88000,
        employeeCount: '311K+',
        strengths: ['Industrial automation leadership', 'Digitalization (Siemens Xcelerator)', 'Energy transition expertise', 'Global service network'],
        weaknesses: ['Complexity of portfolio', 'Cyclical industrial markets', 'Software transition costs'],
        marketShare: '22%',
        keyProducts: ['SIMATIC PLCs', 'Sinumerik CNC', 'Xcelerator digital platform', 'Smart infrastructure', 'Gas turbines'],
        recentProjects: ['Xcelerator digital business platform', 'Smart infrastructure expansion', 'Low-carbon energy systems', 'Rail automation'],
        customerBase: 'Industrial manufacturers, utilities, infrastructure operators globally',
        pricingModel: 'Enterprise licensing + long-term service contracts',
        marketingApproach: ['Direct enterprise sales', 'System integrator partnerships', 'Hannover Messe presence', 'Digital twin showcases']
      },
      {
        name: 'BASF SE',
        location: 'Germany',
        foundedYear: 1865,
        annualRevenue: 87000,
        employeeCount: '111K+',
        strengths: ['World\'s largest chemical company', 'Verbund production synergies', 'Agricultural chemicals growth', 'Battery materials R&D'],
        weaknesses: ['High energy cost exposure (Germany energy crisis)', 'Restructuring costs', 'Chinese competition in commodities'],
        marketShare: '8%',
        keyProducts: ['Performance chemicals', 'Functional materials', 'Agricultural solutions', 'Battery materials', 'Specialty plastics'],
        recentProjects: ['Ludwigshafen restructuring (€1.1B savings)', 'Battery materials expansion (Schwarzheide)', 'China growth strategy (Zhanjiang)'],
        customerBase: 'Automotive, agriculture, construction, electronics, pharma customers',
        pricingModel: 'Contract pricing + spot market + value-based specialty chemicals',
        marketingApproach: ['Direct long-term contracts with major customers', 'Technical service teams', 'Industry conferences', 'Sustainability branding']
      },
      {
        name: 'Robert Bosch GmbH',
        location: 'Germany',
        foundedYear: 1886,
        annualRevenue: 91600,
        employeeCount: '428K+',
        strengths: ['Technology breadth (auto + industrial + home)', 'R&D investment (7% of revenue)', 'Bosch Foundation ownership structure', 'Semiconductor strategy'],
        weaknesses: ['Automotive ICE transition risk', 'Complex restructuring ongoing', 'Competition from Chinese auto suppliers'],
        marketShare: '12%',
        keyProducts: ['Automotive components', 'Power tools (Milwaukee parent)', 'Industrial sensors', 'Home appliances', 'Semiconductors'],
        recentProjects: ['EV powertrain components', 'Hydrogen technology', 'AI-powered manufacturing', 'Smart home expansion'],
        customerBase: 'Automotive OEMs, industrial manufacturers, consumers, construction',
        pricingModel: 'OEM contracts + premium consumer pricing + B2B industrial contracts',
        marketingApproach: ['OEM direct sales teams', 'Trade distribution', 'Digital commerce', 'Innovation showcases']
      },
      {
        name: 'Thyssenkrupp AG',
        location: 'Germany',
        foundedYear: 1811,
        annualRevenue: 37500,
        employeeCount: '101K+',
        strengths: ['Steel production scale', 'Automotive components leadership', 'Elevator technology (sold to Advent)', 'Green steel hydrogen leadership'],
        weaknesses: ['Steel overcapacity globally', 'High-cost European energy', 'Ongoing restructuring pain', 'Debt burden'],
        marketShare: '7%',
        keyProducts: ['Steel flat products', 'Automotive body parts', 'Marine systems', 'Industrial solutions', 'Spring/stabilizer systems'],
        recentProjects: ['thyssenkrupp nucera green hydrogen electrolyzers', 'tkH2Steel decarbonization', 'Automotive components restructuring', 'Steel Europe transformation'],
        customerBase: 'Automotive OEMs, shipbuilders, construction, energy companies',
        pricingModel: 'Commodity steel index pricing + specialty premium contracts',
        marketingApproach: ['Direct account management', 'Industry trade shows (EuroBLECH)', 'Technical service', 'Sustainability positioning']
      },
      {
        name: 'Heidelberg Materials',
        location: 'Germany',
        foundedYear: 1873,
        annualRevenue: 21200,
        employeeCount: '51K+',
        strengths: ['Global cement market position (#2)', 'Geographic diversification', 'Circular economy leadership', 'Low-carbon cement innovation'],
        weaknesses: ['Capital intensive', 'Carbon exposure (cement = 8% of CO2)', 'Cyclical construction demand', 'Pricing pressure'],
        marketShare: '9%',
        keyProducts: ['Cement', 'Ready-mixed concrete', 'Aggregates', 'Asphalt', 'Building products'],
        recentProjects: ['CCUS carbon capture plant (Brevik, Norway)', 'EcoLabel low-carbon cement', 'African growth expansion', 'Recycled material integration'],
        customerBase: 'Construction companies, civil engineering contractors, governments',
        pricingModel: 'Commodity pricing with regional premiums for specialty products',
        marketingApproach: ['Local sales teams', 'Contractor relationships', 'Sustainability certifications', 'Regional pricing strategies']
      }
    ],
    'retail': [
      {
        name: 'Lidl',
        location: 'Germany',
        foundedYear: 1973,
        annualRevenue: 125000,
        employeeCount: '400K+',
        strengths: ['Discount model', 'Private label quality', 'European expansion', 'Efficiency'],
        weaknesses: ['Limited product range', 'Warehouse format', 'Online presence'],
        marketShare: '11% (Germany)',
        keyProducts: ['Discount groceries', 'Weekly specials', 'Organic range', 'Non-food items'],
        recentProjects: ['Store modernization', 'Digital expansion', 'Sustainability initiatives'],
        customerBase: 'Value-conscious European consumers',
        pricingModel: 'Hard discount',
        marketingApproach: ['Weekly flyers', 'Limited-time offers', 'Quality messaging', 'Social media']
      },
      {
        name: 'Aldi',
        location: 'Germany',
        foundedYear: 1946,
        annualRevenue: 133000,
        employeeCount: '200K+',
        strengths: ['Extreme efficiency', 'Private label dominance', 'Global footprint', 'Simplicity'],
        weaknesses: ['Brand selection', 'Store experience', 'Digital lagging'],
        marketShare: '15% (Germany)',
        keyProducts: ['Discount groceries', 'Weekly specials', 'Specialty buys', 'Organic products'],
        recentProjects: ['Checkout-free stores pilot', 'Online delivery expansion', 'Store refreshes'],
        customerBase: 'Budget-conscious consumers worldwide',
        pricingModel: 'Hard discount leader',
        marketingApproach: ['Value messaging', 'Quality claims', 'Limited promotions', 'Word of mouth']
      }
    ],
    'automotive': [
      {
        name: 'Volkswagen Group',
        location: 'Germany',
        foundedYear: 1937,
        annualRevenue: 295000,
        employeeCount: '675K+',
        strengths: ['Brand portfolio', 'Global scale', 'EV investment', 'Engineering expertise'],
        weaknesses: ['Dieselgate legacy', 'Software challenges', 'Complexity'],
        marketShare: '13% (global)',
        keyProducts: ['VW cars', 'Audi', 'Porsche', 'Electric vehicles (ID series)'],
        recentProjects: ['ID. Buzz', 'Battery gigafactories', 'Software 2.0', 'Trinity project'],
        customerBase: 'Global consumers',
        pricingModel: 'Tiered by brand',
        marketingApproach: ['Brand differentiation', 'Sponsorships', 'Digital marketing', 'Dealership network']
      },
      {
        name: 'BMW Group',
        location: 'Germany',
        foundedYear: 1916,
        annualRevenue: 155000,
        employeeCount: '150K+',
        strengths: ['Premium brand', 'Driving dynamics', 'EV leadership', 'Profitability'],
        weaknesses: ['Price premium', 'Market share pressure', 'Complexity'],
        marketShare: '2.5% (global)',
        keyProducts: ['BMW cars', 'MINI', 'Rolls-Royce', 'iX electric SUV'],
        recentProjects: ['Neue Klasse EV platform', 'Circular economy', 'Autonomous driving'],
        customerBase: 'Premium global customers',
        pricingModel: 'Premium pricing',
        marketingApproach: ['Ultimate Driving Machine', 'Digital experience', 'Sponsorships', 'Dealer network']
      },
      {
        name: 'Mercedes-Benz Group',
        location: 'Germany',
        foundedYear: 1926,
        annualRevenue: 155000,
        employeeCount: '175K+',
        strengths: ['Luxury positioning', 'Innovation', 'EQ electric brand', 'Profitability focus'],
        weaknesses: ['Cost structure', 'Software delays', 'China dependence'],
        marketShare: '2.4% (global)',
        keyProducts: ['Mercedes-Benz cars', 'AMG performance', 'EQ electric', 'Vans'],
        recentProjects: ['Vision EQXX efficiency', 'MB.OS operating system', 'Luxury focus'],
        customerBase: 'Luxury car buyers',
        pricingModel: 'Premium/luxury pricing',
        marketingApproach: ['Luxury lifestyle', 'Experience centers', 'Digital innovation', 'Sponsorships']
      }
    ]
  },
  'australia': {
    'manufacturing': [
      {
        name: 'BlueScope Steel',
        location: 'Australia',
        foundedYear: 2002,
        annualRevenue: 14000,
        employeeCount: '16K+',
        strengths: ['Australian steel market dominance', 'COLORBOND brand strength', 'North Star US operations', 'Construction products'],
        weaknesses: ['Energy cost sensitivity', 'Chinese import competition', 'Port Kembla carbon exposure'],
        marketShare: '48%',
        keyProducts: ['COLORBOND roofing/cladding', 'ZINCALUME steel', 'Structural steel', 'North Star Hot Rolled Coil (US)', 'Metalcorp distribution'],
        recentProjects: ['Electric arc furnace transition planning', 'COLORBOND next-generation', 'US North Star expansion', 'Hydrogen steel research'],
        customerBase: 'Construction, manufacturing, agriculture, transport companies',
        pricingModel: 'Commodity steel pricing + premium for branded products',
        marketingApproach: ['Brand-building for COLORBOND', 'Distributor network', 'Trade shows', 'Sustainability positioning']
      },
      {
        name: 'Ansell Limited',
        location: 'Australia',
        foundedYear: 1905,
        annualRevenue: 1500,
        employeeCount: '14K+',
        strengths: ['Global PPE leadership', 'Healthcare and industrial gloves dominance', 'Brand portfolio breadth', 'Regulatory expertise'],
        weaknesses: ['Post-COVID demand normalization', 'Raw material (nitrile, latex) costs', 'Competition from Asian manufacturers'],
        marketShare: '22%',
        keyProducts: ['GAMMEX surgical gloves', 'AlphaTec chemical protection', 'HyFlex mechanical gloves', 'SKYN condoms', 'Microflex lab gloves'],
        recentProjects: ['Digitalization of glove manufacturing', 'Emerging markets expansion', 'ESG certification programs', 'Healthcare portfolio focus'],
        customerBase: 'Hospitals, industrial manufacturers, food processing, laboratories',
        pricingModel: 'Premium pricing for safety-critical products',
        marketingApproach: ['Healthcare distributor relationships', 'Industrial safety partners', 'Regulatory compliance positioning', 'Trade exhibitions']
      },
      {
        name: 'Amcor PLC',
        location: 'Australia',
        foundedYear: 1860,
        annualRevenue: 14000,
        employeeCount: '41K+',
        strengths: ['Global packaging leadership', 'Flexible and rigid plastics breadth', 'Sustainability innovation', 'Customer stickiness (multi-year contracts)'],
        weaknesses: ['Polymer raw material exposure', 'Plastic sustainability pressure', 'Mature market growth'],
        marketShare: '15%',
        keyProducts: ['Flexible food packaging', 'Pharmaceutical blister packs', 'Rigid containers', 'Healthcare packaging', 'AmFiber sustainable packaging'],
        recentProjects: ['AmFiber paper-based packaging', 'rPET recycled content packaging', 'Berry Global acquisition integration', 'Circular economy commitments'],
        customerBase: 'Global food & beverage companies, pharmaceutical manufacturers, consumer goods',
        pricingModel: 'Long-term supply contracts with raw material pass-through clauses',
        marketingApproach: ['Customer co-development partnerships', 'Sustainability credentials', 'Trade conferences (Interpack)', 'Direct key account management']
      }
    ],
    'retail': [
      {
        name: 'Woolworths Group',
        location: 'Australia',
        foundedYear: 1924,
        annualRevenue: 43000,
        employeeCount: '180K+',
        strengths: ['Market leadership', 'Everyday Rewards', 'Fresh food focus', 'Supply chain'],
        weaknesses: ['Regulatory pressure', 'Price perception', 'Competition'],
        marketShare: '37%',
        keyProducts: ['Groceries', 'Fresh produce', 'Big W department store', 'Liquor (BWS, Dan Murphy\'s)'],
        recentProjects: ['Automated distribution centers', 'Metro format', 'Sustainability programs'],
        customerBase: 'Australian mass market',
        pricingModel: 'Competitive with quality focus',
        marketingApproach: ['Everyday Rewards', 'TV advertising', 'Catalogs', 'Digital campaigns']
      },
      {
        name: 'Coles Group',
        location: 'Australia',
        foundedYear: 1914,
        annualRevenue: 31000,
        employeeCount: '120K+',
        strengths: ['Flybuys loyalty', 'Private label', 'Convenience', 'Value perception'],
        weaknesses: ['Market share #2', 'Digital experience', 'Margin pressure'],
        marketShare: '28%',
        keyProducts: ['Groceries', 'Coles Own Brand', 'Liquorland', 'Coles Express fuel'],
        recentProjects: ['Coles 360 data platform', 'Ocado partnership', 'Store refreshes'],
        customerBase: 'Australian families',
        pricingModel: 'Down down pricing',
        marketingApproach: ['Flybuys', 'Little Shop collectibles', 'TV campaigns', 'Price promotions']
      }
    ]
  },
  'japan': {
    'manufacturing': [
      {
        name: 'Toyota Motor Corporation',
        location: 'Japan',
        foundedYear: 1937,
        annualRevenue: 274000,
        employeeCount: '375K+',
        strengths: ['TPS lean manufacturing pioneer', 'World\'s largest automaker (10.5M units)', 'Hydrogen fuel cell leadership (Mirai)', 'Lexus premium profitability'],
        weaknesses: ['Hybrid over EV strategy criticism', 'Software-defined vehicle gaps', 'China market share under BYD pressure'],
        marketShare: '34%',
        keyProducts: ['Corolla', 'Camry', 'Prius hybrid', 'Land Cruiser', 'Lexus', 'Mirai fuel cell', 'Hilux'],
        recentProjects: ['bZ4X BEV platform', 'Solid-state battery 2027', 'Woven City smart city', 'Toyota Production System digital evolution'],
        customerBase: 'Global consumers, fleet operators, governments, commercial vehicle buyers',
        pricingModel: 'Retail pricing through dealer network + fleet contracts',
        marketingApproach: ['Global dealer network (170 countries)', 'Sponsorships (Olympics)', 'Digital marketing', 'Reliability/quality messaging']
      },
      {
        name: 'Sony Group Corporation',
        location: 'Japan',
        foundedYear: 1946,
        annualRevenue: 88000,
        employeeCount: '113K+',
        strengths: ['PlayStation 5 dominance', 'Sony Pictures Entertainment', 'Sensor technology leadership (50% of CMOS sensors)', 'Music (Sony Music + Columbia)'],
        weaknesses: ['Consumer electronics maturity', 'Mobile segment struggles', 'Content production costs'],
        marketShare: '18%',
        keyProducts: ['PlayStation 5', 'Sony Alpha cameras', 'CMOS image sensors', 'OLED TV (Bravia)', 'Xperia phones', 'Sony Pictures films'],
        recentProjects: ['PlayStation 5 Pro', 'Honda-Sony AFEELA EV partnership', 'Sony AI music generation', 'CMOS sensor expansion for automotive'],
        customerBase: 'Gaming consumers, professional photographers, Hollywood studios, smartphone makers',
        pricingModel: 'Premium hardware + gaming software/subscription (PS Plus)',
        marketingApproach: ['Gaming community engagement', 'E3/Tokyo Game Show presence', 'Artist partnerships (music)', 'Technology showcase events']
      },
      {
        name: 'Panasonic Holdings',
        location: 'Japan',
        foundedYear: 1918,
        annualRevenue: 63000,
        employeeCount: '233K+',
        strengths: ['Tesla battery supply (Gigafactory Nevada)', 'B2B solutions transformation', 'Supply chain software (Blue Yonder)', 'Energy storage growth'],
        weaknesses: ['Consumer electronics margin pressure', 'Slow restructuring pace', 'Chinese competition in appliances'],
        marketShare: '10%',
        keyProducts: ['EV batteries (Panasonic Energy)', 'HVAC systems (Eco Solutions)', 'Blue Yonder supply chain software', 'Automotive components', 'LUMIX cameras'],
        recentProjects: ['Kansas Gigafactory (Tesla batteries)', 'Blue Yonder AI integration', 'EV battery next-gen development', 'Entertainment systems for airlines'],
        customerBase: 'Tesla, automotive OEMs, commercial buildings, supply chain companies',
        pricingModel: 'Long-term OEM contracts + B2B solutions + consumer retail',
        marketingApproach: ['OEM relationship management', 'B2B solutions marketing', 'Digital transformation messaging', 'Trade shows (CES)']
      },
      {
        name: 'Fanuc Corporation',
        location: 'Japan',
        foundedYear: 1956,
        annualRevenue: 5800,
        employeeCount: '8K+',
        strengths: ['CNC systems dominance (70% market share)', 'Highest operating margins in automation (35%+)', 'Zero-debt balance sheet', 'Remarkable quality/reliability'],
        weaknesses: ['China revenue exposure (40%)', 'Niche market limits growth', 'Slow product cycle vs software-first rivals'],
        marketShare: '70%',
        keyProducts: ['FANUC CNC controllers', 'Industrial robots (FANUC LR Mate, M-Series)', 'ROBODRILL machining centers', 'ROBOSHOT injection molding', 'ROBOMACHINES'],
        recentProjects: ['Collaborative robot expansion (CRX series)', 'AI-enhanced machine tool intelligence', 'IIoT connectivity (MT-Connect)', 'China factory growth'],
        customerBase: 'Machine tool makers, automotive plants, electronics factories, aerospace',
        pricingModel: 'Premium component pricing with long product lifecycles',
        marketingApproach: ['Technical demonstration', 'Direct sales to machine tool builders', 'Industry 4.0 positioning', 'JIMTOF machine tool show']
      },
      {
        name: 'Mitsubishi Heavy Industries (MHI)',
        location: 'Japan',
        foundedYear: 1884,
        annualRevenue: 35000,
        employeeCount: '84K+',
        strengths: ['Aerospace & defense leader in Japan', 'Gas turbine technology', 'Energy transition positioning', 'SpaceJet lessons learned'],
        weaknesses: ['SpaceJet regional jet program cancellation ($3B loss)', 'Capital intensity', 'Defense budget dependency'],
        marketShare: '8%',
        keyProducts: ['F-35 components manufacturing', 'Gas turbines (GTCC)', 'Space launch systems (H3)', 'Naval vessels', 'Industrial machinery'],
        recentProjects: ['H3 rocket (JAXA)', 'Gas turbine export growth', 'Carbon capture systems', 'Shipbuilding efficiency modernization'],
        customerBase: 'Japan Defense Ministry, JAXA, power utilities, industrial operators',
        pricingModel: 'Government defense contracts + commercial project contracts',
        marketingApproach: ['Government relationship management', 'International aerospace shows', 'Technical capability demonstrations']
      }
    ],
    'retail': [
      {
        name: '7-Eleven Japan',
        location: 'Japan',
        foundedYear: 1973,
        annualRevenue: 50000,
        employeeCount: '150K+',
        strengths: ['Convenience dominance', 'Product innovation', 'Density strategy', 'Quality control'],
        weaknesses: ['Labor shortage', 'Franchise relations', 'Limited formats'],
        marketShare: '27% (convenience)',
        keyProducts: ['Ready-to-eat meals', 'Onigiri rice balls', 'Seven Premium', 'Services (bill pay, ATM)'],
        recentProjects: ['Cashless payment', 'Delivery partnerships', 'Smart stores'],
        customerBase: 'Japanese consumers',
        pricingModel: 'Premium convenience',
        marketingApproach: ['Product quality', 'Location density', 'Seasonal limited editions', 'In-store promotions']
      },
      {
        name: 'Fast Retailing (UNIQLO)',
        location: 'Japan',
        foundedYear: 1984,
        annualRevenue: 23000,
        employeeCount: '60K+',
        strengths: ['Tech-casual innovation', 'Global expansion', 'Efficiency', 'Brand strength'],
        weaknesses: ['China dependence', 'Competition', 'Regional challenges'],
        marketShare: '8% (apparel)',
        keyProducts: ['HEATTECH', 'AIRism', 'Ultra Light Down', 'LifeWear basics'],
        recentProjects: ['Digital transformation', 'Sustainability initiatives', 'Global flagship expansion'],
        customerBase: 'Global casual wear consumers',
        pricingModel: 'Value pricing',
        marketingApproach: ['Innovation messaging', 'Global ambassadors', 'Collaborations', 'Experience stores']
      }
    ]
  },
  'china': {
    'manufacturing': [
      {
        name: 'Foxconn (Hon Hai Precision)',
        location: 'China',
        foundedYear: 1974,
        annualRevenue: 222000,
        employeeCount: '800K+',
        strengths: ['World\'s largest EMS (Electronics Manufacturing Services)', 'Apple supply chain relationship', 'Scale and speed of execution', 'India/Vietnam diversification'],
        weaknesses: ['Apple revenue concentration (55%+)', 'Thin margins (2-3%)', 'Labor relations complexity', 'Geopolitical risk'],
        marketShare: '42%',
        keyProducts: ['iPhone assembly', 'iPad/Mac manufacturing', 'Server production', 'EV components', 'Industrial robots'],
        recentProjects: ['India iPhone manufacturing scale-up', 'EV joint ventures', 'Sharp display business', 'Semiconductor investment'],
        customerBase: 'Apple, Xiaomi, Dell, HP, Sony, Nintendo, Amazon',
        pricingModel: 'Cost-plus manufacturing contracts',
        marketingApproach: ['Strategic OEM relationship management', 'Capacity investment signals', 'Government relationship in key markets']
      },
      {
        name: 'BYD Co. Ltd',
        location: 'China',
        foundedYear: 1995,
        annualRevenue: 84000,
        employeeCount: '570K+',
        strengths: ['#1 EV manufacturer globally by volume (2023)', 'Vertical integration (batteries to vehicles)', 'Low-cost manufacturing leadership', 'Export market growth'],
        weaknesses: ['EU tariff headwinds (17-35%)', 'Western market brand recognition', 'Quality perception in premium segments', 'Geopolitical risk'],
        marketShare: '18%',
        keyProducts: ['Han sedan', 'Atto 3 EV', 'Song SUV', 'Blade Battery', 'BYD buses & trucks'],
        recentProjects: ['European market entry (Norway, UK, Germany)', 'Thailand/Brazil production plants', 'Solid-state battery R&D', 'Premium brand Yangwang'],
        customerBase: 'Chinese consumers, fleet operators, international markets, bus operators',
        pricingModel: 'Value-based pricing undercutting Western OEMs by 30-40%',
        marketingApproach: ['Direct sales channels', 'Dealership network expansion', 'Government fleet contracts', 'International auto shows']
      },
      {
        name: 'SAIC Motor',
        location: 'China',
        foundedYear: 1955,
        annualRevenue: 120000,
        employeeCount: '150K+',
        strengths: ['China\'s largest automaker', 'JV partnerships (VW-SAIC, GM-SAIC)', 'Government backing', 'Domestic brand MG (international)'],
        weaknesses: ['JV model disrupted by EV transition', 'Heavy reliance on aging ICE platforms', 'Domestic competition intensifying'],
        marketShare: '22%',
        keyProducts: ['SAIC-Volkswagen cars', 'SAIC-GM Buick/Chevrolet', 'MG cars (international)', 'Wuling mini EVs', 'ROEWE/IM EVs'],
        recentProjects: ['MG4 EV international expansion', 'Wuling global EV push', 'IM luxury EV brand', 'Smart factory transformation'],
        customerBase: 'Chinese consumers, global consumers through MG brand, fleet buyers',
        pricingModel: 'Tiered pricing from budget (Wuling) to premium (IM)',
        marketingApproach: ['Dealer network', 'JV marketing programs', 'International expansion', 'Digital marketing China']
      },
      {
        name: 'CITIC Pacific Specialty Steels',
        location: 'China',
        foundedYear: 1986,
        annualRevenue: 15000,
        employeeCount: '28K+',
        strengths: ['Specialty steel dominance in China', 'Automotive steel growing demand', 'Wind power steel supply', 'Technology upgrading'],
        weaknesses: ['Steel overcapacity pressure', 'Energy costs', 'Environmental compliance costs', 'International competition'],
        marketShare: '15%',
        keyProducts: ['Automotive specialty steel', 'Bearing steel', 'Tool steel', 'Spring steel', 'Gear steel'],
        recentProjects: ['EV-grade steel grades development', 'Wind power tower steel', 'Green manufacturing certification', 'Capacity expansion projects'],
        customerBase: 'Automotive OEMs, bearing manufacturers, tool makers, wind power companies',
        pricingModel: 'Commodity base + specialty premium pricing',
        marketingApproach: ['Direct key account management', 'Certification programs', 'Technical service teams', 'Trade show participation']
      },
      {
        name: 'Haier Smart Home',
        location: 'China',
        foundedYear: 1984,
        annualRevenue: 38000,
        employeeCount: '120K+',
        strengths: ['World\'s largest home appliance brand', 'GE Appliances acquisition success', 'Smart home ecosystem', 'Rendanheyi management model'],
        weaknesses: ['Mature appliance market growth limitations', 'Samsung/LG premium competition', 'Integration of global acquisitions'],
        marketShare: '14%',
        keyProducts: ['Haier refrigerators & washing machines', 'GE Appliances (US)', 'Candy (Europe)', 'AQUA (Japan)', 'Smart home platform'],
        recentProjects: ['GE Appliances plant expansion (US)', 'Smart home AI integration', 'European market share growth', 'Industrial IoT platform'],
        customerBase: 'Global consumers, commercial kitchen operators, smart building developers',
        pricingModel: 'Mass-market to premium tiered pricing across brands',
        marketingApproach: ['Global brand portfolio strategy', 'Retail partnerships', 'Digital marketing', 'Smart home ecosystem positioning']
      }
    ],
    'ecommerce': [
      {
        name: 'Alibaba Group',
        location: 'China',
        foundedYear: 1999,
        annualRevenue: 131000,
        employeeCount: '235K+',
        strengths: ['E-commerce dominance', 'Alipay ecosystem', 'Cloud computing', 'Logistics network'],
        weaknesses: ['Regulatory pressure', 'Competition', 'Profitability challenges'],
        marketShare: '47% (Chinese e-commerce)',
        keyProducts: ['Taobao', 'Tmall', 'Alibaba Cloud', '1688.com', 'Cainiao logistics'],
        recentProjects: ['AI integration', 'Globalization', 'Live commerce', 'Community group buying'],
        customerBase: 'Chinese consumers and businesses',
        pricingModel: 'Commission and advertising',
        marketingApproach: ['Singles Day', 'Live streaming', 'KOL partnerships', 'Platform promotions']
      },
      {
        name: 'JD.com',
        location: 'China',
        foundedYear: 1998,
        annualRevenue: 155000,
        employeeCount: '540K+',
        strengths: ['Logistics ownership', 'Quality assurance', 'Direct sales', 'Technology'],
        weaknesses: ['Lower margins', 'Competitive pressure', 'Growth slowing'],
        marketShare: '17% (Chinese e-commerce)',
        keyProducts: ['JD Retail', 'JD Logistics', 'JD Health', 'JD Technology'],
        recentProjects: ['Autonomous delivery', 'Omnichannel integration', 'Supply chain finance'],
        customerBase: 'Quality-conscious Chinese consumers',
        pricingModel: 'Direct sales with commissions',
        marketingApproach: ['618 Shopping Festival', 'Celebrity endorsements', 'Quality messaging', 'Technology showcase']
      },
      {
        name: 'Pinduoduo',
        location: 'China',
        foundedYear: 2015,
        annualRevenue: 21000,
        employeeCount: '13K+',
        strengths: ['Social commerce', 'Lower-tier cities', 'Agriculture direct', 'Gamification'],
        weaknesses: ['Quality concerns', 'Regulatory scrutiny', 'Brand perception'],
        marketShare: '15% (Chinese e-commerce)',
        keyProducts: ['Group buying', 'Agricultural products', 'Temu (international)', 'Duo Duo Grocery'],
        recentProjects: ['Temu global expansion', 'Agricultural support', 'Manufacturing partnerships'],
        customerBase: 'Value-conscious Chinese consumers',
        pricingModel: 'Ultra-low pricing',
        marketingApproach: ['Social sharing', 'Gamification', 'Subsidies', 'Viral growth']
      }
    ]
  },
  'india': {
    'manufacturing': [
      {
        name: 'Larsen & Toubro (L&T)',
        location: 'India',
        foundedYear: 1938,
        annualRevenue: 26000,
        employeeCount: '50K+',
        strengths: ['Engineering conglomerate breadth', 'Infrastructure project execution', 'Defence manufacturing growth', 'Technology services arm (LTIMindtree)'],
        weaknesses: ['Project execution risk', 'Working capital cycles', 'Competition from Chinese players in certain segments'],
        marketShare: '18%',
        keyProducts: ['Heavy engineering', 'Defence equipment', 'Power plant EPC', 'Industrial machinery', 'Green hydrogen systems'],
        recentProjects: ['Tejas fighter aircraft components', 'Green hydrogen electrolyzers', 'Advanced manufacturing for defence', 'Smart manufacturing expansion'],
        customerBase: 'Government infrastructure projects, defence, power sector, oil & gas',
        pricingModel: 'Fixed-price and cost-plus EPC contracts',
        marketingApproach: ['Government relationship management', 'Direct bidding on tenders', 'International project positioning', 'Technology partnerships']
      },
      {
        name: 'Bharat Heavy Electricals Limited (BHEL)',
        location: 'India',
        foundedYear: 1964,
        annualRevenue: 8500,
        employeeCount: '30K+',
        strengths: ['Power equipment dominance', 'Government backing', 'Installed base (200GW+)', 'Railway electrification growth'],
        weaknesses: ['Slow order execution', 'Dependence on government orders', 'Competition from Chinese imports', 'Margin pressure'],
        marketShare: '35%',
        keyProducts: ['Steam turbines', 'Boilers', 'Transformers', 'Railway traction systems', 'Solar panels'],
        recentProjects: ['Solar energy component manufacturing', 'Railway electrification', 'Defence electronics', 'Supercritical power plants'],
        customerBase: 'NTPC, state electricity boards, railways, defence',
        pricingModel: 'Government tender pricing',
        marketingApproach: ['Government tender participation', 'Long-term relationship management', 'Joint ventures', 'Defence DPP alignment']
      },
      {
        name: 'Tata Steel',
        location: 'India',
        foundedYear: 1907,
        annualRevenue: 22000,
        employeeCount: '78K+',
        strengths: ['Vertically integrated operations', 'Premium products capability', 'Global footprint (India + Europe)', 'Jamshedpur township model'],
        weaknesses: ['UK operations losses', 'Debt from Corus acquisition', 'Energy cost exposure', 'Cyclical steel markets'],
        marketShare: '19%',
        keyProducts: ['Hot-rolled coil', 'Cold-rolled products', 'Wire rod', 'Tubes & pipes', 'Long products'],
        recentProjects: ['Port Talbot EAF transition (UK)', 'EV-grade steel development', 'Kalinganagar capacity expansion', 'Recycled steel growth'],
        customerBase: 'Automotive, construction, engineering, consumer durables',
        pricingModel: 'Index-linked pricing + premium for high-grade products',
        marketingApproach: ['Direct key account management', 'Distribution network', 'Product certification programs', 'Sustainability positioning']
      },
      {
        name: 'Mahindra & Mahindra (Manufacturing)',
        location: 'India',
        foundedYear: 1945,
        annualRevenue: 14000,
        employeeCount: '40K+',
        strengths: ['SUV market leadership', 'Tractor dominance (45% share)', 'EV transition (BE6, XEV9e)', 'Strong brand in rural India'],
        weaknesses: ['International market challenges', 'EV competition from Tata Motors and MG', 'Premium segment gaps'],
        marketShare: '13%',
        keyProducts: ['Thar', 'Scorpio N', 'XUV700', 'JAYO/BE6 EVs', 'Tractors (Mahindra Tractors)'],
        recentProjects: ['Born EV platform launch 2025', 'EV manufacturing plant expansion', 'Tractor export push', 'Defence vehicles'],
        customerBase: 'Urban/semi-urban consumers, farmers, fleet operators, defence',
        pricingModel: 'Retail pricing + fleet discounts + agricultural credit schemes',
        marketingApproach: ['Dealer network (2,000+ outlets)', 'Digital marketing', 'Agri focus campaigns', 'Sponsorships']
      },
      {
        name: 'Asian Paints',
        location: 'India',
        foundedYear: 1942,
        annualRevenue: 4700,
        employeeCount: '8K+',
        strengths: ['#1 paints brand India', 'Distribution network (80,000+ dealers)', 'Premiumization success', 'Beautiful Homes services'],
        weaknesses: ['Raw material (TiO2) price volatility', 'Increasing competition from Grasim/Birla Opus', 'Rural demand slowdown'],
        marketShare: '45%',
        keyProducts: ['Royale luxury paints', 'Apex exterior', 'SmartCare waterproofing', 'Bath fittings (Ess Ess)', 'Smart home services'],
        recentProjects: ['Grasim competition response strategy', 'Beautiful Homes showrooms expansion', 'International market growth (25 countries)', 'Sustainability packaging'],
        customerBase: 'Homeowners, builders, commercial projects, industrial customers',
        pricingModel: 'Premium pricing + tiered product range for all income segments',
        marketingApproach: ['Dealer relationship programs', 'Influencer campaigns', 'TV advertising', 'Digital home design tools']
      }
    ],
    'ecommerce': [
      {
        name: 'Flipkart',
        location: 'India',
        foundedYear: 2007,
        annualRevenue: 6000,
        employeeCount: '30K+',
        strengths: ['Market leadership', 'Walmart backing', 'Local understanding', 'Supply chain'],
        weaknesses: ['Profitability', 'Competition', 'Regulatory challenges'],
        marketShare: '48%',
        keyProducts: ['E-commerce marketplace', 'Myntra fashion', 'PhonePe payments', 'Flipkart Grocery'],
        recentProjects: ['Social commerce', 'Quick commerce', 'Shopsy value platform'],
        customerBase: 'Indian consumers',
        pricingModel: 'Competitive marketplace',
        marketingApproach: ['Big Billion Days', 'Celebrity campaigns', 'Regional marketing', 'Cashback offers']
      },
      {
        name: 'Amazon India',
        location: 'India',
        foundedYear: 2013,
        annualRevenue: 4500,
        employeeCount: '100K+',
        strengths: ['Global resources', 'Technology', 'Prime membership', 'Customer service'],
        weaknesses: ['Regulatory challenges', 'Local competition', 'FDI restrictions'],
        marketShare: '26%',
        keyProducts: ['E-commerce', 'Amazon Prime', 'AWS', 'Amazon Pay'],
        recentProjects: ['Local language support', 'Seller enablement', 'Rural expansion'],
        customerBase: 'Indian consumers',
        pricingModel: 'Marketplace with Prime',
        marketingApproach: ['Prime Day', 'Great Indian Festival', 'Regional campaigns', 'Influencer partnerships']
      }
    ],
    'technology': [
      {
        name: 'Tata Consultancy Services',
        location: 'India',
        foundedYear: 1968,
        annualRevenue: 27900,
        employeeCount: '614K+',
        strengths: ['Global delivery', 'Industry expertise', 'Digital services', 'Brand trust'],
        weaknesses: ['Margin pressure', 'Attrition', 'Competition'],
        marketShare: '8%',
        keyProducts: ['IT services', 'Consulting', 'Digital transformation', 'Cloud migration'],
        recentProjects: ['AI.Cloud platform', 'Sustainability solutions', 'Industry 4.0'],
        customerBase: 'Global enterprises',
        pricingModel: 'Time and materials / fixed price',
        marketingApproach: ['Thought leadership', 'Client relationships', 'Industry events', 'Brand campaigns']
      },
      {
        name: 'Infosys Limited',
        location: 'India',
        foundedYear: 1981,
        annualRevenue: 18200,
        employeeCount: '342K+',
        strengths: ['Digital leadership', 'Client relationships', 'Innovation', 'Training'],
        weaknesses: ['Attrition challenges', 'Margin compression', 'Competition'],
        marketShare: '5%',
        keyProducts: ['Digital transformation', 'Cloud services', 'Consulting', 'Engineering services'],
        recentProjects: ['Infosys Topaz AI', 'Cobalt cloud', 'ESG initiatives'],
        customerBase: 'Global enterprises',
        pricingModel: 'Value-based and T&M',
        marketingApproach: ['Brand building', 'Sponsorships', 'Innovation showcases', 'Executive programs']
      }
    ]
  }
};

// Helper function to get real competitors based on location and business idea
export function getRealCompetitors(location: string, businessIdea: string, targetRevenue: number): CompanyData[] {
  const locationKey = location.toLowerCase().replace(/\s+/g, '-');
  
  // Determine industry from business idea
  let industry = 'retail'; // default
  const ideaLower = businessIdea.toLowerCase();
  
  if (ideaLower.includes('tech') || ideaLower.includes('software') || ideaLower.includes('app') || 
      ideaLower.includes('digital') || ideaLower.includes('platform') || ideaLower.includes('cloud') ||
      ideaLower.includes('ai') || ideaLower.includes('data') || ideaLower.includes('saas')) {
    industry = 'technology';
  } else if (ideaLower.includes('manufactur') || ideaLower.includes('production') || ideaLower.includes('factory') ||
             ideaLower.includes('industrial') || ideaLower.includes('fabricat') || ideaLower.includes('assembly line') ||
             ideaLower.includes('plant operations') || ideaLower.includes('process plant')) {
    industry = 'manufacturing';
  } else if (ideaLower.includes('restaurant') || ideaLower.includes('cafe') || 
             ideaLower.includes('dining') || ideaLower.includes('coffee shop')) {
    industry = 'restaurant';
  } else if (ideaLower.includes('food processing') || ideaLower.includes('food manufactur') || ideaLower.includes('food production')) {
    industry = 'manufacturing';
  } else if (ideaLower.includes('ecommerce') || ideaLower.includes('e-commerce') || ideaLower.includes('online store') ||
             ideaLower.includes('marketplace') || ideaLower.includes('online shopping')) {
    industry = 'ecommerce';
  } else if (ideaLower.includes('health') || ideaLower.includes('medical') || ideaLower.includes('clinic') ||
             ideaLower.includes('pharmacy') || ideaLower.includes('wellness')) {
    industry = 'healthcare';
  } else if (ideaLower.includes('automotive') || ideaLower.includes('automobile') || ideaLower.includes('car manufactur') ||
             ideaLower.includes('vehicle manufactur') || ideaLower.includes('auto industry')) {
    industry = 'automotive';
  } else if (ideaLower.includes('logistics') || ideaLower.includes('supply chain') || ideaLower.includes('freight') ||
             ideaLower.includes('shipping company') || ideaLower.includes('warehousing') || ideaLower.includes('courier')) {
    industry = 'manufacturing'; // falls back to manufacturing for industrial operations
  } else if (ideaLower.includes('construction') || ideaLower.includes('infrastructure') || ideaLower.includes('civil engineering')) {
    industry = 'manufacturing';
  } else if (ideaLower.includes('retail') || ideaLower.includes('supermarket') || ideaLower.includes('grocery') ||
             ideaLower.includes('consumer goods') || ideaLower.includes('department store')) {
    industry = 'retail';
  }
  
  // Get competitors for this location and industry
  const locationData = realCompaniesDatabase[locationKey];
  if (locationData && locationData[industry]) {
    return locationData[industry];
  }
  
  // Fallback: try to find the closest industry data for this location
  if (locationData) {
    // Try to find a relevant industry match rather than just first available
    const industrialFallbacks: { [key: string]: string[] } = {
      'manufacturing': ['technology', 'retail'],
      'technology': ['manufacturing', 'retail'],
      'restaurant': ['retail', 'technology'],
      'healthcare': ['technology', 'retail'],
      'automotive': ['manufacturing', 'technology'],
      'ecommerce': ['retail', 'technology'],
    };
    const fallbackOrder = industrialFallbacks[industry] || Object.keys(locationData);
    for (const fallbackIndustry of fallbackOrder) {
      if (locationData[fallbackIndustry]) {
        return locationData[fallbackIndustry];
      }
    }
    const industries = Object.keys(locationData);
    if (industries.length > 0) {
      return locationData[industries[0]];
    }
  }
  
  // Try global database first for manufacturing and other industries
  const globalData = realCompaniesDatabase['global'];
  if (globalData && globalData[industry]) {
    return globalData[industry].map(comp => ({
      ...comp,
      location: `${location} (Global operations)`
    }));
  }

  // Last fallback: use US data
  const usData = realCompaniesDatabase['united-states'];
  if (usData[industry]) {
    // Adapt the location
    return usData[industry].map(comp => ({
      ...comp,
      location: `${location} (Global operations)`
    }));
  }
  
  // Ultimate fallback — use US manufacturing data (much more relevant than retail for unknown industries)
  if (usData['manufacturing']) {
    return usData['manufacturing'].map(comp => ({
      ...comp,
      location: `${location} (Global operations)`
    }));
  }

  return usData['retail'].map(comp => ({
    ...comp,
    location: `${location} (Global operations)`
  }));
}
