// @ts-nocheck
import { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Calendar, DollarSign, MapPin, Target, Sparkles, Coins, Brain, Search, ClipboardList, CheckCircle2, Loader2 } from 'lucide-react';
import { ActionPlan } from './ActionPlan';
import { generateActionPlan, PlanData } from '../utils/planGenerator';
import { currencies, formatBudgetWithCurrency } from '../utils/locationData';

interface PlanItOutProps {
  onSwitchToResearch: () => void;
}

export function PlanItOut({ onSwitchToResearch }: PlanItOutProps) {
  const [planData, setPlanData] = useState<PlanData | null>(null);
  const [formData, setFormData] = useState({
    need: '',
    timeline: '',
    budget: '',
    area: '',
    currency: 'USD'
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingStage, setLoadingStage] = useState<string>('');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Elapsed-time ticker while generating
  useEffect(() => {
    if (isGenerating) {
      setElapsedSeconds(0);
      timerRef.current = setInterval(() => setElapsedSeconds(s => s + 1), 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [isGenerating]);

  // FIX #8: Budget range `value` now uses the same formatted string as `label` —
  // previously the `value` hardcoded `$` and abbreviated numbers (1K, 1M) regardless
  // of the user's selected currency, corrupting the prompt sent to Gemini.
  const getBudgetRanges = () => {
    const currencyCode = formData.currency;
    const ranges = [
      { low: null,      high: 10000   },
      { low: 10000,     high: 50000   },
      { low: 50000,     high: 100000  },
      { low: 100000,    high: 500000  },
      { low: 500000,    high: 1000000 },
      { low: 1000000,   high: 5000000 },
      { low: 5000000,   high: null    },
    ];
    return ranges.map(({ low, high }) => {
      const label = low === null
        ? `Under ${formatBudgetWithCurrency(high!, currencyCode)}`
        : high === null
          ? `${formatBudgetWithCurrency(low, currencyCode)}+`
          : `${formatBudgetWithCurrency(low, currencyCode)} - ${formatBudgetWithCurrency(high, currencyCode)}`;
      // value === label so the full currency-correct string reaches the Gemini prompt
      return { value: label, label };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.need || !formData.timeline || !formData.budget || !formData.area) {
      alert('Please fill in all fields');
      return;
    }

    setIsGenerating(true);
    setLoadingStage('analyzing');
    try {
      const plan = await generateActionPlan(formData, (stage) => {
        setLoadingStage(stage);
      });
      setPlanData(plan);
    } catch (error: any) {
      console.error('Error generating plan:', error);
      alert('An error occurred while generating your plan. Please check the console for details and try again.');
    } finally {
      setIsGenerating(false);
      setLoadingStage('');
    }
  };

  const handleNewPlan = () => {
    setPlanData(null);
    setFormData({
      need: '',
      timeline: '',
      budget: '',
      area: '',
      currency: 'USD'
    });
  };

  if (planData) {
    return <ActionPlan data={planData} onNewPlan={handleNewPlan} onSwitchToResearch={onSwitchToResearch} />;
  }

  // ── Loading stages config ──────────────────────────────────────────────────
  const stages = [
    {
      key: 'analyzing',
      icon: Brain,
      title: 'Thinking deeply about your idea…',
      subtitle: 'Analyzing industry, viability, location fit, critical path, and regulatory requirements',
      color: 'text-violet-400',
      bg: 'bg-violet-500/10 border-violet-500/30',
      dot: 'bg-violet-400',
    },
    {
      key: 'researching',
      icon: Search,
      title: 'Researching real market data…',
      subtitle: 'Using Google Search to find real vendors, current pricing, and local regulations in ' + formData.area,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/30',
      dot: 'bg-blue-400',
    },
    {
      key: 'finalizing',
      icon: ClipboardList,
      title: 'Building your action plan…',
      subtitle: 'Assembling all sections into a cohesive, location-specific plan',
      color: 'text-[#FF5733]',
      bg: 'bg-[#FF5733]/10 border-[#FF5733]/30',
      dot: 'bg-[#FF5733]',
    },
  ];

  const currentStageIdx = stages.findIndex(s => s.key === loadingStage);
  const currentStage = stages[currentStageIdx] ?? stages[0];
  const StageIcon = currentStage.icon;

  // Render loading overlay when generating
  if (isGenerating) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card className="shadow-xl bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300">
          <CardContent className="p-8 md:p-12">
            {/* Main animated status */}
            <div className={`rounded-2xl border-2 p-6 mb-6 transition-all duration-700 ${currentStage.bg}`}>
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 mt-0.5">
                  <div className="relative">
                    <StageIcon className={`w-8 h-8 ${currentStage.color}`} />
                    {/* Pulsing ring */}
                    <span className={`absolute -inset-1 rounded-full opacity-30 animate-ping ${currentStage.dot}`} />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`font-bold text-lg ${currentStage.color}`}>{currentStage.title}</p>
                  <p className="text-gray-500 dark:text-zinc-400 text-sm mt-1 leading-relaxed">{currentStage.subtitle}</p>
                </div>
                <div className="flex-shrink-0 text-right">
                  <p className="text-gray-400 dark:text-zinc-500 text-xs font-mono">{elapsedSeconds}s</p>
                </div>
              </div>

              {/* Progress dots */}
              <div className="flex items-center gap-3 mt-5 pl-12">
                {[0, 1, 2, 3, 4].map(i => (
                  <div
                    key={i}
                    className={`rounded-full transition-all duration-300 ${currentStage.dot} ${
                      i <= (elapsedSeconds % 5) ? 'opacity-100' : 'opacity-20'
                    } w-2 h-2`}
                  />
                ))}
                <span className="text-xs text-gray-400 dark:text-zinc-500 ml-1">Processing…</span>
              </div>
            </div>

            {/* Stage progress tracker */}
            <div className="space-y-3 mb-6">
              {stages.map((stage, idx) => {
                const SIcon = stage.icon;
                const isDone = idx < currentStageIdx;
                const isCurrent = idx === currentStageIdx;
                const isPending = idx > currentStageIdx;
                return (
                  <div
                    key={stage.key}
                    className={`flex items-center gap-3 p-3 rounded-xl border transition-all duration-500 ${
                      isDone
                        ? 'bg-green-500/10 border-green-500/30'
                        : isCurrent
                          ? stage.bg
                          : 'bg-gray-50 dark:bg-zinc-800/50 border-gray-200 dark:border-zinc-700/50 opacity-50'
                    }`}
                  >
                    <div className="flex-shrink-0">
                      {isDone ? (
                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                      ) : isCurrent ? (
                        <Loader2 className={`w-5 h-5 ${stage.color} animate-spin`} />
                      ) : (
                        <SIcon className="w-5 h-5 text-gray-400 dark:text-zinc-500" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className={`text-sm font-semibold ${
                        isDone ? 'text-green-600 dark:text-green-400' :
                        isCurrent ? stage.color :
                        'text-gray-400 dark:text-zinc-500'
                      }`}>
                        {isDone ? `✓ ${stage.title.replace('…', ' — Done')}` : stage.title}
                      </p>
                    </div>
                    {isDone && (
                      <span className="text-xs text-green-600 dark:text-green-400 font-medium">Complete</span>
                    )}
                    {isCurrent && (
                      <span className={`text-xs font-medium ${stage.color}`}>In progress</span>
                    )}
                    {isPending && (
                      <span className="text-xs text-gray-400 dark:text-zinc-500">Pending</span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Info block */}
            <div className="bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-xl p-4">
              <p className="text-xs text-gray-500 dark:text-zinc-400 text-center leading-relaxed">
                <strong className="text-gray-700 dark:text-zinc-300">Why does this take time?</strong>
                {' '}Unlike instant template-based tools, this performs deep strategic analysis of your specific idea, 
                then uses live Google Search to find real vendors, actual pricing, and current regulations 
                in <strong className="text-[#FF5733]">{formData.area}</strong> — before writing a single word of your plan.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Card className="shadow-xl bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300">
        <CardHeader className="border-b border-gray-200 dark:border-zinc-800 transition-colors duration-300">
          <div className="flex items-center gap-2 sm:gap-3">
            <Sparkles className="w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8 text-[#FF5733]" />
            <div>
              <CardTitle className="text-gray-900 dark:text-white text-xl sm:text-2xl md:text-3xl font-serif transition-colors duration-300">Plan It Out</CardTitle>
              <p className="text-gray-600 dark:text-zinc-400 text-xs sm:text-sm mt-1 transition-colors duration-300">
                Get a detailed action plan with steps and local vendors
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-4 sm:p-6 md:p-8 bg-white dark:bg-zinc-900 transition-colors duration-300">
          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
            {/* Need/Goal */}
            <div className="space-y-2">
              <Label htmlFor="need" className="text-sm sm:text-base flex items-center gap-2 text-gray-900 dark:text-white">
                <Target className="w-4 h-4 sm:w-5 sm:h-5 text-[#FF5733]" />
                What do you need to accomplish?
              </Label>
              <Textarea
                id="need"
                placeholder="E.g., Launch a new coffee shop, Start a tech startup, Expand manufacturing operations, Open a retail store..."
                value={formData.need}
                onChange={(e) => setFormData({ ...formData, need: e.target.value })}
                className="min-h-[80px] sm:min-h-[100px] text-sm sm:text-base bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white placeholder:text-gray-500 dark:placeholder:text-zinc-500"
                required
              />
              <p className="text-xs sm:text-sm text-gray-500 dark:text-zinc-500">
                Describe your business goal or project need in detail
              </p>
            </div>

            {/* Timeline */}
            <div className="space-y-2">
              <Label htmlFor="timeline" className="text-sm sm:text-base flex items-center gap-2 text-gray-900 dark:text-white">
                <Calendar className="w-4 h-4 sm:w-5 sm:h-5 text-[#FF5733]" />
                Timeline
              </Label>
              <Select
                value={formData.timeline}
                onValueChange={(value) => setFormData({ ...formData, timeline: value })}
                required
              >
                <SelectTrigger className="text-sm sm:text-base bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white">
                  <SelectValue placeholder="Select your target timeline" />
                </SelectTrigger>
                <SelectContent className="bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white">
                  <SelectItem value="1-3 months">1-3 Months</SelectItem>
                  <SelectItem value="3-6 months">3-6 Months</SelectItem>
                  <SelectItem value="6-12 months">6-12 Months</SelectItem>
                  <SelectItem value="1-2 years">1-2 Years</SelectItem>
                  <SelectItem value="2+ years">2+ Years</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Currency */}
            <div className="space-y-2">
              <Label htmlFor="currency" className="text-sm sm:text-base flex items-center gap-2 text-gray-900 dark:text-white">
                <Coins className="w-4 h-4 sm:w-5 sm:h-5 text-[#FF5733]" />
                Currency
              </Label>
              <Select
                value={formData.currency}
                onValueChange={(value) => setFormData({ ...formData, currency: value, budget: '' })}
                required
              >
                <SelectTrigger className="text-sm sm:text-base bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white">
                  <SelectValue placeholder="Select your currency" />
                </SelectTrigger>
                <SelectContent className="bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white">
                  {currencies.map((currency) => (
                    <SelectItem key={currency.code} value={currency.code}>
                      {currency.name} ({currency.code})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Budget */}
            <div className="space-y-2">
              <Label htmlFor="budget" className="text-sm sm:text-base flex items-center gap-2 text-gray-900 dark:text-white">
                <DollarSign className="w-4 h-4 sm:w-5 sm:h-5 text-[#FF5733]" />
                Budget Range
              </Label>
              <Select
                value={formData.budget}
                onValueChange={(value) => setFormData({ ...formData, budget: value })}
                required
              >
                <SelectTrigger className="text-sm sm:text-base bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white">
                  <SelectValue placeholder="Select your budget range" />
                </SelectTrigger>
                <SelectContent className="bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white">
                  {getBudgetRanges().map((range) => (
                    <SelectItem key={range.value} value={range.value}>
                      {range.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Location/Area */}
            <div className="space-y-2">
              <Label htmlFor="area" className="text-sm sm:text-base flex items-center gap-2 text-gray-900 dark:text-white">
                <MapPin className="w-4 h-4 sm:w-5 sm:h-5 text-[#FF5733]" />
                Location/Area
              </Label>
              <Select
                value={formData.area}
                onValueChange={(value) => setFormData({ ...formData, area: value })}
                required
              >
                <SelectTrigger className="text-sm sm:text-base bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white">
                  <SelectValue placeholder="Select your location" />
                </SelectTrigger>
                <SelectContent className="bg-gray-100 dark:bg-zinc-800 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white">
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
            </div>

            <Button
              type="submit"
              size="lg"
              className="w-full bg-[#FF5733] hover:bg-[#FF5733]/90 text-white text-lg py-6"
              disabled={isGenerating}
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Generate Action Plan
            </Button>
          </form>

          
        </CardContent>
      </Card>
    </div>
  );
}