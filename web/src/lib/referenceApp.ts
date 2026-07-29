export const REFERENCE_REPLIT_APP_URL = "https://aggressive-crushing-learning.replit.app";

export type ValidationSectionId = "plan-it-out" | "business-planning";

export const VALIDATION_SECTIONS: Array<{
  id: ValidationSectionId;
  label: string;
  hubButton: string;
  description: string;
}> = [
  {
    id: "plan-it-out",
    label: "Plan It Out",
    hubButton: "Plan It Out",
    description:
      "Build a step-by-step action plan with timelines, budgets, local vendors, and implementation milestones tailored to your idea and market.",
  },
  {
    id: "business-planning",
    label: "Business Planning",
    hubButton: "Business Plan",
    description:
      "Generate a complete business plan with financial projections, market positioning, and strategy sections for your idea and geography.",
  },
];