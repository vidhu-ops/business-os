// @ts-nocheck
import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { FileText, DollarSign, MapPin, Coins, Loader2 } from 'lucide-react';
import { BusinessPlanResults } from './BusinessPlanResults';
import { generateBusinessPlan, BusinessPlanData, BusinessPlanFormData } from '../utils/businessPlanGenerator';
import { generateBusinessPlanWithGemini } from '../utils/businessPlanGemini';
import { isGeminiConfigured } from '../utils/geminiService';
import { currencies } from '../utils/locationData';

export function BusinessPlan() {
  const [planData, setPlanData] = useState<BusinessPlanData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState<BusinessPlanFormData>({
    businessIdea: '',
    targetRevenue: '',
    country: '',
    currency: 'USD'
  });
  const geminiConfigured = isGeminiConfigured();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.businessIdea || !formData.targetRevenue || !formData.country) {
      alert('Please fill in all fields');
      return;
    }

    setIsLoading(true);

    try {
      let plan;
      
      if (geminiConfigured) {
        try {
          console.log('🚀 Using Gemini API for business plan...');
          console.log('📋 Business Idea:', formData.businessIdea);
          console.log('🌍 Location:', formData.country);
          console.log('💰 Target Revenue:', formData.targetRevenue, formData.currency);
          
          const aiPlan = await generateBusinessPlanWithGemini(
            formData.businessIdea,
            formData.targetRevenue,
            formData.country,
            formData.currency
          );
          
          // Validate competitor data
          const competitorCount = aiPlan?.marketAnalysis?.competitiveAnalysis?.directCompetitors?.length || 0;
          console.log(`✅ Business plan generated with ${competitorCount} competitors`);
          
          if (competitorCount === 0) {
            console.warn('⚠️ WARNING: Business plan has no competitors in competitive analysis');
          } else {
            const competitorNames = aiPlan.marketAnalysis.competitiveAnalysis.directCompetitors
              .map((c: any) => c.name)
              .join(', ');
            console.log('🏢 Competitors found:', competitorNames);
          }
          
          // Convert AI plan to expected format
          plan = {
            businessIdea: formData.businessIdea,
            targetRevenue: formData.targetRevenue,
            country: formData.country,
            currency: formData.currency,
            ...aiPlan
          };
        } catch (apiError) {
          console.error('❌ Gemini API failed, falling back to mock data:', apiError);
          plan = generateBusinessPlan(formData);
        }
      } else {
        console.log('ℹ️ Gemini not configured, using mock data');
        plan = generateBusinessPlan(formData);
      }
      
      setPlanData(plan);
    } catch (error) {
      console.error('❌ Error generating business plan:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewPlan = () => {
    setPlanData(null);
    setFormData({
      businessIdea: '',
      targetRevenue: '',
      country: '',
      currency: 'USD'
    });
  };

  if (planData) {
    return <BusinessPlanResults data={planData} onNewPlan={handleNewPlan} />;
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Card className="shadow-xl bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300">
        <CardHeader className="border-b border-gray-200 dark:border-zinc-800 transition-colors duration-300">
          <div className="flex items-center gap-2 sm:gap-3">
            <FileText className="w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8 text-[#FF5733]" />
            <div>
              <CardTitle className="text-gray-900 dark:text-white text-xl sm:text-2xl md:text-3xl font-serif transition-colors duration-300">Business Plan Generator</CardTitle>
              <p className="text-gray-600 dark:text-zinc-400 text-xs sm:text-sm mt-1 transition-colors duration-300">
                Create a comprehensive business plan tailored to your market
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-4 sm:p-6 md:p-8 bg-white dark:bg-zinc-900 transition-colors duration-300">
          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
            {/* Business Idea */}
            <div className="space-y-2">
              <Label htmlFor="businessIdea" className="text-sm sm:text-base flex items-center gap-2 text-gray-900 dark:text-white transition-colors duration-300">
                <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-[#FF5733]" />
                Business Idea
              </Label>
              <Textarea
                id="businessIdea"
                placeholder="Describe your business idea in detail. For example: 'A subscription-based meal planning app that uses AI to create personalized weekly meal plans based on dietary preferences, budget, and local grocery store availability. The app will also provide shopping lists and step-by-step cooking instructions...'"
                value={formData.businessIdea}
                onChange={(e) => setFormData({ ...formData, businessIdea: e.target.value })}
                className="min-h-[120px] sm:min-h-[150px] text-sm sm:text-base bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white placeholder:text-gray-500 dark:placeholder:text-zinc-500 transition-colors duration-300"
                required
              />
              <p className="text-xs sm:text-sm text-gray-500 dark:text-zinc-500 transition-colors duration-300">
                Be specific about what you're selling, who your customers are, and how you'll make money
              </p>
            </div>

            {/* Target Revenue */}
            <div className="space-y-2">
              <Label htmlFor="targetRevenue" className="text-sm sm:text-base flex items-center gap-2 text-gray-900 dark:text-white transition-colors duration-300">
                <DollarSign className="w-4 h-4 sm:w-5 sm:h-5 text-[#FF5733]" />
                Target Annual Revenue (Year 3)
              </Label>
              <Input
                id="targetRevenue"
                type="number"
                placeholder="1000000"
                value={formData.targetRevenue}
                onChange={(e) => setFormData({ ...formData, targetRevenue: e.target.value })}
                className="text-sm sm:text-base bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white placeholder:text-gray-500 dark:placeholder:text-zinc-500 transition-colors duration-300"
                required
                min="0"
                step="1000"
              />
              <p className="text-xs sm:text-sm text-gray-500 dark:text-zinc-500 transition-colors duration-300">
                Enter your revenue goal for year 3 in numbers (e.g., 1000000 for 1 million)
              </p>
            </div>

            {/* Country/Location */}
            <div className="space-y-2">
              <Label htmlFor="country" className="text-sm sm:text-base flex items-center gap-2 text-gray-900 dark:text-white transition-colors duration-300">
                <MapPin className="w-4 h-4 sm:w-5 sm:h-5 text-[#FF5733]" />
                Country/Location
              </Label>
              <Select
                value={formData.country}
                onValueChange={(value) => setFormData({ ...formData, country: value })}
                required
              >
                <SelectTrigger className="text-sm sm:text-base bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white transition-colors duration-300">
                  <SelectValue placeholder="Select your country" />
                </SelectTrigger>
                <SelectContent className="bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white transition-colors duration-300">
                  <SelectItem value="United States">United States</SelectItem>
                  <SelectItem value="United Kingdom">United Kingdom</SelectItem>
                  <SelectItem value="Canada">Canada</SelectItem>
                  <SelectItem value="Australia">Australia</SelectItem>
                  <SelectItem value="Germany">Germany</SelectItem>
                  <SelectItem value="France">France</SelectItem>
                  <SelectItem value="Japan">Japan</SelectItem>
                  <SelectItem value="China">China</SelectItem>
                  <SelectItem value="India">India</SelectItem>
                  <SelectItem value="Brazil">Brazil</SelectItem>
                  <SelectItem value="Mexico">Mexico</SelectItem>
                  <SelectItem value="Singapore">Singapore</SelectItem>
                  <SelectItem value="UAE">United Arab Emirates</SelectItem>
                  <SelectItem value="South Korea">South Korea</SelectItem>
                  <SelectItem value="Netherlands">Netherlands</SelectItem>
                  <SelectItem value="Spain">Spain</SelectItem>
                  <SelectItem value="Italy">Italy</SelectItem>
                  <SelectItem value="Switzerland">Switzerland</SelectItem>
                  <SelectItem value="Sweden">Sweden</SelectItem>
                  <SelectItem value="Norway">Norway</SelectItem>
                  <SelectItem value="Denmark">Denmark</SelectItem>
                  <SelectItem value="Ireland">Ireland</SelectItem>
                  <SelectItem value="New Zealand">New Zealand</SelectItem>
                  <SelectItem value="South Africa">South Africa</SelectItem>
                  <SelectItem value="Israel">Israel</SelectItem>
                  <SelectItem value="Poland">Poland</SelectItem>
                  <SelectItem value="Turkey">Turkey</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-zinc-500 transition-colors duration-300">
                The plan will use location-specific economic data, tax rates, and market conditions
              </p>
            </div>

            {/* Currency */}
            <div className="space-y-2">
              <Label htmlFor="currency" className="text-sm sm:text-base flex items-center gap-2 text-gray-900 dark:text-white transition-colors duration-300">
                <Coins className="w-4 h-4 sm:w-5 sm:h-5 text-[#FF5733]" />
                Currency
              </Label>
              <Select
                value={formData.currency}
                onValueChange={(value) => setFormData({ ...formData, currency: value })}
                required
              >
                <SelectTrigger className="text-sm sm:text-base bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white transition-colors duration-300">
                  <SelectValue placeholder="Select your currency" />
                </SelectTrigger>
                <SelectContent className="bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white transition-colors duration-300">
                  {currencies.map((currency) => (
                    <SelectItem key={currency.code} value={currency.code}>
                      {currency.name} ({currency.code})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-zinc-500 transition-colors duration-300">
                All financial projections will be displayed in this currency
              </p>
            </div>

            {geminiConfigured && (
              <div className="p-3 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg">
                <p className="text-xs text-green-800 dark:text-green-200">
                  ✓ Research-backed analysis enabled - Using real market data and verified company information
                </p>
              </div>
            )}

            <Button
              type="submit"
              size="lg"
              className="w-full bg-[#FF5733] hover:bg-[#FF5733]/90 text-white text-lg py-6"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Generating Business Plan...
                </>
              ) : (
                <>
                  <FileText className="w-5 h-5 mr-2" />
                  Generate Business Plan
                </>
              )}
            </Button>
          </form>

          <div className="mt-8 p-4 bg-gray-100 dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-lg transition-colors duration-300">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2 transition-colors duration-300">Your business plan will include:</h3>
            <ul className="text-sm text-gray-700 dark:text-zinc-300 space-y-1 transition-colors duration-300">
              <li>✓ Executive Summary with financial highlights</li>
              <li>✓ Comprehensive Market Analysis with competitor research</li>
              <li>✓ Organization & Management structure</li>
              <li>✓ Products/Services description with pricing strategy</li>
              <li>✓ Marketing & Sales strategy with ROI projections</li>
              <li>✓ Operations Plan with supplier and facility details</li>
              <li>✓ 3-Year Financial Projections with location-specific tax rates</li>
              <li>✓ Risk Analysis & Contingency Planning</li>
              <li>✓ Implementation Timeline with milestones</li>
              <li>✓ Exit Strategy options and valuations</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}