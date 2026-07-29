// @ts-nocheck
export interface LocationInfo {
  name: string;
  currency: string;
  currencySymbol: string;
  priceMultiplier: number; // Relative to US baseline
  phoneFormat: string;
  phonePrefix: string;
  timezone: string;
  businessHours: string;
  averageSalary: string;
  taxRate: string;
  laborCostMultiplier: number;
  realEstateMultiplier: number;
  // Economic indicators
  gdpGrowthRate: number; // Annual GDP growth %
  inflationRate: number; // Annual inflation %
  interestRate: number; // Base interest rate %
  marketGrowthMultiplier: number; // Market growth relative to global average
  corporateTaxRate: number; // Corporate tax %
  regulatoryComplexity: 'Low' | 'Medium' | 'High';
  marketMaturity: 'Emerging' | 'Growth' | 'Mature';
  riskLevel: 'Low' | 'Medium' | 'High';
  easeOfDoingBusiness: number; // Score out of 100
}

// Available currencies for manual selection
export interface CurrencyInfo {
  code: string;
  symbol: string;
  name: string;
  conversionRate: number; // Relative to USD
}

export const currencies: CurrencyInfo[] = [
  { code: 'USD', symbol: '$', name: 'US Dollar', conversionRate: 1.0 },
  { code: 'EUR', symbol: '€', name: 'Euro', conversionRate: 0.93 },
  { code: 'GBP', symbol: '£', name: 'British Pound', conversionRate: 0.80 },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar', conversionRate: 1.37 },
  { code: 'AUD', symbol: 'A$', name: 'Australian Dollar', conversionRate: 1.54 },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen', conversionRate: 150.8 },
  { code: 'CNY', symbol: '¥', name: 'Chinese Yuan', conversionRate: 7.28 },
  { code: 'INR', symbol: '₹', name: 'Indian Rupee', conversionRate: 83.45 },
  { code: 'KRW', symbol: '₩', name: 'South Korean Won', conversionRate: 1335.0 },
  { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar', conversionRate: 1.35 },
  { code: 'MXN', symbol: 'MX$', name: 'Mexican Peso', conversionRate: 17.4 },
  { code: 'BRL', symbol: 'R$', name: 'Brazilian Real', conversionRate: 5.02 },
  { code: 'ARS', symbol: 'AR$', name: 'Argentine Peso', conversionRate: 365.0 },
  { code: 'AED', symbol: 'AED', name: 'UAE Dirham', conversionRate: 3.67 },
  { code: 'SAR', symbol: 'SAR', name: 'Saudi Riyal', conversionRate: 3.75 },
  { code: 'ZAR', symbol: 'R', name: 'South African Rand', conversionRate: 18.8 },
  { code: 'NGN', symbol: '₦', name: 'Nigerian Naira', conversionRate: 820.0 },
  { code: 'NOK', symbol: 'kr', name: 'Norwegian Krone', conversionRate: 11.0 },
  { code: 'SEK', symbol: 'kr', name: 'Swedish Krona', conversionRate: 11.0 },
  { code: 'DKK', symbol: 'kr', name: 'Danish Krone', conversionRate: 7.0 },
  { code: 'CHF', symbol: 'CHF', name: 'Swiss Franc', conversionRate: 1.0 },
  { code: 'PLN', symbol: 'zł', name: 'Polish Złoty', conversionRate: 4.0 },
  { code: 'TRY', symbol: '₺', name: 'Turkish Lira', conversionRate: 18.0 },
  { code: 'NZD', symbol: 'NZ$', name: 'New Zealand Dollar', conversionRate: 1.5 },
  { code: 'ILS', symbol: '₪', name: 'Israeli New Shekel', conversionRate: 3.5 },
];

// Location name to key mapping helper
export function getLocationKey(locationName: string): string {
  const mapping: { [key: string]: string } = {
    'united states': 'usa',
    'united kingdom': 'uk',
    'canada': 'canada',
    'mexico': 'mexico',
    'australia': 'australia',
    'germany': 'germany',
    'france': 'france',
    'spain': 'spain',
    'italy': 'italy',
    'japan': 'japan',
    'china': 'china',
    'india': 'india',
    'south korea': 'south-korea',
    'singapore': 'singapore',
    'brazil': 'brazil',
    'uae': 'uae',
    'united arab emirates': 'uae',
    'south africa': 'south-africa',
    'saudi arabia': 'saudi-arabia',
    'argentina': 'argentina',
    'nigeria': 'nigeria',
    // Individual European / other countries — each gets their own entry
    'netherlands': 'netherlands',
    'switzerland': 'switzerland',
    'sweden': 'sweden',
    'norway': 'norway',
    'denmark': 'denmark',
    'ireland': 'ireland',
    'new zealand': 'new-zealand',
    'israel': 'israel',
    'poland': 'poland',
    'turkey': 'turkey',
    // Regional / aggregate location display names
    'north america': 'north-america',
    'europe': 'europe',
    'asia-pacific': 'asia-pacific',
    'latin america': 'latin-america',
    'middle east': 'middle-east',
    'africa': 'africa',
    'global': 'global',
  };
  
  const key = locationName.toLowerCase();
  return mapping[key] || 'global';
}

export const locationData: { [key: string]: LocationInfo } = {
  'global': {
    name: 'Global',
    currency: 'USD',
    currencySymbol: '$',
    priceMultiplier: 1.0,
    phoneFormat: '+1 (XXX) XXX-XXXX',
    phonePrefix: '+1',
    timezone: 'Various',
    businessHours: '9 AM - 5 PM local time',
    averageSalary: '$65,000',
    taxRate: '20-30%',
    laborCostMultiplier: 1.0,
    realEstateMultiplier: 1.0,
    // Economic indicators
    gdpGrowthRate: 2.5,
    inflationRate: 2.0,
    interestRate: 2.5,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 21,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 60,
  },
  'north-america': {
    name: 'North America',
    currency: 'USD',
    currencySymbol: '$',
    priceMultiplier: 1.0,
    phoneFormat: '+1 (XXX) XXX-XXXX',
    phonePrefix: '+1',
    timezone: 'EST/PST',
    businessHours: '9 AM - 6 PM',
    averageSalary: '$62,000',
    taxRate: '22-28%',
    laborCostMultiplier: 1.0,
    realEstateMultiplier: 1.0,
    // Economic indicators
    gdpGrowthRate: 2.5,
    inflationRate: 2.0,
    interestRate: 2.5,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 21,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 60,
  },
  'usa': {
    name: 'United States',
    currency: 'USD',
    currencySymbol: '$',
    priceMultiplier: 1.0,
    phoneFormat: '+1 (XXX) XXX-XXXX',
    phonePrefix: '+1',
    timezone: 'EST/CST/MST/PST',
    businessHours: '9 AM - 6 PM',
    averageSalary: '$72,500',
    taxRate: '22-37%',
    laborCostMultiplier: 1.0,
    realEstateMultiplier: 1.0,
    // Economic indicators
    gdpGrowthRate: 2.5,
    inflationRate: 2.0,
    interestRate: 2.5,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 21,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 60,
  },
  'canada': {
    name: 'Canada',
    currency: 'CAD',
    currencySymbol: 'C$',
    priceMultiplier: 0.85,
    phoneFormat: '+1 (XXX) XXX-XXXX',
    phonePrefix: '+1',
    timezone: 'EST/MST/PST',
    businessHours: '9 AM - 5 PM',
    averageSalary: 'C$62,000',
    taxRate: '26-33%',
    laborCostMultiplier: 0.85,
    realEstateMultiplier: 0.9,
    // Economic indicators — Bank of Canada / Statistics Canada 2025/2026
    gdpGrowthRate: 1.3,
    inflationRate: 1.9,
    interestRate: 3.0,
    marketGrowthMultiplier: 0.95,
    corporateTaxRate: 26,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 75,
  },
  'mexico': {
    name: 'Mexico',
    currency: 'MXN',
    currencySymbol: 'MX$',
    priceMultiplier: 0.35,
    phoneFormat: '+52 XX XXXX XXXX',
    phonePrefix: '+52',
    timezone: 'CST',
    businessHours: '9 AM - 6 PM',
    averageSalary: 'MX$285,000',
    taxRate: '30-35%',
    laborCostMultiplier: 0.25,
    realEstateMultiplier: 0.4,
    // Economic indicators
    gdpGrowthRate: 2.0,
    inflationRate: 4.0,
    interestRate: 7.0,
    marketGrowthMultiplier: 0.8,
    corporateTaxRate: 30,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'High',
    easeOfDoingBusiness: 50,
  },
  'europe': {
    name: 'Europe',
    currency: 'EUR',
    currencySymbol: '€',
    priceMultiplier: 1.1,
    phoneFormat: '+XX XX XXXX XXXX',
    phonePrefix: '+44/+49/+33',
    timezone: 'CET/GMT',
    businessHours: '9 AM - 5 PM',
    averageSalary: '€48,000',
    taxRate: '25-45%',
    laborCostMultiplier: 1.1,
    realEstateMultiplier: 1.2,
    // Economic indicators
    gdpGrowthRate: 2.0,
    inflationRate: 2.0,
    interestRate: 0.5,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 20,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 70,
  },
  'uk': {
    name: 'United Kingdom',
    currency: 'GBP',
    currencySymbol: '£',
    priceMultiplier: 1.15,
    phoneFormat: '+44 XXXX XXXXXX',
    phonePrefix: '+44',
    timezone: 'GMT',
    businessHours: '9 AM - 5:30 PM',
    averageSalary: '£44,500',
    taxRate: '20-45%',
    laborCostMultiplier: 1.15,
    realEstateMultiplier: 1.4,
    // Economic indicators — Bank of England / ONS 2025/2026
    gdpGrowthRate: 0.9,
    inflationRate: 3.2,
    interestRate: 4.5,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 25,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 70,
  },
  'germany': {
    name: 'Germany',
    currency: 'EUR',
    currencySymbol: '€',
    priceMultiplier: 1.1,
    phoneFormat: '+49 XXX XXXXXXX',
    phonePrefix: '+49',
    timezone: 'CET',
    businessHours: '9 AM - 5 PM',
    averageSalary: '€52,000',
    taxRate: '30-45%',
    laborCostMultiplier: 1.2,
    realEstateMultiplier: 1.15,
    // Economic indicators — Bundesbank / Destatis 2025/2026
    gdpGrowthRate: 0.2,
    inflationRate: 2.3,
    interestRate: 2.65,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 30,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 70,
  },
  'france': {
    name: 'France',
    currency: 'EUR',
    currencySymbol: '€',
    priceMultiplier: 1.12,
    phoneFormat: '+33 X XX XX XX XX',
    phonePrefix: '+33',
    timezone: 'CET',
    businessHours: '9 AM - 6 PM',
    averageSalary: '€45,000',
    taxRate: '30-50%',
    laborCostMultiplier: 1.25,
    realEstateMultiplier: 1.3,
    // Economic indicators — INSEE / Banque de France 2025/2026
    gdpGrowthRate: 1.1,
    inflationRate: 1.7,
    interestRate: 2.65,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 25,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 70,
  },
  'spain': {
    name: 'Spain',
    currency: 'EUR',
    currencySymbol: '€',
    priceMultiplier: 0.85,
    phoneFormat: '+34 XXX XXX XXX',
    phonePrefix: '+34',
    timezone: 'CET',
    businessHours: '9 AM - 6 PM',
    averageSalary: '€35,000',
    taxRate: '24-47%',
    laborCostMultiplier: 0.8,
    realEstateMultiplier: 0.9,
    // Economic indicators — Banco de España / INE 2025/2026
    gdpGrowthRate: 2.4,
    inflationRate: 2.8,
    interestRate: 2.65,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 25,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 70,
  },
  'italy': {
    name: 'Italy',
    currency: 'EUR',
    currencySymbol: '€',
    priceMultiplier: 0.95,
    phoneFormat: '+39 XXX XXX XXXX',
    phonePrefix: '+39',
    timezone: 'CET',
    businessHours: '9 AM - 6 PM',
    averageSalary: '€38,000',
    taxRate: '23-43%',
    laborCostMultiplier: 0.9,
    realEstateMultiplier: 1.0,
    // Economic indicators — Banca d'Italia / ISTAT 2025/2026
    gdpGrowthRate: 0.7,
    inflationRate: 1.5,
    interestRate: 2.65,
    marketGrowthMultiplier: 0.9,
    corporateTaxRate: 24,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 65,
  },
  'asia-pacific': {
    name: 'Asia-Pacific',
    currency: 'USD',
    currencySymbol: '$',
    priceMultiplier: 0.7,
    phoneFormat: '+XX XXXX XXXX',
    phonePrefix: '+86/+81/+91',
    timezone: 'Various',
    businessHours: '9 AM - 6 PM',
    averageSalary: '$32,000',
    taxRate: '15-35%',
    laborCostMultiplier: 0.5,
    realEstateMultiplier: 0.8,
    // Economic indicators
    gdpGrowthRate: 5.0,
    inflationRate: 2.0,
    interestRate: 4.0,
    marketGrowthMultiplier: 1.2,
    corporateTaxRate: 20,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'High',
    easeOfDoingBusiness: 50,
  },
  'china': {
    name: 'China',
    currency: 'CNY',
    currencySymbol: '¥',
    priceMultiplier: 0.55,
    phoneFormat: '+86 XXX XXXX XXXX',
    phonePrefix: '+86',
    timezone: 'CST',
    businessHours: '9 AM - 6 PM',
    averageSalary: '¥285,000',
    taxRate: '20-45%',
    laborCostMultiplier: 0.4,
    realEstateMultiplier: 1.1,
    // Economic indicators — NBS China / PBOC 2025/2026
    gdpGrowthRate: 4.9,
    inflationRate: 0.5,
    interestRate: 3.1,
    marketGrowthMultiplier: 1.2,
    corporateTaxRate: 25,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'High',
    easeOfDoingBusiness: 45,
  },
  'japan': {
    name: 'Japan',
    currency: 'JPY',
    currencySymbol: '¥',
    priceMultiplier: 1.05,
    phoneFormat: '+81 XX XXXX XXXX',
    phonePrefix: '+81',
    timezone: 'JST',
    businessHours: '9 AM - 6 PM',
    averageSalary: '¥5,200,000',
    taxRate: '20-45%',
    laborCostMultiplier: 1.0,
    realEstateMultiplier: 1.8,
    // Economic indicators — Bank of Japan / Cabinet Office 2025/2026
    gdpGrowthRate: 0.4,
    inflationRate: 3.6,
    interestRate: 0.5,
    marketGrowthMultiplier: 0.9,
    corporateTaxRate: 23,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 72,
  },
  'india': {
    name: 'India',
    currency: 'INR',
    currencySymbol: '₹',
    priceMultiplier: 0.25,
    phoneFormat: '+91 XXXXX XXXXX',
    phonePrefix: '+91',
    timezone: 'IST',
    businessHours: '10 AM - 7 PM',
    averageSalary: '₹9,20,000',
    taxRate: '20-30%',
    laborCostMultiplier: 0.2,
    realEstateMultiplier: 0.3,
    // Economic indicators — RBI / MOSPI 2025/2026
    gdpGrowthRate: 6.5,
    inflationRate: 4.9,
    interestRate: 6.25,
    marketGrowthMultiplier: 1.5,
    corporateTaxRate: 22,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 55,
  },
  'south-korea': {
    name: 'South Korea',
    currency: 'KRW',
    currencySymbol: '₩',
    priceMultiplier: 0.8,
    phoneFormat: '+82 XX XXXX XXXX',
    phonePrefix: '+82',
    timezone: 'KST',
    businessHours: '9 AM - 6 PM',
    averageSalary: '₩45,000,000',
    taxRate: '15-42%',
    laborCostMultiplier: 0.75,
    realEstateMultiplier: 1.3,
    // Economic indicators — Bank of Korea / Statistics Korea 2025/2026
    gdpGrowthRate: 2.3,
    inflationRate: 2.2,
    interestRate: 2.75,
    marketGrowthMultiplier: 1.05,
    corporateTaxRate: 22,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 72,
  },
  'australia': {
    name: 'Australia',
    currency: 'AUD',
    currencySymbol: 'A$',
    priceMultiplier: 1.05,
    phoneFormat: '+61 X XXXX XXXX',
    phonePrefix: '+61',
    timezone: 'AEST',
    businessHours: '9 AM - 5 PM',
    averageSalary: 'A$90,000',
    taxRate: '19-45%',
    laborCostMultiplier: 1.1,
    realEstateMultiplier: 1.2,
    // Economic indicators — Reserve Bank of Australia / ABS 2025/2026
    gdpGrowthRate: 1.5,
    inflationRate: 2.4,
    interestRate: 4.1,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 30,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 75,
  },
  'singapore': {
    name: 'Singapore',
    currency: 'SGD',
    currencySymbol: 'S$',
    priceMultiplier: 1.15,
    phoneFormat: '+65 XXXX XXXX',
    phonePrefix: '+65',
    timezone: 'SGT',
    businessHours: '9 AM - 6 PM',
    averageSalary: 'S$75,000',
    taxRate: '15-22%',
    laborCostMultiplier: 1.0,
    realEstateMultiplier: 2.0,
    // Economic indicators — MAS / Singapore DOS 2025/2026
    gdpGrowthRate: 4.4,
    inflationRate: 1.5,
    interestRate: 3.4,
    marketGrowthMultiplier: 1.1,
    corporateTaxRate: 17,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 88,
  },
  'latin-america': {
    name: 'Latin America',
    currency: 'USD',
    currencySymbol: '$',
    priceMultiplier: 0.4,
    phoneFormat: '+XX XX XXXX XXXX',
    phonePrefix: '+52/+55',
    timezone: 'Various',
    businessHours: '9 AM - 6 PM',
    averageSalary: '$22,000',
    taxRate: '25-35%',
    laborCostMultiplier: 0.35,
    realEstateMultiplier: 0.5,
    // Economic indicators
    gdpGrowthRate: 2.0,
    inflationRate: 4.0,
    interestRate: 7.0,
    marketGrowthMultiplier: 0.8,
    corporateTaxRate: 30,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'High',
    easeOfDoingBusiness: 50,
  },
  'brazil': {
    name: 'Brazil',
    currency: 'BRL',
    currencySymbol: 'R$',
    priceMultiplier: 0.45,
    phoneFormat: '+55 XX XXXXX XXXX',
    phonePrefix: '+55',
    timezone: 'BRT',
    businessHours: '9 AM - 6 PM',
    averageSalary: 'R$52,000',
    taxRate: '27.5-40%',
    laborCostMultiplier: 0.4,
    realEstateMultiplier: 0.6,
    // Economic indicators — Banco Central do Brasil / IBGE 2025/2026
    gdpGrowthRate: 3.2,
    inflationRate: 4.8,
    interestRate: 13.75,
    marketGrowthMultiplier: 0.9,
    corporateTaxRate: 34,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'High',
    easeOfDoingBusiness: 50,
  },
  'argentina': {
    name: 'Argentina',
    currency: 'ARS',
    currencySymbol: 'AR$',
    priceMultiplier: 0.35,
    phoneFormat: '+54 XX XXXX XXXX',
    phonePrefix: '+54',
    timezone: 'ART',
    businessHours: '9 AM - 6 PM',
    averageSalary: 'AR$3,500,000',
    taxRate: '25-35%',
    laborCostMultiplier: 0.15,
    realEstateMultiplier: 0.2,
    // Economic indicators — INDEC / BCRA 2025/2026
    gdpGrowthRate: 5.0,
    inflationRate: 118.0,
    interestRate: 32.0,
    marketGrowthMultiplier: 0.7,
    corporateTaxRate: 35,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'High',
    easeOfDoingBusiness: 45,
  },
  'middle-east': {
    name: 'Middle East',
    currency: 'USD',
    currencySymbol: '$',
    priceMultiplier: 0.85,
    phoneFormat: '+XXX XX XXX XXXX',
    phonePrefix: '+971/+966',
    timezone: 'GST',
    businessHours: '8 AM - 5 PM',
    averageSalary: '$42,000',
    taxRate: '0-20%',
    laborCostMultiplier: 0.6,
    realEstateMultiplier: 1.0,
    // Economic indicators
    gdpGrowthRate: 2.0,
    inflationRate: 2.0,
    interestRate: 2.5,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 20,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 70,
  },
  'uae': {
    name: 'United Arab Emirates',
    currency: 'AED',
    currencySymbol: 'AED',
    priceMultiplier: 1.0,
    phoneFormat: '+971 XX XXX XXXX',
    phonePrefix: '+971',
    timezone: 'GST',
    businessHours: '8 AM - 5 PM',
    averageSalary: 'AED 180,000',
    taxRate: '0-9%',
    laborCostMultiplier: 0.8,
    realEstateMultiplier: 1.3,
    // Economic indicators
    gdpGrowthRate: 2.0,
    inflationRate: 2.0,
    interestRate: 2.5,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 0,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 70,
  },
  'saudi-arabia': {
    name: 'Saudi Arabia',
    currency: 'SAR',
    currencySymbol: 'SAR',
    priceMultiplier: 0.75,
    phoneFormat: '+966 XX XXX XXXX',
    phonePrefix: '+966',
    timezone: 'AST',
    businessHours: '8 AM - 4 PM',
    averageSalary: 'SAR 120,000',
    taxRate: '20%',
    laborCostMultiplier: 0.7,
    realEstateMultiplier: 0.9,
    // Economic indicators
    gdpGrowthRate: 2.0,
    inflationRate: 2.0,
    interestRate: 2.5,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 20,
    regulatoryComplexity: 'High',
    marketMaturity: 'Mature',
    riskLevel: 'Medium',
    easeOfDoingBusiness: 70,
  },
  'africa': {
    name: 'Africa',
    currency: 'USD',
    currencySymbol: '$',
    priceMultiplier: 0.35,
    phoneFormat: '+XXX XX XXX XXXX',
    phonePrefix: '+27/+234',
    timezone: 'Various',
    businessHours: '8 AM - 5 PM',
    averageSalary: '$18,000',
    taxRate: '18-35%',
    laborCostMultiplier: 0.25,
    realEstateMultiplier: 0.4,
    // Economic indicators
    gdpGrowthRate: 3.0,
    inflationRate: 5.0,
    interestRate: 10.0,
    marketGrowthMultiplier: 0.8,
    corporateTaxRate: 30,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'High',
    easeOfDoingBusiness: 50,
  },
  'south-africa': {
    name: 'South Africa',
    currency: 'ZAR',
    currencySymbol: 'R',
    priceMultiplier: 0.4,
    phoneFormat: '+27 XX XXX XXXX',
    phonePrefix: '+27',
    timezone: 'SAST',
    businessHours: '8 AM - 5 PM',
    averageSalary: 'R 420,000',
    taxRate: '18-45%',
    laborCostMultiplier: 0.35,
    realEstateMultiplier: 0.5,
    // Economic indicators
    gdpGrowthRate: 2.0,
    inflationRate: 5.0,
    interestRate: 10.0,
    marketGrowthMultiplier: 0.8,
    corporateTaxRate: 28,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'High',
    easeOfDoingBusiness: 50,
  },
  'nigeria': {
    name: 'Nigeria',
    currency: 'NGN',
    currencySymbol: '₦',
    priceMultiplier: 0.28,
    phoneFormat: '+234 XXX XXX XXXX',
    phonePrefix: '+234',
    timezone: 'WAT',
    businessHours: '8 AM - 5 PM',
    averageSalary: '₦4,800,000',
    taxRate: '7-24%',
    laborCostMultiplier: 0.2,
    realEstateMultiplier: 0.3,
    // Economic indicators — CBN / NBS 2025/2026
    gdpGrowthRate: 3.4,
    inflationRate: 33.2,
    interestRate: 27.25,
    marketGrowthMultiplier: 0.85,
    corporateTaxRate: 30,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'High',
    easeOfDoingBusiness: 45,
  },
  // ── Individual European & other countries ─────────────────────────────────
  'norway': {
    name: 'Norway',
    currency: 'NOK',
    currencySymbol: 'kr',
    priceMultiplier: 1.35,
    phoneFormat: '+47 XXX XX XXX',
    phonePrefix: '+47',
    timezone: 'CET',
    businessHours: '8 AM - 4 PM',
    averageSalary: 'kr 650,000',
    taxRate: '22-47%',
    laborCostMultiplier: 1.5,
    realEstateMultiplier: 1.4,
    // Economic indicators — Norges Bank / SSB 2025/2026
    gdpGrowthRate: 2.1,
    inflationRate: 3.0,
    interestRate: 4.5,
    marketGrowthMultiplier: 1.05,
    corporateTaxRate: 22,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 80,
  },
  'sweden': {
    name: 'Sweden',
    currency: 'SEK',
    currencySymbol: 'kr',
    priceMultiplier: 1.2,
    phoneFormat: '+46 XX XXX XXXX',
    phonePrefix: '+46',
    timezone: 'CET',
    businessHours: '8 AM - 5 PM',
    averageSalary: 'kr 420,000',
    taxRate: '20-57%',
    laborCostMultiplier: 1.3,
    realEstateMultiplier: 1.3,
    // Economic indicators — Riksbank / SCB 2025/2026
    gdpGrowthRate: 0.5,
    inflationRate: 2.3,
    interestRate: 2.75,
    marketGrowthMultiplier: 1.0,
    corporateTaxRate: 20.6,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 79,
  },
  'denmark': {
    name: 'Denmark',
    currency: 'DKK',
    currencySymbol: 'kr',
    priceMultiplier: 1.3,
    phoneFormat: '+45 XXXX XXXX',
    phonePrefix: '+45',
    timezone: 'CET',
    businessHours: '8 AM - 4 PM',
    averageSalary: 'kr 480,000',
    taxRate: '22-52%',
    laborCostMultiplier: 1.4,
    realEstateMultiplier: 1.35,
    // Economic indicators — Danmarks Nationalbank / Statistics Denmark 2025/2026
    gdpGrowthRate: 2.0,
    inflationRate: 2.5,
    interestRate: 3.1,
    marketGrowthMultiplier: 1.05,
    corporateTaxRate: 22,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 82,
  },
  'netherlands': {
    name: 'Netherlands',
    currency: 'EUR',
    currencySymbol: '€',
    priceMultiplier: 1.15,
    phoneFormat: '+31 XX XXX XXXX',
    phonePrefix: '+31',
    timezone: 'CET',
    businessHours: '9 AM - 5:30 PM',
    averageSalary: '€54,000',
    taxRate: '36-49%',
    laborCostMultiplier: 1.25,
    realEstateMultiplier: 1.35,
    // Economic indicators — De Nederlandsche Bank / CBS 2025/2026
    gdpGrowthRate: 1.6,
    inflationRate: 2.7,
    interestRate: 2.65,
    marketGrowthMultiplier: 1.05,
    corporateTaxRate: 25.8,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 80,
  },
  'switzerland': {
    name: 'Switzerland',
    currency: 'CHF',
    currencySymbol: 'CHF',
    priceMultiplier: 1.5,
    phoneFormat: '+41 XX XXX XXXX',
    phonePrefix: '+41',
    timezone: 'CET',
    businessHours: '8 AM - 5 PM',
    averageSalary: 'CHF 95,000',
    taxRate: '13-22%',
    laborCostMultiplier: 1.6,
    realEstateMultiplier: 1.8,
    // Economic indicators — SNB / Swiss Federal Statistics Office 2025/2026
    gdpGrowthRate: 1.4,
    inflationRate: 1.1,
    interestRate: 0.5,
    marketGrowthMultiplier: 1.05,
    corporateTaxRate: 14.9,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 84,
  },
  'ireland': {
    name: 'Ireland',
    currency: 'EUR',
    currencySymbol: '€',
    priceMultiplier: 1.2,
    phoneFormat: '+353 XX XXX XXXX',
    phonePrefix: '+353',
    timezone: 'GMT',
    businessHours: '9 AM - 5:30 PM',
    averageSalary: '€50,000',
    taxRate: '20-40%',
    laborCostMultiplier: 1.2,
    realEstateMultiplier: 1.5,
    // Economic indicators — Central Bank of Ireland / CSO 2025/2026
    gdpGrowthRate: 3.5,
    inflationRate: 2.4,
    interestRate: 2.65,
    marketGrowthMultiplier: 1.1,
    corporateTaxRate: 12.5,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 78,
  },
  'poland': {
    name: 'Poland',
    currency: 'PLN',
    currencySymbol: 'zł',
    priceMultiplier: 0.6,
    phoneFormat: '+48 XXX XXX XXX',
    phonePrefix: '+48',
    timezone: 'CET',
    businessHours: '8 AM - 5 PM',
    averageSalary: 'zł 72,000',
    taxRate: '12-32%',
    laborCostMultiplier: 0.55,
    realEstateMultiplier: 0.65,
    // Economic indicators — NBP / GUS 2025/2026
    gdpGrowthRate: 3.8,
    inflationRate: 4.9,
    interestRate: 5.75,
    marketGrowthMultiplier: 1.05,
    corporateTaxRate: 19,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Growth',
    riskLevel: 'Low',
    easeOfDoingBusiness: 72,
  },
  'turkey': {
    name: 'Turkey',
    currency: 'TRY',
    currencySymbol: '₺',
    priceMultiplier: 0.3,
    phoneFormat: '+90 XXX XXX XXXX',
    phonePrefix: '+90',
    timezone: 'TRT',
    businessHours: '9 AM - 6 PM',
    averageSalary: '₺360,000',
    taxRate: '15-40%',
    laborCostMultiplier: 0.25,
    realEstateMultiplier: 0.5,
    // Economic indicators — CBRT / TurkStat 2025/2026
    gdpGrowthRate: 3.0,
    inflationRate: 65.0,
    interestRate: 42.5,
    marketGrowthMultiplier: 0.85,
    corporateTaxRate: 25,
    regulatoryComplexity: 'High',
    marketMaturity: 'Emerging',
    riskLevel: 'High',
    easeOfDoingBusiness: 55,
  },
  'new-zealand': {
    name: 'New Zealand',
    currency: 'NZD',
    currencySymbol: 'NZ$',
    priceMultiplier: 0.95,
    phoneFormat: '+64 X XXX XXXX',
    phonePrefix: '+64',
    timezone: 'NZST',
    businessHours: '8:30 AM - 5 PM',
    averageSalary: 'NZ$70,000',
    taxRate: '10.5-39%',
    laborCostMultiplier: 1.0,
    realEstateMultiplier: 1.1,
    // Economic indicators — Reserve Bank of NZ / Stats NZ 2025/2026
    gdpGrowthRate: 0.8,
    inflationRate: 2.5,
    interestRate: 3.75,
    marketGrowthMultiplier: 0.95,
    corporateTaxRate: 28,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'Low',
    easeOfDoingBusiness: 82,
  },
  'israel': {
    name: 'Israel',
    currency: 'ILS',
    currencySymbol: '₪',
    priceMultiplier: 1.1,
    phoneFormat: '+972 XX XXX XXXX',
    phonePrefix: '+972',
    timezone: 'IST',
    businessHours: '8:30 AM - 5 PM (Sun–Thu)',
    averageSalary: '₪180,000',
    taxRate: '20-50%',
    laborCostMultiplier: 1.1,
    realEstateMultiplier: 1.6,
    // Economic indicators — Bank of Israel / CBS 2025/2026
    gdpGrowthRate: 1.7,
    inflationRate: 2.8,
    interestRate: 4.5,
    marketGrowthMultiplier: 1.1,
    corporateTaxRate: 23,
    regulatoryComplexity: 'Medium',
    marketMaturity: 'Mature',
    riskLevel: 'High',
    easeOfDoingBusiness: 70,
  },
};

export function getLocationInfo(locationKey: string): LocationInfo {
  return locationData[locationKey] || locationData['global'];
}

export function formatCurrency(amount: number, locationKey: string, decimals: number = 1): string {
  const location = getLocationInfo(locationKey);
  const localizedAmount = amount * location.priceMultiplier;
  
  // Format based on currency
  if (location.currency === 'JPY' || location.currency === 'KRW') {
    // These currencies typically don't use decimals
    return `${location.currencySymbol}${Math.round(localizedAmount).toLocaleString()}`;
  } else if (location.currency === 'INR') {
    // Indian numbering system
    return `${location.currencySymbol}${localizedAmount.toFixed(decimals)}`;
  } else {
    return `${location.currencySymbol}${localizedAmount.toFixed(decimals)}`;
  }
}

export function formatBudgetAmount(usdAmount: number, locationKey: string): string {
  const location = getLocationInfo(locationKey);
  const localizedAmount = usdAmount * location.priceMultiplier;
  
  // Format with proper thousand separators, no abbreviations
  if (location.currency === 'INR') {
    // Indian numbering system with commas
    return `${location.currencySymbol}${Math.round(localizedAmount).toLocaleString('en-IN')}`;
  }
  // Japanese Yen and Korean Won don't use decimals
  else if (location.currency === 'JPY' || location.currency === 'KRW') {
    return `${location.currencySymbol}${Math.round(localizedAmount).toLocaleString()}`;
  } 
  // Standard formatting for other currencies
  else {
    return `${location.currencySymbol}${Math.round(localizedAmount).toLocaleString()}`;
  }
}

export function generateLocalPhone(locationKey: string, type: 'office' | 'mobile' = 'office'): string {
  const location = getLocationInfo(locationKey);
  const format = location.phoneFormat;
  
  // Generate deterministic pseudo-digits based on location key and type (no Math.random)
  const digits = format.replace(/[^X]/g, '').length;
  const seed = locationKey.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  let number = '';
  for (let i = 0; i < digits; i++) {
    number += ((seed * 7 + i * 13 + (type === 'mobile' ? 3 : 1)) % 10).toString();
  }
  
  // Replace X's with random digits
  let phone = format;
  for (let i = 0; i < number.length; i++) {
    phone = phone.replace('X', number[i]);
  }
  
  return phone;
}

export function generateLocalEmail(vendorName: string, locationKey: string): string {
  const cleanName = vendorName.toLowerCase().replace(/[^a-z0-9]/g, '');
  // Deterministic domain selection based on vendor name hash (no Math.random)
  const domains = ['com', 'co', 'net', 'biz'];
  const nameHash = cleanName.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const domain = domains[nameHash % domains.length]; // eslint-disable-line @typescript-eslint/no-unused-vars
  
  // Use country-specific domain extensions
  const location = getLocationInfo(locationKey);
  let extension = 'com';
  
  if (locationKey === 'uk') extension = 'co.uk';
  else if (locationKey === 'canada') extension = 'ca';
  else if (locationKey === 'australia') extension = 'com.au';
  else if (locationKey === 'germany') extension = 'de';
  else if (locationKey === 'france') extension = 'fr';
  else if (locationKey === 'japan') extension = 'jp';
  else if (locationKey === 'china') extension = 'cn';
  else if (locationKey === 'india') extension = 'in';
  else if (locationKey === 'brazil') extension = 'com.br';
  else if (locationKey === 'mexico') extension = 'mx';
  else if (locationKey === 'south-africa') extension = 'co.za';
  
  return `contact@${cleanName}.${extension}`;
}

// Get currency info by code
export function getCurrencyInfo(currencyCode: string): CurrencyInfo {
  return currencies.find(c => c.code === currencyCode) || currencies[0];
}

// Format amount with custom currency
export function formatWithCurrency(usdAmount: number, currencyCode: string, decimals: number = 1): string {
  const currency = getCurrencyInfo(currencyCode);
  const localizedAmount = usdAmount * currency.conversionRate;

  // For small fractional amounts (< 1 000) keep decimal precision
  if (Math.abs(localizedAmount) < 1000) {
    if (currencyCode === 'JPY' || currencyCode === 'KRW' || currencyCode === 'NGN' || currencyCode === 'ARS') {
      return `${currency.symbol}${Math.round(localizedAmount).toLocaleString()}`;
    }
    return `${currency.symbol}${localizedAmount.toFixed(decimals)}`;
  }

  // Large numbers — always use comma-formatted integers (no K/M abbreviations)
  if (currencyCode === 'INR') {
    return `${currency.symbol}${Math.round(localizedAmount).toLocaleString('en-IN')}`;
  }
  return `${currency.symbol}${Math.round(localizedAmount).toLocaleString()}`;
}

// Format budget amount with custom currency
export function formatBudgetWithCurrency(usdAmount: number, currencyCode: string): string {
  const currency = getCurrencyInfo(currencyCode);
  const localizedAmount = usdAmount * currency.conversionRate;
  
  // Format with proper thousand separators, no abbreviations
  if (currencyCode === 'INR') {
    // Indian numbering system with commas
    return `${currency.symbol}${Math.round(localizedAmount).toLocaleString('en-IN')}`;
  }
  // Japanese Yen, Korean Won, and other currencies without decimals
  else if (currencyCode === 'JPY' || currencyCode === 'KRW' || currencyCode === 'NGN' || currencyCode === 'ARS') {
    return `${currency.symbol}${Math.round(localizedAmount).toLocaleString()}`;
  } 
  // Standard formatting for other currencies
  else {
    return `${currency.symbol}${Math.round(localizedAmount).toLocaleString()}`;
  }
}