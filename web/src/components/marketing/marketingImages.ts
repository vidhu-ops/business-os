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
    src: "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1600&q=80",
    alt: "Founders collaborating on a business plan",
    caption: "Founders planning together",
  },
  "mobile-founder": {
    src: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=1200&q=80",
    alt: "Founder smiling while working on a laptop",
    caption: "Work from anywhere",
  },
  "strategy-meeting": {
    src: "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?auto=format&fit=crop&w=1600&q=80",
    alt: "Team strategy discussion in a modern office",
    caption: "Strategy sessions",
  },
  "market-research": {
    src: "https://images.unsplash.com/photo-1551836022-d5d88e9218df?auto=format&fit=crop&w=1200&q=80",
    alt: "Analyst discussing market insights with a colleague",
    caption: "Market intelligence",
  },
  "msme-business": {
    src: "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1200&q=80",
    alt: "Small business owner talking with their team",
    caption: "Built for MSMEs",
  },
  workspace: {
    src: "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1200&q=80",
    alt: "Founders collaborating around a laptop",
    caption: "Your workspace",
  },
  presentation: {
    src: "https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1200&q=80",
    alt: "Team presenting business results in a meeting",
    caption: "Investor-ready output",
  },
  collaboration: {
    src: "https://images.unsplash.com/photo-1521737711867-e3b97375f902?auto=format&fit=crop&w=1200&q=80",
    alt: "Colleagues collaborating in a bright office",
    caption: "Shared deliverables",
  },
  analytics: {
    src: "/marketing/people/solution.jpg",
    alt: "Operators reviewing growth plans together",
    caption: "Data-backed decisions",
  },
  healthcare: {
    src: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=1200&q=80",
    alt: "Healthcare professional smiling in a clinic",
    caption: "Healthcare verticals",
  },
  retail: {
    src: "https://images.unsplash.com/photo-1556740738-b6a63e27c4df?auto=format&fit=crop&w=1200&q=80",
    alt: "Retail founder helping a customer in store",
    caption: "Retail & D2C",
  },
  logistics: {
    src: "https://images.unsplash.com/photo-1600880292089-90a7e086ee0c?auto=format&fit=crop&w=1200&q=80",
    alt: "Operations team planning logistics work together",
    caption: "Operations & logistics",
  },
};
