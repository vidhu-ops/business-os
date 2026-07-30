export type MarketingPhotoId =
  | "founder-team"
  | "mobile-founder"
  | "strategy-meeting"
  | "market-research"
  | "msme-business"
  | "workspace"
  | "presentation"
  | "collaboration"
  | "analytics"
  | "logistics"
  | "healthcare"
  | "retail";

export const MARKETING_PHOTOS: Record<
  MarketingPhotoId,
  { src: string; alt: string; caption?: string }
> = {
  "founder-team": {
    src: "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80",
    alt: "Founders collaborating on a business plan",
    caption: "Founders planning together",
  },
  "mobile-founder": {
    src: "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?auto=format&fit=crop&w=1200&q=80",
    alt: "Founder reviewing business insights on a phone",
    caption: "Work from anywhere",
  },
  "strategy-meeting": {
    src: "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?auto=format&fit=crop&w=1200&q=80",
    alt: "Team strategy discussion in a modern office",
    caption: "Strategy sessions",
  },
  "market-research": {
    src: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80",
    alt: "Analyst reviewing market data and charts",
    caption: "Market intelligence",
  },
  "msme-business": {
    src: "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1200&q=80",
    alt: "Small business owner at work",
    caption: "Built for MSMEs",
  },
  workspace: {
    src: "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1200&q=80",
    alt: "Entrepreneur working on a laptop in a cafe",
    caption: "Your workspace",
  },
  presentation: {
    src: "https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1200&q=80",
    alt: "Team presenting business results",
    caption: "Investor-ready output",
  },
  collaboration: {
    src: "https://images.unsplash.com/photo-1573164713714-d95e436ab8d6?auto=format&fit=crop&w=1200&q=80",
    alt: "Colleagues reviewing documents together",
    caption: "Shared deliverables",
  },
  analytics: {
    src: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80",
    alt: "Business analytics dashboard on screen",
    caption: "Data-backed decisions",
  },
  logistics: {
    src: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1200&q=80",
    alt: "Warehouse and supply chain operations",
    caption: "Operations & logistics",
  },
  healthcare: {
    src: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1200&q=80",
    alt: "Healthcare professional using technology",
    caption: "Healthcare verticals",
  },
  retail: {
    src: "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1200&q=80",
    alt: "Retail store with modern merchandising",
    caption: "Retail & D2C",
  },
};
