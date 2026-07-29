// @ts-nocheck
import { PlanData } from '../utils/planGenerator';
import { getLocationInfo, getLocationKey, getCurrencyInfo, formatBudgetWithCurrency } from '../utils/locationData';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Checkbox } from './ui/checkbox';
import { useState } from 'react';
import { 
  ArrowLeft, 
  Download, 
  MapPin, 
  Calendar, 
  DollarSign, 
  Target, 
  CheckCircle2, 
  Clock, 
  Lightbulb, 
  FileText, 
  Building2, 
  Package, 
  Phone, 
  Mail, 
  Globe, 
  Banknote, 
  TrendingUp, 
  AlertTriangle, 
  Users, 
  ClipboardCheck, 
  Scale,
  Share2,
  ExternalLink
} from 'lucide-react';
import { 
  ComposedChart, 
  LineChart, 
  Line, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { toast } from 'sonner';
import { downloadActionPlan } from '../utils/pdfGenerator';

interface ActionPlanProps {
  data: PlanData;
  onNewPlan: () => void;
  onSwitchToResearch: () => void;
}

export function ActionPlan({ data, onNewPlan, onSwitchToResearch }: ActionPlanProps) {
  const locationKey = getLocationKey(data.area);
  const locationInfo = getLocationInfo(locationKey);
  const currencyInfo = getCurrencyInfo(data.currency);
  
  // State for managing checklist items
  const [checklistItems, setChecklistItems] = useState<Record<string, boolean>>({});
  
  // Generate checklist items from action steps
  const generateChecklistItems = () => {
    const items: Record<string, boolean> = {};
    // Add null guards for when API fails or returns partial data
    if (!data?.actionSteps || !Array.isArray(data.actionSteps)) {
      return items;
    }
    data.actionSteps.forEach((step, stepIndex) => {
      // Guard against missing detailedTasks
      if (!step?.detailedTasks || !Array.isArray(step.detailedTasks)) {
        return;
      }
      step.detailedTasks.forEach((task, taskIndex) => {
        const key = `${stepIndex}-${taskIndex}`;
        items[key] = checklistItems[key] || false;
      });
    });
    return items;
  };

  // Initialize checklist items on first render
  const [isChecklistInitialized, setIsChecklistInitialized] = useState(false);
  if (!isChecklistInitialized) {
    setChecklistItems(generateChecklistItems());
    setIsChecklistInitialized(true);
  }

  // Toggle checklist item
  const toggleChecklistItem = (key: string) => {
    setChecklistItems((prev) => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Calculate progress
  const calculateProgress = () => {
    const total = Object.keys(checklistItems).length;
    const completed = Object.values(checklistItems).filter(Boolean).length;
    return { completed, total, percentage: total > 0 ? Math.round((completed / total) * 100) : 0 };
  };
  
  const handleDownload = async () => {
    await downloadActionPlan(data.need, data.area);
  };

  // Save checklist and generate shareable link
  const handleSaveChecklist = () => {
    // Generate unique ID
    const checklistId = `plan_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Save to localStorage
    localStorage.setItem(`checklist_${checklistId}`, JSON.stringify({
      plan: data,
      items: checklistItems
    }));
    
    // Generate shareable URL
    const checklistUrl = `${window.location.origin}/checklist?id=${checklistId}`;
    
    // Try native share if available, otherwise copy to clipboard
    if (navigator.share) {
      navigator.share({
        title: `Action Plan Checklist: ${data.need}`,
        text: 'Track your progress on this action plan. Add it to your home screen for quick access!',
        url: checklistUrl
      }).then(() => {
        toast.success('Checklist link shared successfully!');
      }).catch((error) => {
        if (error.name !== 'AbortError') {
          copyToClipboard(checklistUrl);
        }
      });
    } else {
      copyToClipboard(checklistUrl);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Checklist link copied! Open it in your browser and add to home screen.');
  };

  return (
    <div className="min-h-screen bg-white dark:bg-black space-y-4 sm:space-y-6 p-2 sm:p-6 transition-colors duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 print:hidden">
        <div className="flex items-center gap-3">
          
         
        </div>
        
        <Button onClick={handleDownload} className="text-sm sm:text-base bg-[#FF5733] hover:bg-[#FF5733]/90">
          <Download className="w-4 h-4 mr-2" />
          Download Plan
        </Button>
      </div>

      <div data-pdf-content>
      <Card className="shadow-xl bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300">
        <CardHeader className="border-b border-gray-200 dark:border-zinc-800 transition-colors duration-300">
          <div className="space-y-2">
            <CardTitle className="text-gray-900 dark:text-white text-xl sm:text-2xl md:text-3xl leading-tight break-words font-serif transition-colors duration-300">Action Plan: {data.need}</CardTitle>
            <div className="flex items-center gap-2 sm:gap-3 text-gray-600 dark:text-zinc-400 text-xs sm:text-sm flex-wrap transition-colors duration-300">
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3 sm:w-4 sm:h-4" />
                Timeline: {data.timeline}
              </span>
              <span className="flex items-center gap-1">
                <DollarSign className="w-3 h-3 sm:w-4 sm:h-4" />
                Budget: {data.budget}
              </span>
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3 sm:w-4 sm:h-4" />
                {data.area}
              </span>
              <Badge variant="secondary" className="bg-[#FF5733] text-white hover:bg-[#FF5733]/90 text-xs">
                Generated: {data.generatedDate}
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-4 sm:p-6 md:p-8 space-y-8 sm:space-y-12 bg-white dark:bg-zinc-900 transition-colors duration-300">
          {/* Table of Contents / Index */}
          <section className="bg-gradient-to-br from-zinc-800 to-zinc-900 p-6 rounded-lg border-2 border-[#FF5733] print:break-inside-avoid">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-[#FF5733] rounded-lg">
                <ClipboardCheck className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-white text-2xl font-serif">Action Plan Index</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h3 className="text-[#FF5733] font-bold text-sm uppercase tracking-wide mb-3">Plan Overview</h3>
                <a href="#location-info" className="flex items-center gap-2 text-zinc-300 hover:text-[#FF5733] transition-colors py-1 text-sm group">
                  <span className="text-[#FF5733] group-hover:translate-x-1 transition-transform">→</span>
                  <span>Location-Specific Information</span>
                </a>
                <a href="#executive-summary" className="flex items-center gap-2 text-zinc-300 hover:text-[#FF5733] transition-colors py-1 text-sm group">
                  <span className="text-[#FF5733] group-hover:translate-x-1 transition-transform">→</span>
                  <span>Executive Summary</span>
                </a>
                <a href="#budget-breakdown" className="flex items-center gap-2 text-zinc-300 hover:text-[#FF5733] transition-colors py-1 text-sm group">
                  <span className="text-[#FF5733] group-hover:translate-x-1 transition-transform">→</span>
                  <span>Budget Breakdown & Analysis</span>
                </a>
              </div>
              <div className="space-y-2">
                <h3 className="text-[#FF5733] font-bold text-sm uppercase tracking-wide mb-3">Implementation</h3>
                <a href="#action-steps" className="flex items-center gap-2 text-zinc-300 hover:text-[#FF5733] transition-colors py-1 text-sm group">
                  <span className="text-[#FF5733] group-hover:translate-x-1 transition-transform">→</span>
                  <span>Detailed Action Steps ({data.actionSteps?.length || 0} steps)</span>
                </a>
                <a href="#risk-assessment" className="flex items-center gap-2 text-zinc-300 hover:text-[#FF5733] transition-colors py-1 text-sm group">
                  <span className="text-[#FF5733] group-hover:translate-x-1 transition-transform">→</span>
                  <span>Risk Assessment & Mitigation</span>
                </a>
                <a href="#success-metrics" className="flex items-center gap-2 text-zinc-300 hover:text-[#FF5733] transition-colors py-1 text-sm group">
                  <span className="text-[#FF5733] group-hover:translate-x-1 transition-transform">→</span>
                  <span>Success Metrics & KPIs</span>
                </a>
              </div>
            </div>
            <div className="mt-6 p-4 bg-black/40 rounded-lg border border-zinc-700">
              <p className="text-xs text-zinc-400 leading-relaxed">
                <strong className="text-white">Quick Navigation:</strong> Click any section above to jump directly to that part of your action plan. 
                This comprehensive plan includes {data.actionSteps?.length || 0} detailed steps with local vendors, budget allocations, and success metrics.
              </p>
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Location-Specific Information */}
          <section id="location-info" className="bg-gray-100 dark:bg-zinc-800 p-4 sm:p-6 rounded-lg border border-gray-300 dark:border-zinc-700 scroll-mt-20 transition-colors duration-300">
            <div className="flex items-center gap-2 mb-3 sm:mb-4">
              <MapPin className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733] flex-shrink-0" />
              <h2 className="text-gray-900 dark:text-white text-lg sm:text-xl md:text-2xl leading-tight font-serif transition-colors duration-300">Location-Specific Market Information</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
              <div className="bg-white dark:bg-zinc-900 p-3 sm:p-4 rounded-lg shadow-sm border border-[#FF5733] transition-colors duration-300">
                <p className="text-xs sm:text-sm text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Selected Currency</p>
                <p className="text-lg sm:text-xl font-bold text-[#FF5733] break-words">{data.currency} ({currencyInfo.symbol})</p>
                <p className="text-xs text-gray-500 dark:text-zinc-500 mt-1 transition-colors duration-300">All amounts shown in this currency</p>
              </div>
              <div className="bg-white dark:bg-zinc-900 p-3 sm:p-4 rounded-lg shadow-sm border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                <p className="text-xs sm:text-sm text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Location</p>
                <p className="text-base sm:text-lg font-bold text-gray-900 dark:text-white break-words transition-colors duration-300">{locationInfo.name}</p>
              </div>
              
              <div className="bg-white dark:bg-zinc-900 p-4 rounded-lg shadow-sm border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                <p className="text-sm text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Tax Rate</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white transition-colors duration-300">{locationInfo.taxRate}</p>
              </div>
              <div className="bg-white dark:bg-zinc-900 p-4 rounded-lg shadow-sm border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                <p className="text-sm text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Time Zone</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white transition-colors duration-300">{locationInfo.timezone}</p>
              </div>
              <div className="bg-white dark:bg-zinc-900 p-4 rounded-lg shadow-sm border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                <p className="text-sm text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Business Hours</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white transition-colors duration-300">{locationInfo.businessHours}</p>
              </div>
              <div className="bg-white dark:bg-zinc-900 p-4 rounded-lg shadow-sm border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                <p className="text-sm text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Phone Prefix</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white transition-colors duration-300">{locationInfo.phonePrefix}</p>
              </div>
              <div className="bg-white dark:bg-zinc-900 p-4 rounded-lg shadow-sm col-span-2 border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                <p className="text-sm text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Region Details</p>
                <p className="text-sm text-gray-700 dark:text-zinc-300 transition-colors duration-300">Labor cost: {(locationInfo.laborCostMultiplier * 100).toFixed(0)}% of US baseline | Real estate: {(locationInfo.realEstateMultiplier * 100).toFixed(0)}% of US baseline</p>
              </div>
            </div>
            <div className="mt-4 p-4 bg-white dark:bg-zinc-900 border border-gray-300 dark:border-zinc-700 rounded transition-colors duration-300">
              <p className="text-sm text-gray-700 dark:text-zinc-300 transition-colors duration-300">
                <strong className="text-[#FF5733]">Note:</strong> All pricing, vendor contacts, and recommendations in this plan are specific to {locationInfo.name}. 
                All monetary values are displayed in {data.currency} ({currencyInfo.symbol}). Contact information uses local formats with {locationInfo.phonePrefix} phone prefix.
              </p>
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Executive Summary */}
          <section id="executive-summary" className="scroll-mt-10">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1">
                <Target className="w-10 h-6 text-[#FF5733]" />
                <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">Executive Summary</h2>
              </div>
              
            </div>
            <div className="bg-gray-100 dark:bg-zinc-800 p-1 rounded-lg border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
              <p className="text-gray-700 dark:text-zinc-300 leading-relaxed transition-colors duration-300">{data.summary}</p>
            </div>
            <div className="mt-2 p-1 bg-gray-100 dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-lg print:hidden transition-colors duration-300">
              <p className="text-sm text-gray-700 dark:text-zinc-300 transition-colors duration-300">
                <strong className="text-[#FF5733]">💡 Pro Tip:</strong>"Research This Market" to generate a comprehensive business intelligence report with market size, competitive analysis, financial projections, and industry trends for {data.need} in {data.area}. This will provide detailed market research to complement your action plan.
              </p>
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Budget Breakdown */}
          <section id="budget-breakdown" className="scroll-mt-20">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-6 h-6 text-[#FF5733]" />
              <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">Budget Allocation & Breakdown</h2>
            </div>
            <div className="space-y-4">
              {(data.budgetBreakdown || []).map((item, index) => (
                <Card key={index} className="border-l-4 border-[#FF5733] bg-white dark:bg-zinc-900 transition-colors duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-bold text-lg text-gray-900 dark:text-white transition-colors duration-300">{item.category}</h3>
                        <p className="text-sm text-gray-600 dark:text-zinc-400 mt-1 transition-colors duration-300">{item.description}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-[#FF5733]">{item.amount}</div>
                        <Badge 
                          variant={item.priority === 'High' ? 'default' : 'secondary'}
                          className={item.priority === 'High' ? 'bg-red-600' : item.priority === 'Medium' ? 'bg-orange-500' : 'bg-green-600'}
                        >
                          {item.priority} Priority
                        </Badge>
                      </div>
                    </div>
                    <div className="bg-gray-100 dark:bg-zinc-800 p-4 rounded border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                      <p className="text-xs font-semibold text-gray-700 dark:text-zinc-300 mb-2 transition-colors duration-300">Specific Line Items:</p>
                      <ul className="list-disc list-inside text-sm text-gray-600 dark:text-zinc-400 space-y-1 transition-colors duration-300">
                        {(item.specificItems || []).map((specificItem, idx) => (
                          <li key={idx}>{specificItem}</li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Detailed Action Steps */}
          <section id="action-steps" className="scroll-mt-20">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-6 h-6 text-[#FF5733]" />
                <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">Detailed Action Steps with Alternatives</h2>
              </div>
              
              {/* Create Checklist Dialog */}
              <Dialog>
                <DialogTrigger asChild>
                  <Button className="bg-[#FF5733] hover:bg-[#FF5733]/90 print:hidden">
                    <ClipboardCheck className="w-4 h-4 mr-2" />
                    Create Checklist
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                  <DialogHeader>
                    <DialogTitle className="text-2xl font-bold text-[#FF5733] flex items-center gap-2">
                      <ClipboardCheck className="w-7 h-7" />
                      Complete Project Checklist
                    </DialogTitle>
                    <DialogDescription className="text-base text-gray-700 dark:text-zinc-300 transition-colors duration-300">
                      Track all tasks from your action plan. Check off items as you complete them. Progress is saved in your session.
                    </DialogDescription>
                  </DialogHeader>
                  
                  {/* Progress Bar */}
                  {(() => {
                    const progress = calculateProgress();
                    return (
                      <div className="mb-6 p-4 bg-gray-100 dark:bg-zinc-800 rounded-lg border-2 border-[#FF5733] transition-colors duration-300">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-semibold text-gray-900 dark:text-white transition-colors duration-300">Overall Progress</span>
                          <span className="text-lg font-bold text-[#FF5733]">{progress.completed} / {progress.total} tasks</span>
                        </div>
                        <div className="w-full bg-gray-300 dark:bg-zinc-700 rounded-full h-4 overflow-hidden transition-colors duration-300">
                          <div 
                            className="h-full bg-gradient-to-r from-green-500 to-emerald-600 transition-all duration-500 ease-out flex items-center justify-end pr-2"
                            style={{ width: `${progress.percentage}%` }}
                          >
                            {progress.percentage > 10 && (
                              <span className="text-xs font-bold text-white">{progress.percentage}%</span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Checklist by Phase */}
                  <div className="space-y-6">
                    {(data.actionSteps || []).map((step, stepIndex) => (
                      <Card key={stepIndex} className="border-l-4 border-[#FF5733] bg-gray-100 dark:bg-zinc-800 transition-colors duration-300">
                        <CardHeader className="bg-white dark:bg-zinc-900 pb-3 transition-colors duration-300">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[#FF5733] text-white flex items-center justify-center font-bold text-sm">
                              {stepIndex + 1}
                            </div>
                            <div className="flex-1">
                              <CardTitle className="text-lg text-gray-900 dark:text-white transition-colors duration-300">{step.phase}</CardTitle>
                              <div className="flex items-center gap-3 mt-2 text-xs text-gray-600 dark:text-zinc-400 transition-colors duration-300">
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  {step.duration}
                                </span>
                                <span className="flex items-center gap-1">
                                  <DollarSign className="w-3 h-3" />
                                  {step.estimatedCost}
                                </span>
                              </div>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="pt-4 bg-gray-100 dark:bg-zinc-800 transition-colors duration-300">
                          <div className="space-y-3">
                            {(step.detailedTasks || []).map((task, taskIndex) => {
                              const key = `${stepIndex}-${taskIndex}`;
                              const isChecked = checklistItems[key] || false;
                              
                              return (
                                <div
                                  key={taskIndex}
                                  className={`flex items-start gap-3 p-3 rounded-lg border-2 transition-all ${
                                    isChecked
                                      ? 'bg-green-900/30 border-green-600'
                                      : 'bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-700 hover:border-[#FF5733]'
                                  }`}
                                >
                                  <Checkbox
                                    id={key}
                                    checked={isChecked}
                                    onCheckedChange={() => toggleChecklistItem(key)}
                                    className="mt-1"
                                  />
                                  <label
                                    htmlFor={key}
                                    className="flex-1 cursor-pointer"
                                  >
                                    <div className={`font-semibold transition-colors duration-300 ${isChecked ? 'line-through text-zinc-500' : 'text-gray-900 dark:text-white'}`}>
                                      {task.task}
                                    </div>
                                    <p className={`text-sm mt-1 transition-colors duration-300 ${isChecked ? 'line-through text-zinc-600' : 'text-gray-700 dark:text-zinc-300'}`}>
                                      {task.description}
                                    </p>
                                    <div className="flex items-center gap-2 mt-2">
                                      <Badge variant="outline" className="text-xs border-gray-400 dark:border-zinc-600 text-gray-700 dark:text-zinc-300 transition-colors duration-300">
                                        <Clock className="w-3 h-3 mr-1" />
                                        {task.estimatedTime}
                                      </Badge>
                                    </div>
                                  </label>
                                </div>
                              );
                            })}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Completion Message */}
                  {(() => {
                    const progress = calculateProgress();
                    if (progress.percentage === 100) {
                      return (
                        <div className="mt-6 p-6 bg-green-900/30 border-2 border-green-600 rounded-lg text-center">
                          <div className="flex justify-center mb-3">
                            <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center">
                              <CheckCircle2 className="w-10 h-10 text-white" />
                            </div>
                          </div>
                          <h3 className="text-2xl font-bold text-green-400 mb-2">🎉 Congratulations!</h3>
                          <p className="text-green-300">
                            You've completed all {progress.total} tasks in your action plan. Great work on finishing your project!
                          </p>
                        </div>
                      );
                    }
                    return null;
                  })()}

                  {/* Save & Share Footer */}
                  <div className="sticky bottom-0 mt-6 p-4 bg-gray-100 dark:bg-zinc-800 border-t-2 border-[#FF5733] rounded-b-lg transition-colors duration-300">
                    <div className="flex flex-col sm:flex-row items-center gap-3">
                      <div className="flex-1 text-center sm:text-left">
                        <p className="text-sm font-semibold text-gray-900 dark:text-white mb-1 transition-colors duration-300">
                          📱 Save to Your Phone
                        </p>
                        <p className="text-xs text-gray-700 dark:text-zinc-300 transition-colors duration-300">
                          Generate a link to access this checklist anytime, even offline. Add it to your home screen!
                        </p>
                      </div>
                      <Button
                        onClick={handleSaveChecklist}
                        className="bg-[#FF5733] hover:bg-[#FF5733]/90 shrink-0"
                        size="lg"
                      >
                        <Share2 className="w-4 h-4 mr-2" />
                        Save & Share Link
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
            
            <div className="bg-gray-100 dark:bg-zinc-800 p-4 sm:p-6 rounded-lg border border-gray-300 dark:border-zinc-700 mb-4 sm:mb-6 transition-colors duration-300">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-sm sm:text-base transition-colors duration-300">Section Overview: Implementation Roadmap</h3>
              <p className="text-sm sm:text-base text-gray-700 dark:text-zinc-300 leading-relaxed transition-colors duration-300">
                This section provides a comprehensive, phase-by-phase implementation roadmap tailored specifically for {data.area}. Each phase includes detailed tasks with time estimates, multiple alternative approaches to accommodate different circumstances and preferences, best practices derived from successful implementations in {data.area}, and clear deliverables. The phased approach enables manageable execution while maintaining flexibility to adapt based on market feedback, resource availability, and evolving business conditions. All cost estimates reflect {data.area} market rates in {data.currency}, and timelines account for local regulatory approval processes, business practices, and market dynamics. Critical success factors for each phase ensure focus on activities that drive meaningful progress toward objectives.
              </p>
            </div>
            
            <div className="space-y-6">
              {(data.actionSteps || []).map((step, index) => (
                <Card key={index} className="border-l-4 border-[#FF5733] bg-white dark:bg-zinc-900 transition-colors duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4 mb-4">
                      <div className="flex-shrink-0 w-12 h-12 rounded-full bg-[#FF5733] text-white flex items-center justify-center font-bold text-lg">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-bold text-xl text-gray-900 dark:text-white mb-2 transition-colors duration-300">{step.phase}</h3>
                        <p className="text-gray-700 dark:text-zinc-300 mb-3 transition-colors duration-300">{step.description}</p>
                        <div className="grid md:grid-cols-2 gap-3 mb-4">
                          <div className="flex items-center gap-2 text-sm bg-gray-100 dark:bg-zinc-800 p-2 rounded border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                            <Clock className="w-4 h-4 text-[#FF5733]" />
                            <span className="text-gray-700 dark:text-zinc-300 transition-colors duration-300"><strong className="text-gray-900 dark:text-white">Duration:</strong> {step.duration}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm bg-gray-100 dark:bg-zinc-800 p-2 rounded border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                            <DollarSign className="w-4 h-4 text-[#FF5733]" />
                            <span className="text-gray-700 dark:text-zinc-300 transition-colors duration-300"><strong className="text-gray-900 dark:text-white">Cost:</strong> {step.estimatedCost}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Detailed Tasks */}
                    <div className="space-y-6 mt-6">
                      {(step.detailedTasks || []).map((task, taskIndex) => (
                        <div key={taskIndex} className="bg-gray-100 dark:bg-zinc-800 p-4 rounded-lg border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                          <div className="flex items-start gap-2 mb-3">
                            <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5" />
                            <div className="flex-1">
                              <h4 className="font-semibold text-gray-900 dark:text-white transition-colors duration-300">{task.task}</h4>
                              <p className="text-sm text-gray-700 dark:text-zinc-300 mt-1 transition-colors duration-300">{task.description}</p>
                              <p className="text-xs text-gray-600 dark:text-zinc-400 mt-1 transition-colors duration-300">
                                <strong>Estimated Time:</strong> {task.estimatedTime}
                              </p>
                            </div>
                          </div>

                          {/* Alternatives */}
                          <div className="mt-3 p-3 bg-white/10 border border-blue-700 rounded">
                            <p className="text-sm font-semibold text-blue-500 mb-2 flex items-center gap-1">
                              <Lightbulb className="w-4 h-4" />
                              Alternative Approaches:
                            </p>
                            <ul className="list-disc list-inside text-sm text-blue-400 space-y-1">
                              {(task.alternatives || []).map((alt, altIndex) => (
                                <li key={altIndex}>{alt}</li>
                              ))}
                            </ul>
                          </div>

                          {/* Best Practices */}
                          <div className="mt-3 p-3 bg-white/10 border border-green-700 rounded">
                            <p className="text-sm font-semibold text-green-600 mb-2 flex items-center gap-1">
                              <Target className="w-4 h-4" />
                              Best Practices:
                            </p>
                            <ul className="list-disc list-inside text-sm text-green-500 space-y-1">
                              {(task.bestPractices || []).map((practice, practiceIndex) => (
                                <li key={practiceIndex}>{practice}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Deliverables */}
                    <div className="mt-6 p-4 bg-gray-100 dark:bg-zinc-800 border border-[#FF5733] rounded transition-colors duration-300">
                      <p className="text-sm font-semibold text-[#FF5733] mb-2">Phase Deliverables:</p>
                      <div className="flex flex-wrap gap-2">
                        {(step.deliverables || []).map((deliverable, delIndex) => (
                          <Badge key={delIndex} variant="outline" className="bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-700 text-gray-900 dark:text-white transition-colors duration-300">
                            <FileText className="w-3 h-3 mr-1" />
                            {deliverable}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Critical Success Factors */}
                    <div className="mt-4 p-4 bg-white/10 border border-orange-700 rounded">
                      <p className="text-sm font-semibold text-orange-600 mb-2">Critical Success Factors:</p>
                      <ul className="list-disc list-inside text-sm text-orange-400 space-y-1">
                        {(step.criticalSuccessFactors || []).map((factor, factorIndex) => (
                          <li key={factorIndex}>{factor}</li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Local Vendors with Alternatives */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Building2 className="w-6 h-6 text-[#FF5733]" />
              <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">Recommended Vendors & Service Providers</h2>
            </div>
            
            <div className="bg-gray-100 dark:bg-zinc-800 p-4 sm:p-6 rounded-lg border border-gray-300 dark:border-zinc-700 mb-4 transition-colors duration-300">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-sm sm:text-base transition-colors duration-300">Section Overview: Local Vendor Ecosystem in {data.area}</h3>
              <p className="text-sm sm:text-base text-gray-700 dark:text-zinc-300 leading-relaxed transition-colors duration-300">
                This section provides carefully curated vendor recommendations for {data.area}, with all contact information localized (phone numbers with {locationInfo.phonePrefix} prefix, business hours in {locationInfo.timezone}). Each vendor listing includes detailed service offerings, estimated costs in {data.currency}, and alternative options to ensure competitive pricing and service quality. Vendor selection considers reputation in {data.area}, financial stability, service quality, responsiveness, and specific expertise relevant to your needs. Alternative providers are included for each category, enabling competitive bidding and backup options. All cost estimates reflect current {data.area} market rates and include typical pricing ranges to support budgeting and negotiation. Building strong relationships with local vendors is crucial for success in {data.area}, where business often operates on relationship trust and long-term partnerships.
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              {(data.vendors || []).map((vendor, index) => (
                <Card key={index} className="hover:shadow-lg transition-shadow bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-3 mb-3">
                      <Package className="w-5 h-5 text-[#FF5733] mt-1" />
                      <div className="flex-1">
                        <h3 className="font-bold text-gray-900 dark:text-white transition-colors duration-300">{vendor.name}</h3>
                        <Badge variant="secondary" className="mt-1 bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-zinc-300 border-gray-300 dark:border-zinc-700 transition-colors duration-300">{vendor.category}</Badge>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-zinc-300 mb-3 transition-colors duration-300">{vendor.description}</p>
                    
                    {/* Services Offered */}
                    <div className="mb-3 p-3 bg-gray-100 dark:bg-zinc-800 rounded border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                      <p className="text-xs font-semibold text-gray-900 dark:text-white mb-1 transition-colors duration-300">Services Offered:</p>
                      <ul className="list-disc list-inside text-xs text-gray-700 dark:text-zinc-300 space-y-0.5 transition-colors duration-300">
                        {(vendor.services || []).map((service, svcIndex) => (
                          <li key={svcIndex}>{service}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Contact Info */}
                    <div className="space-y-2 text-sm text-gray-700 dark:text-zinc-300 mb-3 transition-colors duration-300">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-gray-600 dark:text-zinc-400 transition-colors duration-300" />
                        <span>{vendor.location}</span>
                      </div>
                      {vendor.phone && (
                        <div className="flex items-center gap-2">
                          <Phone className="w-4 h-4 text-gray-600 dark:text-zinc-400 transition-colors duration-300" />
                          <span>{vendor.phone}</span>
                        </div>
                      )}
                      {vendor.email && (
                        <div className="flex items-center gap-2">
                          <Mail className="w-4 h-4 text-gray-600 dark:text-zinc-400 transition-colors duration-300" />
                          <span>{vendor.email}</span>
                        </div>
                      )}
                      {vendor.website && (
                        <div className="flex items-center gap-2">
                          <Globe className="w-4 h-4 text-gray-600 dark:text-zinc-400 transition-colors duration-300" />
                          <a href={vendor.website} className="text-[#FF5733] hover:underline" target="_blank" rel="noopener noreferrer">
                            Visit Website
                          </a>
                        </div>
                      )}
                    </div>

                    {/* Alternatives */}
                    <div className="p-3 bg-white/10 border border-blue-700 rounded mb-3">
                      <p className="text-xs font-semibold text-blue-500 mb-1">Alternative Options:</p>
                      <ul className="list-disc list-inside text-xs text-blue-500 space-y-0.5">
                        {(vendor.alternatives || []).map((alt, altIndex) => (
                          <li key={altIndex}>{alt}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="pt-3 border-t border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                      <p className="text-xs text-gray-600 dark:text-zinc-400 transition-colors duration-300">
                        <strong className="text-gray-900 dark:text-white">Est. Cost:</strong> {vendor.estimatedCost}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Funding Options */}
          <section>
            <div className="flex items-center gap-2 mb-1">
              <Banknote className="w-6 h-6 text-[#FF5733]" />
              <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">Funding Options & Alternatives</h2>
            </div>
            <p className="text-gray-700 dark:text-zinc-300 mb-4 transition-colors duration-300">
              Multiple pathways to secure capital for your venture. Choose the option that best fits your situation:
            </p>
            <div className="grid md:grid-cols-2 sm:grid-row gap-4">
              {(data.fundingOptions || []).map((option, index) => (
                <Card key={index} className="hover:shadow-lg transition-shadow bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-0 mb-1">
                      <DollarSign className="w-5 h-5 text-green-500 mt-1" />
                      <div className="flex-1">
                        <h3 className="font-bold text-gray-900 dark:text-white transition-colors duration-300">{option.option}</h3>
                        <p className="text-sm text-gray-700 dark:text-zinc-300 mt-1 transition-colors duration-300">{option.description}</p>
                        <Badge variant="outline" className="mt-2 bg-white border-green-700 text-green-600">
                          Typical: {option.typicalAmount}
                        </Badge>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 sm:grid-row gap-1 mt-4">
                      <div className="p-3 bg-green-900/60 border border-green-700 rounded">
                        <p className="text-xs font-semibold text-green-300 mb-1">Pros:</p>
                        <ul className="list-disc list-inside text-xs text-green-200 space-y-0.5">
                          {(option.pros || []).map((pro, proIndex) => (
                            <li key={proIndex}>{pro}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="p-3 bg-red-900/10 border border-red-700 rounded">
                        <p className="text-xs font-semibold text-red-500 mb-1">Cons:</p>
                        <ul className="list-disc list-inside text-xs text-red-500 space-y-0.5">
                          {(option.cons || []).map((con, conIndex) => (
                            <li key={conIndex}>{con}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Key Milestones */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-6 h-6 text-[#FF5733]" />
              <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">Key Milestones & Timeline</h2>
            </div>
            <div className="space-y-4">
              {(data.milestones || []).map((milestone, index) => (
                <Card key={index} className="border-l-4 border-[#FF5733] bg-white dark:bg-zinc-900 transition-colors duration-300">
                  <CardContent className="p-6">
                    <div className="flex flex-col sm:flex-row items-start gap-4">
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[#FF5733] text-white flex items-center justify-center font-bold text-sm">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-lg text-gray-900 dark:text-white transition-colors duration-300">{milestone.title}</h4>
                        <p className="text-sm text-gray-700 dark:text-zinc-300 mt-1 transition-colors duration-300">{milestone.description}</p>
                        <div className="flex items-center gap-2 mt-2 text-sm text-[#FF5733]">
                          <Calendar className="w-4 h-4" />
                          <span className="font-medium">{milestone.targetDate}</span>
                        </div>
                        
                        <div className="grid md:grid-cols-2 gap-3 mt-3">
                          <div className="p-2 bg-orange-900/10 border border-orange-700 rounded">
                            <p className="text-xs font-semibold text-orange-600 mb-1">Dependencies:</p>
                            <ul className="list-disc list-inside text-xs text-orange-500 space-y-0.5">
                              {(milestone.dependencies || []).map((dep, depIndex) => (
                                <li key={depIndex}>{dep}</li>
                              ))}
                            </ul>
                          </div>
                          <div className="p-2 bg-green-900/70 border border-green-700 rounded">
                            <p className="text-xs font-semibold text-green-200 mb-1">Success Criteria:</p>
                            <ul className="list-disc list-inside text-xs text-white space-y-0.5">
                              {(milestone.successCriteria || []).map((criteria, critIndex) => (
                                <li key={critIndex}>{criteria}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Risk Assessment with Alternatives */}
          <section id="risk-assessment" className="scroll-mt-20">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-6 h-6 text-[#FF5733]" />
              <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">Risk Assessment & Mitigation Strategies</h2>
            </div>
            
            <div className="bg-gray-100 dark:bg-zinc-800 p-4 sm:p-6 rounded-lg border border-gray-300 dark:border-zinc-700 mb-4 transition-colors duration-300">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 text-sm sm:text-base transition-colors duration-300">Section Overview: Risk Management for {data.area}</h3>
              <p className="text-sm sm:text-base text-gray-700 dark:text-zinc-300 leading-relaxed transition-colors duration-300">
                This comprehensive risk assessment identifies potential challenges specific to operating in {data.area}, categorized by severity (High, Medium, Low) based on likelihood and potential impact. Each risk includes primary mitigation strategies proven effective in {data.area} market context, multiple alternative approaches to address the risk from different angles, and detailed contingency plans for scenarios where primary mitigations prove insufficient. Risk factors considered include: regulatory changes (compliance requirements vary and evolve), market competition (intensity varies by sector in {data.area}), economic conditions (currency fluctuations, inflation, interest rates), talent availability (skills shortage in key areas), technology dependencies, supply chain disruptions, and customer adoption challenges. Proactive risk management is essential for sustainable success in {data.area}, where business environment factors can create unexpected challenges requiring rapid adaptation.
              </p>
            </div>
            
            <div className="grid md:grid-cols-1 sm:grid-row gap-4">
              {(data.risks || []).map((risk, index) => (
                <Card key={index} className={`border-l-4 bg-white dark:bg-zinc-900 transition-colors duration-300 ${
                  risk.severity === 'High' ? 'border-red-500' : 
                  risk.severity === 'Medium' ? 'border-orange-500' : 
                  'border-yellow-500'
                }`}>
                  <CardContent className="p-6">
                    <div className="flex flex-col sm:flex-row items-start gap-3 mb-3">
                      <AlertTriangle className={`w-6 h-6 mt-0.5 ${
                        risk.severity === 'High' ? 'text-red-500' : 
                        risk.severity === 'Medium' ? 'text-orange-500' : 
                        'text-yellow-500'
                      }`} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="font-bold text-lg text-gray-900 dark:text-white transition-colors duration-300">{risk.risk}</h4>
                          <Badge 
                            variant="outline"
                            className={
                              risk.severity === 'High' ? 'bg-red-900/30 text-red-300 border-red-700' : 
                              risk.severity === 'Medium' ? 'bg-orange-900/30 text-orange-300 border-orange-700' : 
                              'bg-yellow-900/30 text-yellow-300 border-yellow-700'
                            }
                          >
                            {risk.severity} Severity
                          </Badge>
                        </div>
                        
                        <div className="mb-3 p-3 bg-blue-900/10 border border-blue-700 rounded">
                          <p className="text-sm font-semibold text-blue-500 mb-1">Primary Mitigation Strategy:</p>
                          <p className="text-sm text-blue-500">{risk.mitigation}</p>
                        </div>

                        <div className="mb-3 p-3 bg-gray-100 dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded transition-colors duration-300">
                          <p className="text-sm font-semibold text-[#FF5733] mb-1">Alternative Approaches:</p>
                          <ul className="list-disc list-inside text-sm text-gray-700 dark:text-zinc-300 space-y-1 transition-colors duration-300">
                            {(risk.alternativeApproaches || []).map((approach, approachIndex) => (
                              <li key={approachIndex}>{approach}</li>
                            ))}
                          </ul>
                        </div>

                        <div className="p-3 bg-orange-900/10 border border-orange-700 rounded">
                          <p className="text-sm font-semibold text-orange-500 mb-1">Contingency Plan:</p>
                          <p className="text-sm text-orange-500">{risk.contingencyPlan}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Resources with Alternatives */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Users className="w-6 h-6 text-[#FF5733]" />
              <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">Resources & Team Requirements</h2>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              {(data.resources || []).map((resource, index) => (
                <Card key={index} className="hover:shadow-lg transition-shadow bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                  <CardContent className="p-6">
                    <h4 className="font-bold text-gray-900 dark:text-white mb-2 transition-colors duration-300">{resource.type}</h4>
                    <p className="text-sm text-gray-700 dark:text-zinc-300 mb-3 transition-colors duration-300">{resource.description}</p>
                    <p className="text-sm mb-3 text-gray-700 dark:text-zinc-300 transition-colors duration-300">
                      <strong className="text-gray-900 dark:text-white">Recommended:</strong> {resource.quantity}
                    </p>
                    
                    <div className="p-3 bg-blue-900/10 border border-blue-700 rounded mb-3">
                      <p className="text-xs font-semibold text-blue-500 mb-1">Alternative Options:</p>
                      <ul className="list-disc list-inside text-xs text-blue-400 space-y-0.5">
                        {(resource.alternatives || []).map((alt, altIndex) => (
                          <li key={altIndex}>{alt}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-3 bg-green-900/10 border border-green-700 rounded">
                      <p className="text-xs font-semibold text-green-500 mb-1">Cost-Saving Options:</p>
                      <ul className="list-disc list-inside text-xs text-green-500 space-y-0.5">
                        {resource.costSavingOptions.map((option, optionIndex) => (
                          <li key={optionIndex}>{option}</li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Compliance Checklist */}
          <section>
            <div className="flex flex-col sm:flex-row items-center sm:text-left gap-2 mb-4">
              <ClipboardCheck className="w-6 h-6 text-[#FF5733]" />
              <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">Legal & Compliance Checklist</h2>
            </div>
            <p className="text-gray-700 dark:text-zinc-300 mb-4 transition-colors duration-300">
              Critical compliance requirements to ensure legal operation:
            </p>
            <div className="space-y-3">
              {(data.complianceChecklist || []).map((item, index) => (
                <Card key={index} className="flex flex-col sm:flex-row border-l-4 border-blue-500 bg-white dark:bg-zinc-900 transition-colors duration-300 text-wrap">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <Scale className="w-5 h-5 text-blue-500 mt-1" />
                      <div className="flex flex-col sm:flex-row">
                        <h4 className="text-sm flex flex-col font-semibold text-gray-900 dark:text-white transition-colors duration-300 p-[0px] ml-[0px] sm:ml-12 mr-[50px] my-[0px]">{item.requirement}</h4>
                        <p className=" flex text-sm text-gray-700 dark:text-zinc-300 mt-1 transition-colors duration-300">{item.description}</p>
                        <div className="flex items-center gap-2 mt-2 text-sm">
                          <Badge variant="outline" className="bg-orange-900/10 border-orange-700 text-orange-500">
                            Deadline: {item.deadline}
                          </Badge>
                        </div>
                        <div className="mt-1 p-2 bg-gray-100 dark:bg-zinc-800 rounded border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                          <p className="text-xs font-semibold text-gray-900 dark:text-white mb-1 transition-colors duration-300">Resources:</p>
                          <ul className="list-disc list-inside text-xs text-gray-700 dark:text-zinc-300 space-y-0.5 transition-colors duration-300">
                            {(item.resources || []).map((resource, resIndex) => (
                              <li key={resIndex}>{resource}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Detailed Recommendations */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="w-6 h-6 text-[#FF5733]" />
              <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">Expert Recommendations by Category</h2>
            </div>
            <div className="space-y-4">
              {(data.detailedRecommendations || []).map((category, index) => (
                <Card key={index} className="bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                  <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                    <CardTitle className="text-lg text-gray-900 dark:text-white transition-colors duration-300">{category.category}</CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <ul className="space-y-2">
                      {(category.recommendations || []).map((rec, recIndex) => (
                        <li key={recIndex} className="flex items-start gap-2">
                          <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-gray-700 dark:text-zinc-300 transition-colors duration-300">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Financial Projections - 5 Year */}
          {data.financialProjections && (
            <section>
              <div className="flex items-center gap-2 mb-4">
                <DollarSign className="w-6 h-6 text-[#FF5733]" />
                <h2 className="text-gray-900 dark:text-white text-2xl font-serif transition-colors duration-300">5-Year Financial Projections</h2>
              </div>
              <p className="text-gray-700 dark:text-zinc-300 mb-6 transition-colors duration-300">
                Comprehensive financial projections for your {data.need} business idea in {data.area}, showing expected revenue growth, profitability, and key financial metrics over 5 years. All amounts shown in {data.currency}.
              </p>

              {/* Revenue & Profitability Chart */}
              <Card className="mb-6 bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                <CardHeader className="border-b border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                  <CardTitle className="text-gray-900 dark:text-white transition-colors duration-300">5-Year Revenue, EBITDA & Net Income Trajectory</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <ComposedChart data={data.financialProjections.yearlyProjections}>
                      <CartesianGrid key="actionplan-grid" strokeDasharray="3 3" />
                      <XAxis key="actionplan-xaxis" dataKey="year" />
                      <YAxis key="actionplan-yaxis-left" yAxisId="left" label={{ value: 'Amount ($M)', angle: -90, position: 'insideLeft' }} />
                      <YAxis key="actionplan-yaxis-right" yAxisId="right" orientation="right" label={{ value: 'Margin (%)', angle: 90, position: 'insideRight' }} />
                      <Tooltip 
                        key="actionplan-tooltip"
                        formatter={(value: any, name: any) => {
                          if (String(name).includes('Margin')) return `${value}%`;
                          return `$${typeof value === 'number' ? value.toFixed(2) : value}M`;
                        }}
                      />
                      <Legend key="actionplan-legend" />
                      <Bar key="actionplan-bar-revenue" yAxisId="left" dataKey="revenue" fill="#8b5cf6" name="Revenue" />
                      <Bar key="actionplan-bar-ebitda" yAxisId="left" dataKey="ebitda" fill="#10b981" name="EBITDA" />
                      <Bar key="actionplan-bar-netincome" yAxisId="left" dataKey="netIncome" fill="#3b82f6" name="Net Income" />
                      <Line key="actionplan-line-ebitdamargin" yAxisId="right" type="monotone" dataKey="ebitdaMargin" stroke="#059669" strokeWidth={3} name="EBITDA Margin %" />
                      <Line key="actionplan-line-netmargin" yAxisId="right" type="monotone" dataKey="netMargin" stroke="#2563eb" strokeWidth={3} name="Net Margin %" />
                    </ComposedChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Detailed Financial Table */}
              <Card className="mb-6 bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                <CardHeader className="border-b border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                  <CardTitle className="text-gray-900 dark:text-white transition-colors duration-300">Comprehensive Financial Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                          <TableHead className="font-bold text-gray-900 dark:text-white transition-colors duration-300">Year</TableHead>
                          <TableHead className="font-bold text-gray-900 dark:text-white transition-colors duration-300">Revenue</TableHead>
                          <TableHead className="font-bold text-gray-900 dark:text-white transition-colors duration-300">Gross Profit</TableHead>
                          <TableHead className="font-bold text-gray-900 dark:text-white transition-colors duration-300">EBITDA</TableHead>
                          <TableHead className="font-bold text-gray-900 dark:text-white transition-colors duration-300">Net Income</TableHead>
                          <TableHead className="font-bold text-gray-900 dark:text-white transition-colors duration-300">FCF</TableHead>
                          <TableHead className="font-bold text-gray-900 dark:text-white transition-colors duration-300">Growth</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {data.financialProjections.yearlyProjections.map((proj: any, idx: number) => (
                          <TableRow key={idx} className="border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                            <TableCell className="font-medium text-gray-900 dark:text-white transition-colors duration-300">{proj.year}</TableCell>
                            <TableCell className="text-[#FF5733] font-semibold">{proj.revenueFormatted}</TableCell>
                            <TableCell className="text-gray-700 dark:text-zinc-300 transition-colors duration-300">{formatBudgetWithCurrency(proj.grossProfit * 1000000, data.currency)}</TableCell>
                            <TableCell className="text-green-500 font-semibold">{proj.ebitdaFormatted}</TableCell>
                            <TableCell className="text-blue-500 font-semibold">{proj.netIncomeFormatted}</TableCell>
                            <TableCell className="text-gray-700 dark:text-zinc-300 transition-colors duration-300">{proj.freeCashFlowFormatted}</TableCell>
                            <TableCell className="text-emerald-500">{proj.revenueGrowth}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>

              {/* Profit Margins Over Time */}
              <Card className="mb-6 bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                <CardHeader className="border-b border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                  <CardTitle className="text-gray-900 dark:text-white transition-colors duration-300">Profitability Margins Evolution</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data.financialProjections.yearlyProjections}>
                      <CartesianGrid key="margins-grid" strokeDasharray="3 3" />
                      <XAxis key="margins-xaxis" dataKey="year" />
                      <YAxis key="margins-yaxis" label={{ value: 'Margin (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip key="margins-tooltip" formatter={(value: any) => `${value}%`} />
                      <Legend key="margins-legend" />
                      <Line key="margins-line-gross" type="monotone" dataKey="grossMargin" stroke="#8b5cf6" strokeWidth={3} name="Gross Margin %" />
                      <Line key="margins-line-ebitda" type="monotone" dataKey="ebitdaMargin" stroke="#10b981" strokeWidth={3} name="EBITDA Margin %" />
                      <Line key="margins-line-net" type="monotone" dataKey="netMargin" stroke="#3b82f6" strokeWidth={3} name="Net Margin %" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Key Financial Metrics */}
              <Card className="mb-6 bg-white dark:bg-zinc-900 border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                <CardHeader className="border-b border-gray-300 dark:border-zinc-800 transition-colors duration-300">
                  <CardTitle className="text-gray-900 dark:text-white transition-colors duration-300">Key Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-4">
                    {data.financialProjections.keyMetrics.map((metric: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between p-4 bg-gray-100 dark:bg-zinc-800 rounded-lg border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                        <div>
                          <p className="text-sm text-gray-600 dark:text-zinc-400 transition-colors duration-300">{metric.metric}</p>
                          <p className="text-2xl font-bold text-[#FF5733]">{metric.value}</p>
                          <p className="text-xs text-gray-500 dark:text-zinc-500 transition-colors duration-300">Target: {metric.target}</p>
                        </div>
                        <Badge 
                          variant="outline" 
                          className={
                            metric.status === 'Exceeding' 
                              ? 'bg-green-900/10 text-green-600 border-green-700' 
                              : 'bg-blue-900/10 text-blue-600 border-blue-700'
                          }
                        >
                          {metric.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Financial Assumptions */}
              <Card className="border-gray-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 transition-colors duration-300">
                <CardHeader className="bg-white dark:bg-zinc-900 border-b border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                  <CardTitle className="text-gray-900 dark:text-white transition-colors duration-300">{data.financialProjections.assumptions.title}</CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                  <ul className="space-y-2">
                    {data.financialProjections.assumptions.items.map((item: string, idx: number) => (
                      <li key={idx} className="text-sm flex items-start gap-2">
                        <span className="text-[#FF5733] mt-1">•</span>
                        <span className="text-gray-700 dark:text-zinc-300 transition-colors duration-300">{item}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </section>
          )}

          <Separator className="bg-gray-300 dark:bg-zinc-800 transition-colors duration-300" />

          {/* Success Metrics */}
          <section id="success-metrics" className="scroll-mt-20">
            <div className="bg-white dark:bg-zinc-800 p-6 rounded-lg border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
              <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-3 flex items-center gap-2 transition-colors duration-300">
                <Target className="w-6 h-6 text-[#FF5733]" />
                Success Metrics & KPIs
              </h3>
              <ul className="space-y-2 text-gray-800 dark:text-white">
                {(data.successMetrics || []).map((metric, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>{metric}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* Footer */}
          <div className="text-center text-gray-500 dark:text-zinc-600 text-xs tracking-wider py-8 border-t border-gray-300 dark:border-zinc-800 transition-colors duration-300">
            <p className="text-[10px]">
              Action plan based on real market data, verified local vendors, and industry-standard timelines for {data.area}
            </p>
          </div>
        </CardContent>
      </Card>
      </div>
    </div>
  );
}