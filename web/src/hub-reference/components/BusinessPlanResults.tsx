// @ts-nocheck
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { 
  FileText, 
  ArrowLeft, 
  Building2, 
  TrendingUp, 
  Users, 
  Package, 
  Target, 
  Cog, 
  DollarSign, 
  AlertTriangle,
  Calendar,
  LogOut,
  Download
} from 'lucide-react';
import { BusinessPlanData } from '../utils/businessPlanGenerator';
import { downloadBusinessPlan } from '../utils/pdfGenerator';

interface BusinessPlanResultsProps {
  data: BusinessPlanData;
  onNewPlan: () => void;
}

export function BusinessPlanResults({ data, onNewPlan }: BusinessPlanResultsProps) {
  // Define all sections for index
  const sections = [
    { id: 'reality-check', title: '💡 MARKET ASSESSMENT', icon: AlertTriangle },
    { id: 'executive-summary', title: 'Executive Summary', icon: FileText },
    { id: 'company-description', title: 'Company Description', icon: Building2 },
    { id: 'market-analysis', title: 'Market Analysis', icon: TrendingUp },
    { id: 'organization-management', title: 'Organization & Management', icon: Users },
    { id: 'products-services', title: 'Products & Services', icon: Package },
    { id: 'marketing-strategy', title: 'Marketing & Sales Strategy', icon: Target },
    { id: 'operations-plan', title: 'Operations Plan', icon: Cog },
    { id: 'financial-projections', title: 'Financial Projections', icon: DollarSign },
    { id: 'risk-analysis', title: 'Risk Analysis & Mitigation', icon: AlertTriangle },
    { id: 'implementation-timeline', title: 'Implementation Timeline', icon: Calendar },
    { id: 'exit-strategy', title: 'Exit Strategy', icon: LogOut },
  ];

  const handleDownload = async () => {
    await downloadBusinessPlan(data.businessIdea);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-black max-w-7xl mx-auto px-3 py-4 sm:p-6 transition-colors duration-300 overflow-x-hidden">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        {/* Download Button */}
        <div className="mb-3 sm:mb-4 flex justify-end">
          <Button
            onClick={handleDownload}
            className="flex items-center gap-1.5 sm:gap-2 bg-gradient-to-r from-[#FF5733] to-[#FF8C42] hover:from-[#FF6B47] hover:to-[#FFA05C] text-white px-3 py-2 sm:px-6 sm:py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 text-sm sm:text-base"
          >
            <Download className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="font-semibold">Download PDF</span>
          </Button>
        </div>
        
        <div className="bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 text-gray-900 dark:text-white p-3 sm:p-6 md:p-8 rounded-lg shadow-xl transition-colors duration-300">
          <div className="flex items-start gap-2 sm:gap-4">
            <FileText className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 flex-shrink-0 text-[#FF5733]" />
            <div className="flex-1 min-w-0">
              <h1 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold mb-1 sm:mb-2 font-serif text-black dark:text-white transition-colors duration-300">Business Plan</h1>
              <p className="text-black dark:text-zinc-300 text-base sm:text-lg mb-1 transition-colors duration-300 break-words">{data.businessIdea}</p>
              <p className="text-gray-600 dark:text-zinc-400 text-xs sm:text-sm transition-colors duration-300 break-words">
                {data.country} • {data.currency} • Generated: {data.generatedDate}
              </p>
              <p className="text-black dark:text-zinc-300 text-sm sm:text-base mt-1 sm:mt-2 transition-colors duration-300 break-words">
                Target Revenue: <span className="font-bold text-[#FF5733]">{data.targetRevenue}</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <div data-pdf-content>
      {/* TABLE OF CONTENTS */}
      <section className="mb-8 sm:mb-12">
        <div className="flex items-baseline gap-3 sm:gap-6 mb-4 sm:mb-6">
          <span className="text-3xl sm:text-5xl md:text-6xl text-[#FF5733] font-light">00.</span>
          <h2 className="text-xl sm:text-3xl md:text-4xl lg:text-5xl font-serif text-black dark:text-white transition-colors duration-300">
            Table of Contents
          </h2>
        </div>
        
        <div className="ml-0 sm:ml-12 md:ml-20">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 sm:gap-3">
            {sections.map((section, index) => {
              const Icon = section.icon;
              return (
                <a
                  key={section.id}
                  href={`#${section.id}`}
                  className="bg-white dark:bg-zinc-900 rounded-lg sm:rounded-xl p-3 sm:p-4 border border-gray-200 dark:border-zinc-800 hover:border-[#FF5733] transition-all group flex items-center gap-2 sm:gap-4"
                >
                  <span className="text-lg sm:text-2xl text-[#FF5733] font-light group-hover:text-black dark:group-hover:text-white transition-colors flex-shrink-0">
                    {String(index + 1).padStart(2, '0')}.
                  </span>
                  <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-[#FF5733] group-hover:text-black dark:group-hover:text-white transition-colors flex-shrink-0" />
                  <span className="text-black dark:text-white text-xs sm:text-sm group-hover:text-[#FF5733] transition-colors break-words">
                    {section.title}
                  </span>
                </a>
              );
            })}
          </div>
        </div>
      </section>

      {/* REALITY CHECK - BRUTALLY HONEST */}
      <Card 
        id="reality-check" 
        className={`mb-6 sm:mb-8 shadow-2xl border-2 transition-colors duration-300 ${
          data.realityCheck.viabilityScore >= 60 
            ? 'bg-green-100 dark:bg-green-950 border-green-600' 
            : data.realityCheck.viabilityScore >= 40 
            ? 'bg-yellow-100 dark:bg-yellow-950 border-yellow-600' 
            : 'bg-red-100 dark:bg-red-950 border-red-600'
        }`}
      >
        <CardHeader className={`border-b-2 transition-colors duration-300 p-3 sm:p-6 ${
          data.realityCheck.viabilityScore >= 60 
            ? 'bg-green-200 dark:bg-green-900 border-green-600' 
            : data.realityCheck.viabilityScore >= 40 
            ? 'bg-yellow-200 dark:bg-yellow-900 border-yellow-600' 
            : 'bg-red-200 dark:bg-red-900 border-red-600'
        }`}>
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-black dark:text-white font-serif transition-colors duration-300">
            <div className="flex items-center gap-2">
              <span className="text-xl sm:text-2xl text-black dark:text-white font-light transition-colors duration-300">00.</span>
              <AlertTriangle className="w-6 h-6 sm:w-8 sm:h-8 text-black dark:text-white transition-colors duration-300" />
            </div>
            <div className="flex-1">
              <div className="text-base sm:text-xl md:text-2xl text-black dark:text-white transition-colors duration-300 break-words">💡 MARKET ASSESSMENT - KEY INSIGHTS</div>
              <div className={`text-xs sm:text-sm mt-1 transition-colors duration-300 ${
                data.realityCheck.viabilityScore >= 60 ? 'text-green-800 dark:text-green-200' 
                : data.realityCheck.viabilityScore >= 40 ? 'text-yellow-800 dark:text-yellow-200' 
                : 'text-orange-800 dark:text-orange-200'
              }`}>
                Market Score: {data.realityCheck.viabilityScore}/100 
                {data.realityCheck.viabilityScore >= 70 && ' - STRONG POTENTIAL'}
                {data.realityCheck.viabilityScore >= 55 && data.realityCheck.viabilityScore < 70 && ' - GOOD OPPORTUNITY'}
                {data.realityCheck.viabilityScore >= 40 && data.realityCheck.viabilityScore < 55 && ' - ACHIEVABLE'}
                {data.realityCheck.viabilityScore < 40 && ' - STRATEGIC APPROACH NEEDED'}
              </div>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-3 sm:p-6 space-y-4 sm:space-y-6">
          {/* Market Assessment */}
          <div className="bg-white dark:bg-zinc-900 p-3 sm:p-6 rounded-lg border-2 border-gray-300 dark:border-white transition-colors duration-300">
            <h3 className="font-bold text-base sm:text-xl mb-2 sm:mb-3 text-black dark:text-white transition-colors duration-300">MARKET OVERVIEW</h3>
            <p className="text-black dark:text-white text-sm sm:text-base md:text-lg leading-relaxed transition-colors duration-300 break-words">{data.realityCheck.honestAssessment}</p>
          </div>

          {/* Challenges to Address */}
          {data.realityCheck.redFlags.length > 0 && (
            <div className="bg-orange-50 dark:bg-orange-900/20 p-3 sm:p-6 rounded-lg border-2 border-orange-400 transition-colors duration-300">
              <h3 className="font-bold text-base sm:text-xl mb-2 sm:mb-3 text-black dark:text-white transition-colors duration-300">💡 CHALLENGES TO ADDRESS</h3>
              <ul className="space-y-2 sm:space-y-3">
                {data.realityCheck.redFlags.map((flag, idx) => (
                  <li key={idx} className="text-black dark:text-white text-xs sm:text-sm md:text-base flex items-start gap-2 transition-colors duration-300">
                    <span className="text-red-600 dark:text-red-400 font-bold flex-shrink-0">•</span>
                    <span className="break-words">{flag}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Market Strengths */}
          {data.realityCheck.greenFlags.length > 0 && (
            <div className="bg-green-100 dark:bg-green-900 p-3 sm:p-6 rounded-lg border-2 border-green-600 transition-colors duration-300">
              <h3 className="font-bold text-base sm:text-xl mb-2 sm:mb-3 text-black dark:text-white transition-colors duration-300">✅ MARKET STRENGTHS</h3>
              <ul className="space-y-2 sm:space-y-3">
                {data.realityCheck.greenFlags.map((flag, idx) => (
                  <li key={idx} className="text-black dark:text-white text-xs sm:text-sm md:text-base flex items-start gap-2 transition-colors duration-300">
                    <span className="text-green-600 dark:text-green-400 font-bold flex-shrink-0">•</span>
                    <span className="break-words">{flag}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Strategic Insights */}
          {data.realityCheck.truthBombs.length > 0 && (
            <div className="bg-blue-50 dark:bg-blue-900/20 p-3 sm:p-6 rounded-lg border-2 border-blue-400 transition-colors duration-300">
              <h3 className="font-bold text-base sm:text-xl mb-2 sm:mb-3 text-black dark:text-white transition-colors duration-300">💡 STRATEGIC INSIGHTS</h3>
              <ul className="space-y-2 sm:space-y-3">
                {data.realityCheck.truthBombs.map((bomb, idx) => (
                  <li key={idx} className="text-black dark:text-white text-xs sm:text-sm md:text-base flex items-start gap-2 transition-colors duration-300">
                    <span className="text-blue-600 dark:text-blue-400 font-bold flex-shrink-0">•</span>
                    <span className="break-words">{bomb}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className={`p-3 sm:p-4 rounded-lg text-center transition-colors duration-300 ${
            data.realityCheck.viabilityScore >= 40
              ? 'bg-green-200 dark:bg-green-800 text-black dark:text-white' 
              : 'bg-orange-200 dark:bg-orange-800 text-black dark:text-white'
          }`}>
            <p className="font-bold text-sm sm:text-base md:text-lg break-words">
              {data.realityCheck.viabilityScore >= 40
                ? '✓ This business idea has potential. Focus on your unique value proposition and execute well.' 
                : '💡 This market is competitive. Success requires a strategic niche approach and differentiation.'}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Executive Summary */}
      <Card id="executive-summary" className="mb-6 shadow-lg bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-black dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#FF5733] font-light">01.</span>
              <FileText className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Executive Summary</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 space-y-4 bg-white dark:bg-zinc-900 transition-colors duration-300 overflow-x-hidden">
          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white transition-colors duration-300">Business Concept</h3>
            <p className="text-sm sm:text-base text-black dark:text-zinc-300 transition-colors duration-300 break-words">{data.executiveSummary.businessConcept}</p>
          </div>
          
          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white transition-colors duration-300">Mission Statement</h3>
            <p className="text-sm sm:text-base text-black dark:text-zinc-300 italic transition-colors duration-300 break-words">{data.executiveSummary.missionStatement}</p>
          </div>
          
          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white transition-colors duration-300">Keys to Success</h3>
            <ul className="list-disc list-inside space-y-1 text-sm sm:text-base text-black dark:text-zinc-300 transition-colors duration-300">
              {data.executiveSummary.keysToSuccess.map((key, idx) => (
                <li key={idx} className="break-words">{key}</li>
              ))}
            </ul>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 pt-3 sm:pt-4">
            <div className="bg-gray-100 dark:bg-zinc-800 p-3 sm:p-4 rounded-lg border border-[#FF5733] transition-colors duration-300">
              <p className="text-xs text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Target Revenue</p>
              <p className="text-base sm:text-lg md:text-xl font-bold text-[#FF5733] break-words">{data.executiveSummary.financialHighlights.targetRevenue}</p>
            </div>
            <div className="bg-gray-100 dark:bg-zinc-800 p-3 sm:p-4 rounded-lg border border-green-600 transition-colors duration-300">
              <p className="text-xs text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Projected Profit</p>
              <p className="text-base sm:text-lg md:text-xl font-bold text-green-500 break-words">{data.executiveSummary.financialHighlights.projectedProfit}</p>
            </div>
            <div className="bg-gray-100 dark:bg-zinc-800 p-3 sm:p-4 rounded-lg border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
              <p className="text-xs text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Break-Even Point</p>
              <p className="text-base sm:text-lg md:text-xl font-bold text-black dark:text-white transition-colors duration-300 break-words">{data.executiveSummary.financialHighlights.breakEvenPoint}</p>
            </div>
            <div className="bg-gray-100 dark:bg-zinc-800 p-3 sm:p-4 rounded-lg border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
              <p className="text-xs text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Initial Investment</p>
              <p className="text-base sm:text-lg md:text-xl font-bold text-black dark:text-white transition-colors duration-300 break-words">{data.executiveSummary.financialHighlights.initialInvestment}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Company Description */}
      <Card id="company-description" className="mb-6 shadow-lg bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-black dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#FF5733] font-light">02.</span>
              <Building2 className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Company Description</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 bg-white dark:bg-zinc-900 transition-colors duration-300 overflow-x-hidden">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-zinc-400 transition-colors duration-300">Business Name</p>
              <p className="font-semibold text-sm sm:text-base text-black dark:text-white transition-colors duration-300 break-words">{data.companyDescription.businessName}</p>
            </div>
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-zinc-400 transition-colors duration-300">Legal Structure</p>
              <p className="font-semibold text-sm sm:text-base text-black dark:text-white transition-colors duration-300 break-words">{data.companyDescription.legalStructure}</p>
            </div>
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-zinc-400 transition-colors duration-300">Location</p>
              <p className="font-semibold text-sm sm:text-base text-black dark:text-white transition-colors duration-300 break-words">{data.companyDescription.location}</p>
            </div>
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-zinc-400 transition-colors duration-300">Ownership</p>
              <p className="font-semibold text-sm sm:text-base text-black dark:text-white transition-colors duration-300 break-words">{data.companyDescription.ownership}</p>
            </div>
          </div>
          <div className="mt-4 space-y-3">
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Business Model</p>
              <p className="text-sm sm:text-base text-black dark:text-zinc-300 transition-colors duration-300 break-words">{data.companyDescription.businessModel}</p>
            </div>
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Value Proposition</p>
              <p className="text-sm sm:text-base text-black dark:text-zinc-300 transition-colors duration-300 break-words">{data.companyDescription.valueProposition}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Market Analysis */}
      <Card id="market-analysis" className="mb-6 shadow-lg bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-black dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#FF5733] font-light">03.</span>
              <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Market Analysis</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 space-y-6 bg-white dark:bg-zinc-900 transition-colors duration-300 overflow-x-hidden">

          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white transition-colors duration-300">Industry Overview</h3>
            <p className="text-sm sm:text-base text-black dark:text-zinc-300 mb-2 transition-colors duration-300 break-words">{data.marketAnalysis.industryOverview}</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mt-3">
              <div className="bg-gray-100 dark:bg-zinc-800 p-3 rounded border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                <p className="text-xs text-gray-600 dark:text-zinc-400 transition-colors duration-300">Market Size</p>
                <p className="font-bold text-sm sm:text-base md:text-lg text-black dark:text-white transition-colors duration-300 break-words">{data.marketAnalysis.marketSize}</p>
              </div>
              <div className="bg-gray-100 dark:bg-zinc-800 p-3 rounded border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                <p className="text-xs text-gray-600 dark:text-zinc-400 transition-colors duration-300">Growth Rate</p>
                <p className="font-bold text-sm sm:text-base md:text-lg text-black dark:text-white transition-colors duration-300 break-words">{data.marketAnalysis.marketGrowthRate}</p>
              </div>
              <div className="bg-gray-100 dark:bg-zinc-800 p-3 rounded border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
                <p className="text-xs text-gray-600 dark:text-zinc-400 transition-colors duration-300">Target Market</p>
                <p className="font-bold text-xs sm:text-sm text-black dark:text-white transition-colors duration-300 break-words">{data.marketAnalysis.targetMarket}</p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-3 text-black dark:text-white transition-colors duration-300">Target Customer Segments</h3>
            <div className="space-y-4">
              {data.marketAnalysis.targetCustomers.map((segment, idx) => (
                <div key={idx} className="border border-gray-300 dark:border-zinc-700 rounded-lg p-3 sm:p-4 bg-gray-100 dark:bg-zinc-800 hover:shadow-md transition-all duration-300">
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-2">
                    <h4 className="font-semibold text-sm sm:text-base text-[#FF5733] break-words">{segment.segment}</h4>
                    <span className="text-xs sm:text-sm font-bold text-black dark:text-white transition-colors duration-300 self-start">{segment.size}</span>
                  </div>
                  <p className="text-xs sm:text-sm text-black dark:text-zinc-300 mb-2 transition-colors duration-300 break-words">{segment.description}</p>
                  <div className="mt-2">
                    <p className="text-xs text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Key Needs:</p>
                    <div className="flex flex-wrap gap-2">
                      {segment.needs.map((need, nIdx) => (
                        <span key={nIdx} className="text-xs bg-[#FF5733] text-white px-2 py-1 rounded break-words">
                          {need}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Competitive Landscape removed */}
        </CardContent>
      </Card>

      {/* Organization & Management */}
      <Card id="organization-management" className="mb-6 shadow-lg bg-white dark:bg-white-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-white dark:bg-zinc-100 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-gray-900 dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#000000] font-light">04.</span>
              <Users className="w-5 h-5 sm:w-6 sm:h-6 text-[#000001]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Organization & Management</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 space-y-6 bg-white dark:bg-zinc-900 transition-colors duration-300 overflow-x-hidden">
          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white">Organizational Structure</h3>
            <p className="text-xs sm:text-sm md:text-base text-zinc-500 break-words">{data.organizationManagement.organizationalStructure}</p>
          </div>

          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-3 text-black dark:text-white">Management Team</h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
              {data.organizationManagement.managementTeam.map((member, idx) => (
                <div key={idx} className="border border-zinc-700 rounded-lg p-3 sm:p-4 bg-white dark:bg-black">
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 sm:gap-0 mb-2">
                    <h4 className="font-semibold text-sm sm:text-base text-black dark:text-white break-words">{member.role}</h4>
                    <span className="text-xs sm:text-sm font-bold text-green-400 self-start">{member.compensation}</span>
                  </div>
                  <p className="text-xs sm:text-sm text-black dark:text-white mb-2 break-words">{member.qualifications}</p>
                  <div className="mt-2">
                    <p className="text-xs text-black dark:text-white mb-1">Key Responsibilities:</p>
                    <ul className="list-disc list-inside text-xs sm:text-sm text-black dark:text-white space-y-0.5">
                      {member.responsibilities.map((resp, rIdx) => (
                        <li key={rIdx} className="break-words">{resp}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            <div>
              <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white">Advisory Board</h3>
              <ul className="list-disc list-inside text-black dark:text-white space-y-1 text-xs sm:text-sm">
                {data.organizationManagement.advisoryBoard.map((advisor, idx) => (
                  <li key={idx} className="break-words">{advisor}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white">Staffing Plan</h3>
              <div className="space-y-2 text-xs sm:text-sm">
                <div className="flex justify-between items-center gap-2">
                  <span className="text-black dark:text-white">Year 1:</span>
                  <span className="font-bold text-black dark:text-white break-words">{data.organizationManagement.staffingPlan.year1} employees</span>
                </div>
                <div className="flex justify-between items-center gap-2">
                  <span className="text-black dark:text-white">Year 2:</span>
                  <span className="font-bold text-black dark:text-white break-words">{data.organizationManagement.staffingPlan.year2} employees</span>
                </div>
                <div className="flex justify-between items-center gap-2">
                  <span className="text-black dark:text-white">Year 3:</span>
                  <span className="font-bold text-black dark:text-white break-words">{data.organizationManagement.staffingPlan.year3} employees</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Products & Services */}
      <Card id="products-services" className="mb-6 shadow-lg bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-gray-900 dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#FF5733] font-light">05.</span>
              <Package className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Products & Services</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 space-y-6 bg-white text-black dark:bg-zinc-900 transition-colors duration-300 overflow-x-hidden">
          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-3 text-black dark:text-white">Product/Service Offerings</h3>
            <div className="space-y-4">
              {data.productsServices.offerings.map((offering, idx) => (
                <div key={idx} className="bg-white dark:bg-black border border-zinc-700 rounded-lg p-3 sm:p-4">
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-2">
                    <h4 className="font-semibold text-sm sm:text-base text-black dark:text-white break-words">{offering.name}</h4>
                    <div className="text-left sm:text-right text-black">
                      <p className="font-bold text-base sm:text-lg text-black dark:text-white break-words">{offering.pricing}</p>
                      <p className="text-xs text-green-500">{offering.profitMargin} margin</p>
                    </div>
                  </div>
                  <p className="text-xs sm:text-sm text-black dark:text-white mb-3 break-words">{offering.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {offering.features.map((feature, fIdx) => (
                      <span key={fIdx} className="text-xs bg-[#FF5733] text-white px-2 py-1 rounded break-words">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 bg-gray-100 dark:bg-zinc-800 p-3 sm:p-4 rounded-lg border border-gray-300 dark:border-zinc-700 transition-colors duration-300">
            <div>
              <p className="text-xs text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Current Stage</p>
              <p className="font-semibold text-xs sm:text-sm text-black dark:text-white transition-colors duration-300 break-words">{data.productsServices.productDevelopment.currentStage}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">Development Timeline</p>
              <p className="font-semibold text-xs sm:text-sm text-black dark:text-white transition-colors duration-300 break-words">{data.productsServices.productDevelopment.developmentTimeline}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 dark:text-zinc-400 mb-1 transition-colors duration-300">R&D Budget</p>
              <p className="font-semibold text-xs sm:text-sm text-black dark:text-white transition-colors duration-300 break-words">{data.productsServices.productDevelopment.rdBudget}</p>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white transition-colors duration-300">Intellectual Property</h3>
            <ul className="list-disc list-inside text-black dark:text-zinc-300 space-y-1 text-xs sm:text-sm transition-colors duration-300">
              {data.productsServices.intellectualProperty.map((ip, idx) => (
                <li key={idx} className="break-words">{ip}</li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Marketing Strategy */}
      <Card id="marketing-strategy" className="mb-6 shadow-lg bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-gray-900 dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#FF5733] font-light">06.</span>
              <Target className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Marketing & Sales Strategy</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 space-y-6 bg-white dark:bg-zinc-900 transition-colors duration-300 overflow-x-hidden">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white">Branding Strategy</h3>
              <p className="text-xs sm:text-sm text-black dark:text-white break-words">{data.marketingStrategy.brandingStrategy}</p>
            </div>
            <div>
              <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white">Pricing Strategy</h3>
              <p className="text-xs sm:text-sm text-black dark:text-white break-words">{data.marketingStrategy.pricingStrategy}</p>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white">Distribution Channels</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {data.marketingStrategy.distributionChannels.map((channel, idx) => (
                <div key={idx} className="bg-purple-900 text-purple-100 px-3 py-2 rounded border border-purple-700 text-xs sm:text-sm break-words">
                  {channel}
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-3 text-black dark:text-white">Promotional Strategy</h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
              {data.marketingStrategy.promotionalStrategy.map((promo, idx) => (
                <div key={idx} className="border border-zinc-700 rounded-lg p-3 sm:p-4 bg-zinc-800">
                  <h4 className="font-semibold text-sm sm:text-base text-[#FF5733] mb-2 break-words">{promo.channel}</h4>
                  <div className="grid grid-cols-2 gap-2 text-xs sm:text-sm">
                    <div>
                      <p className="text-xs text-zinc-400">Budget</p>
                      <p className="font-semibold text-white break-words">{promo.budget}</p>
                    </div>
                    <div>
                      <p className="text-xs text-zinc-400">Expected ROI</p>
                      <p className="font-semibold text-green-400 break-words">{promo.expectedROI}</p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-xs text-zinc-400">Timeline</p>
                      <p className="font-semibold text-white break-words">{promo.timeline}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white dark:bg-black p-4 rounded-lg border border-zinc-700">
            <h3 className="font-semibold text-lg mb-3 text-black dark:text-white">Sales Strategy</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="space-y-2">
                <h4 className="font-semibold text-sm text-black dark:text-white">Sales Targets</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-black dark:text-white">Year 1:</span>
                    <span className="font-bold text-text-black dark:text-white">{data.marketingStrategy.salesStrategy.salesTargets.year1}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-black dark:text-white">Year 2:</span>
                    <span className="font-bold text-black dark:text-white">{data.marketingStrategy.salesStrategy.salesTargets.year2}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-black dark:text-white">Year 3:</span>
                    <span className="font-bold text-black dark:text-white">{data.marketingStrategy.salesStrategy.salesTargets.year3}</span>
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold text-sm text-black dark:text-white">Key Metrics</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-black dark:text-white">Customer Acquisition Cost:</span>
                    <span className="font-bold text-black dark:text-white">{data.marketingStrategy.salesStrategy.customerAcquisitionCost}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-black dark:text-white">Customer Lifetime Value:</span>
                    <span className="font-bold text-black dark:text-white">{data.marketingStrategy.salesStrategy.customerLifetimeValue}</span>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-sm text-black dark:text-white mb-2">Sales Process</h4>
              <ol className="list-decimal list-inside text-sm text-black dark:text-white space-y-1">
                {data.marketingStrategy.salesStrategy.salesProcess.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Operations Plan */}
      <Card id="operations-plan" className="mb-6 shadow-lg bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-gray-900 dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#FF5733] font-light">07.</span>
              <Cog className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Operations Plan</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 space-y-6 bg-white dark:bg-zinc-900 transition-colors duration-300 overflow-x-auto">

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 bg-zinc-800 p-3 sm:p-4 rounded-lg border border-zinc-700">
            <div>
              <p className="text-xs text-zinc-400 mb-1">Facility Type</p>
              <p className="font-semibold text-xs sm:text-sm text-white break-words">{data.operationsPlan.facilities.type}</p>
            </div>
            <div>
              <p className="text-xs text-zinc-400 mb-1">Location</p>
              <p className="font-semibold text-xs sm:text-sm text-white break-words">{data.operationsPlan.facilities.location}</p>
            </div>
            <div>
              <p className="text-xs text-zinc-400 mb-1">Size</p>
              <p className="font-semibold text-xs sm:text-sm text-white break-words">{data.operationsPlan.facilities.size}</p>
            </div>
            <div>
              <p className="text-xs text-zinc-400 mb-1">Cost</p>
              <p className="font-semibold text-xs sm:text-sm text-white break-words">{data.operationsPlan.facilities.cost}</p>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-3 text-black dark:text-white">Equipment & Technology</h3>
            <div className="overflow-x-auto -mx-4 sm:mx-0">
              <table className="w-full text-xs sm:text-sm min-w-[300px]">
                <thead className="bg-zinc-800 border-b border-zinc-700">
                  <tr>
                    <th className="text-left p-2 text-zinc-300">Item</th>
                    <th className="text-center p-2 text-zinc-300">Qty</th>
                    <th className="text-right p-2 text-zinc-300">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {data.operationsPlan.equipment.map((equip, idx) => (
                    <tr key={idx} className="border-b border-zinc-800">
                      <td className="p-2 text-black dark:text-white break-words">{equip.item}</td>
                      <td className="text-center p-2 text-black dark:text-white">{equip.quantity}</td>
                      <td className="text-right p-2 font-semibold text-black dark:text-white whitespace-nowrap">{equip.cost}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-3 text-black dark:text-white">Suppliers</h3>
            <div className="space-y-3">
              {data.operationsPlan.suppliers.map((supplier, idx) => (
                <div key={idx} className="border border-zinc-700 rounded-lg p-3 bg-zinc-800">
                  <h4 className="font-semibold text-sm sm:text-base text-[#FF5733] mb-2 break-words">{supplier.category}</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs sm:text-sm">
                    <div>
                      <p className="text-xs text-zinc-400">Supplier</p>
                      <p className="text-white break-words">{supplier.supplier}</p>
                    </div>
                    <div>
                      <p className="text-xs text-zinc-400">Terms</p>
                      <p className="text-white break-words">{supplier.terms}</p>
                    </div>
                    <div>
                      <p className="text-xs text-zinc-400">Backup</p>
                      <p className="text-white break-words">{supplier.backup}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white">Production Process</h3>
              <ol className="list-decimal list-inside text-xs sm:text-sm text-black dark:text-white space-y-1">
                {data.operationsPlan.productionProcess.map((step, idx) => (
                  <li key={idx} className="break-words">{step}</li>
                ))}
              </ol>
            </div>
            <div>
              <h3 className="font-semibold text-base sm:text-lg mb-2 text-black dark:text-white">Quality Control</h3>
              <ul className="list-disc list-inside text-xs sm:text-sm text-black dark:text-white space-y-1">
                {data.operationsPlan.qualityControl.map((qc, idx) => (
                  <li key={idx} className="break-words">{qc}</li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Financial Projections */}
      <Card id="financial-projections" className="mb-6 shadow-lg bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-gray-900 dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#FF5733] font-light">08.</span>
              <DollarSign className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Financial Projections</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 space-y-6 bg-white dark:bg-zinc-900 transition-colors duration-300 overflow-x-auto">
          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-3 text-black dark:text-white">Startup Costs</h3>
            <div className="space-y-2 mb-3">
              {data.financialProjections.startupCosts.categories.map((cat, idx) => (
                <div key={idx} className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-1 sm:gap-4 border-b border-zinc-700 pb-2">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-xs sm:text-sm text-black dark:text-white break-words">{cat.category}</p>
                    <p className="text-xs text-gray-500 dark:text-white break-words">{cat.description}</p>
                  </div>
                  <p className="font-bold text-sm ml-4 text-black dark:text-white">{cat.amount}</p>
                </div>
              ))}
            </div>
            <div className="flex justify-between items-center bg-purple-900 p-3 rounded font-bold border border-purple-700">
              <span className="text-purple-100">Total Startup Costs</span>
              <span className="text-lg text-white">{data.financialProjections.startupCosts.total}</span>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-lg mb-3 text-black dark:text-white">Funding Requirements</h3>
            <p className="text-sm mb-3 text-black dark:text-white">
              Total Needed: <span className="font-bold text-lg text-black dark:text-white">{data.financialProjections.fundingRequirements.totalNeeded}</span>
            </p>
            <div className="space-y-2">
              {data.financialProjections.fundingRequirements.sources.map((source, idx) => (
                <div key={idx} className="border border-zinc-700 rounded-lg p-3 bg-zinc-800">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-semibold text-white">{source.source}</p>
                      <p className="text-xs text-zinc-400">{source.terms}</p>
                    </div>
                    <p className="font-bold text-white">{source.amount}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-lg mb-3 text-black dark:text-white">3-Year Revenue Projections</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-zinc-800 border-b border-zinc-700">
                  <tr>
                    <th className="text-left p-2 text-zinc-300">Metric</th>
                    <th className="text-right p-2 text-zinc-300">Year 1</th>
                    <th className="text-right p-2 text-zinc-300">Year 2</th>
                    <th className="text-right p-2 text-zinc-300">Year 3</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-zinc-800">
                    <td className="p-2 font-semibold text-black dark:text-white">Revenue</td>
                    <td className="text-right p-2 text-black dark:text-white">{data.financialProjections.revenueProjections[0].revenue}</td>
                    <td className="text-right p-2 text-black dark:text-white">{data.financialProjections.revenueProjections[1].revenue}</td>
                    <td className="text-right p-2 text-black dark:text-white">{data.financialProjections.revenueProjections[2].revenue}</td>
                  </tr>
                  <tr className="border-b border-zinc-800">
                    <td className="p-2 text-black dark:text-white">COGS</td>
                    <td className="text-right p-2 text-black dark:text-white">{data.financialProjections.revenueProjections[0].cogs}</td>
                    <td className="text-right p-2 text-black dark:text-white">{data.financialProjections.revenueProjections[1].cogs}</td>
                    <td className="text-right p-2 text-black dark:text-white">{data.financialProjections.revenueProjections[2].cogs}</td>
                  </tr>
                  <tr className="border-b border-zinc-800 bg-zinc-800">
                    <td className="p-2 font-semibold text-white">Gross Profit</td>
                    <td className="text-right p-2 font-semibold text-white">{data.financialProjections.revenueProjections[0].grossProfit}</td>
                    <td className="text-right p-2 font-semibold text-white">{data.financialProjections.revenueProjections[1].grossProfit}</td>
                    <td className="text-right p-2 font-semibold text-white">{data.financialProjections.revenueProjections[2].grossProfit}</td>
                  </tr>
                  <tr className="border-b border-zinc-800">
                    <td className="p-2 text-xs text-black dark:text-white">Gross Margin</td>
                    <td className="text-right p-2 text-xs text-black dark:text-white">{data.financialProjections.revenueProjections[0].grossMargin}</td>
                    <td className="text-right p-2 text-xs text-black dark:text-white">{data.financialProjections.revenueProjections[1].grossMargin}</td>
                    <td className="text-right p-2 text-xs text-black dark:text-white">{data.financialProjections.revenueProjections[2].grossMargin}</td>
                  </tr>
                  <tr className="border-b border-zinc-800">
                    <td className="p-2 text-black dark:text-white">Operating Expenses</td>
                    <td className="text-right p-2 text-black dark:text-white">{data.financialProjections.revenueProjections[0].operatingExpenses}</td>
                    <td className="text-right p-2 text-black dark:text-white">{data.financialProjections.revenueProjections[1].operatingExpenses}</td>
                    <td className="text-right p-2 text-black dark:text-white">{data.financialProjections.revenueProjections[2].operatingExpenses}</td>
                  </tr>
                  <tr className="border-b border-zinc-800 bg-green-900">
                    <td className="p-2 font-semibold text-white">Net Profit</td>
                    <td className="text-right p-2 font-semibold text-green-300">{data.financialProjections.revenueProjections[0].netProfit}</td>
                    <td className="text-right p-2 font-semibold text-green-300">{data.financialProjections.revenueProjections[1].netProfit}</td>
                    <td className="text-right p-2 font-semibold text-green-300">{data.financialProjections.revenueProjections[2].netProfit}</td>
                  </tr>
                  <tr>
                    <td className="p-2 text-xs text-black dark:text-white">Net Margin</td>
                    <td className="text-right p-2 text-xs text-green-600">{data.financialProjections.revenueProjections[0].netMargin}</td>
                    <td className="text-right p-2 text-xs text-green-600">{data.financialProjections.revenueProjections[1].netMargin}</td>
                    <td className="text-right p-2 text-xs text-green-600">{data.financialProjections.revenueProjections[2].netMargin}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-zinc-800 p-4 rounded-lg border border-zinc-700">
            <h3 className="font-semibold text-lg mb-3 text-white">Financial Assumptions</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
              <div>
                <p className="text-xs text-zinc-400">Revenue Growth Rate</p>
                <p className="font-semibold text-white">{data.financialProjections.financialAssumptions.revenueGrowthRate}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-400">COGS Percentage</p>
                <p className="font-semibold text-white">{data.financialProjections.financialAssumptions.cogsPercentage}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-400">Operating Expense Growth</p>
                <p className="font-semibold text-white">{data.financialProjections.financialAssumptions.operatingExpenseGrowth}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-400">Corporate Tax Rate</p>
                <p className="font-semibold text-white">{data.financialProjections.financialAssumptions.corporateTaxRate}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-400">Inflation Rate</p>
                <p className="font-semibold text-white">{data.financialProjections.financialAssumptions.inflationRate}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">GDP Growth Rate</p>
                <p className="font-semibold">{data.financialProjections.financialAssumptions.gdpGrowthRate}</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-3 rounded border border-blue-200">
              <p className="text-xs text-blue-600 mb-1">Break-Even Month</p>
              <p className="text-lg font-bold text-blue-900">Month {data.financialProjections.cashFlowProjection.breakEvenMonth}</p>
            </div>
            <div className="bg-amber-50 p-3 rounded border border-amber-200">
              <p className="text-xs text-amber-600 mb-1">Minimum Cash Balance</p>
              <p className="text-lg font-bold text-amber-900">{data.financialProjections.cashFlowProjection.minimumCashBalance}</p>
            </div>
            <div className="bg-purple-50 p-3 rounded border border-purple-200">
              <p className="text-xs text-purple-600 mb-1">Monthly Cash Flow</p>
              <p className="text-lg font-bold text-purple-900">{data.financialProjections.cashFlowProjection.year1Monthly ? 'Tracked' : 'Quarterly'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Analysis */}
      <Card id="risk-analysis" className="mb-6 shadow-lg bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-gray-900 dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#FF5733] font-light">09.</span>
              <AlertTriangle className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Risk Analysis & Mitigation</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 space-y-6 bg-white dark:bg-zinc-900 transition-colors duration-300 overflow-x-hidden">
          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-3">Risk Assessment</h3>
            <div className="space-y-3">
              {data.riskAnalysis.risks.map((risk, idx) => (
                <div key={idx} className="border border-slate-200 rounded-lg p-3 sm:p-4">
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-2">
                    <h4 className="font-semibold text-sm sm:text-base text-purple-500 break-words">{risk.category}</h4>
                    <div className="flex flex-wrap gap-2">
                      <span className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
                        risk.likelihood === 'High' ? 'bg-red-100 text-red-700' :
                        risk.likelihood === 'Medium' ? 'bg-amber-100 text-amber-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {risk.likelihood} likelihood
                      </span>
                      <span className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
                        risk.impact === 'High' ? 'bg-red-100 text-red-700' :
                        risk.impact === 'Medium' ? 'bg-amber-100 text-amber-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {risk.impact} impact
                      </span>
                    </div>
                  </div>
                  <p className="text-xs sm:text-sm text-black dark:text-white mb-2 break-words">{risk.description}</p>
                  <div className="bg-green-50 p-2 rounded text-xs sm:text-sm">
                    <p className="text-xs text-green-600 mb-1">Mitigation Strategy:</p>
                    <p className="text-green-800 break-words">{risk.mitigation}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-2">Contingency Plans</h3>
            <ul className="list-disc list-inside text-slate-700 dark:text-white space-y-1 text-xs sm:text-sm">
              {data.riskAnalysis.contingencyPlans.map((plan, idx) => (
                <li key={idx} className="break-words">{plan}</li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-base sm:text-lg mb-3">Insurance Coverage</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {data.riskAnalysis.insurance.map((ins, idx) => (
                <div key={idx} className="border border-slate-200 rounded-lg p-3">
                  <h4 className="font-semibold text-xs sm:text-sm mb-2 break-words">{ins.type}</h4>
                  <div className="flex flex-col sm:flex-row sm:justify-between gap-2 text-xs sm:text-sm">
                    <div>
                      <p className="text-xs text-slate-500">Coverage</p>
                      <p className="font-semibold break-words">{ins.coverage}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Annual Cost</p>
                      <p className="font-semibold text-green-600 break-words">{ins.annualCost}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Implementation Timeline */}
      <Card id="implementation-timeline" className="mb-6 shadow-lg bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-gray-900 dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#FF5733] font-light">10.</span>
              <Calendar className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Implementation Timeline</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 space-y-6 overflow-x-hidden">
          {data.implementationTimeline.phases.map((phase, idx) => (
            <div key={idx} className="border-l-4 border-[#FF5733] pl-3 sm:pl-4">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-3">
                <h3 className="font-semibold text-base sm:text-lg text-black dark:text-white break-words">{phase.phase}</h3>
                <span className="text-xs sm:text-sm bg-purple-900 text-purple-100 px-2 py-1 rounded border border-purple-700 self-start whitespace-nowrap">{phase.duration}</span>
              </div>
              <div className="space-y-2">
                {phase.milestones.map((milestone, mIdx) => (
                  <div key={mIdx} className="bg-zinc-100 dark:bg-black p-3 rounded border border-zinc-700">
                    <div className="flex justify-between items-start mb-1">
                      <p className="font-semibold text-xs sm:text-sm text-black dark:text-white break-words">{milestone.milestone}</p>
                      
                    </div>
                    <div className="flex flex-col sm:flex-row sm:justify-between gap-1 text-xs text-black dark:text-white">
                      <span className="break-words">Owner: {milestone.owner}</span>
                      <span className="whitespace-nowrap">Deadline: {milestone.deadline}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Exit Strategy */}
      <Card id="exit-strategy" className="mb-6 shadow-lg bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 transition-colors duration-300 overflow-hidden">
        <CardHeader className="bg-gray-100 dark:bg-zinc-800 border-b border-gray-200 dark:border-zinc-700 transition-colors duration-300 p-4 sm:p-6">
          <CardTitle className="flex flex-col sm:flex-row sm:items-center gap-2 text-gray-900 dark:text-white font-serif transition-colors duration-300 text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-2 w-full sm:w-auto">
              <span className="text-xl sm:text-2xl text-[#FF5733] font-light">11.</span>
              <LogOut className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF5733]" />
            </div>
            <span className="text-base sm:text-lg md:text-xl break-words">Exit Strategy</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 bg-white dark:bg-zinc-900 transition-colors duration-300 overflow-x-hidden">
          <div className="space-y-4">
            {data.exitStrategy.options.map((option, idx) => (
              <div key={idx} className="border border-zinc-700 rounded-lg p-3 sm:p-4 bg-zinc-800">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-3">
                  <h3 className="font-semibold text-base sm:text-lg text-[#FF5733] break-words">{option.strategy}</h3>
                  <div className="text-left sm:text-right">
                    <p className="text-xs text-zinc-400">Expected Return</p>
                    <p className="font-bold text-sm sm:text-base text-white break-words">{option.expectedReturn}</p>
                  </div>
                </div>
                <div className="mb-3">
                  <p className="text-xs sm:text-sm text-zinc-300 break-words">
                    <span className="font-semibold">Timeline:</span> {option.timeline}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-400 mb-1">Required Conditions:</p>
                  <ul className="list-disc list-inside text-xs sm:text-sm text-zinc-300 space-y-0.5">
                    {option.conditions.map((condition, cIdx) => (
                      <li key={cIdx} className="break-words">{condition}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-center py-6">
        <p className="text-xs text-gray-500 dark:text-zinc-600">
          Business plan based on research-backed market analysis, real competitor data, and verified financial projections for {data.country}
        </p>
      </div>
      </div>
    </div>
  );
}