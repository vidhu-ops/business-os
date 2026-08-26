"use client";

import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

const PARTNER_TYPES = [
  { value: "service_provider", label: "Service provider" },
  { value: "vendor", label: "Vendor / supplier" },
  { value: "consultant", label: "Consultant" },
  { value: "agency", label: "Agency partner" },
  { value: "technology", label: "Technology partner" },
];

const CATEGORY_SUGGESTIONS = [
  "Legal",
  "Accounting",
  "Marketing",
  "HR",
  "IT",
  "Logistics",
  "Manufacturing",
  "Design",
  "Compliance",
  "Funding",
];

function Req({ children }: { children: React.ReactNode }) {
  return (
    <span>
      {children} <abbr title="required" className="partner-req">*</abbr>
    </span>
  );
}

export function PartnerForm() {
  const [step, setStep] = useState<1 | 2>(1);
  const [companyName, setCompanyName] = useState("");
  const [contactName, setContactName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  const [country, setCountry] = useState("");
  const [servicesOffered, setServicesOffered] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [description, setDescription] = useState("");
  const [website, setWebsite] = useState("");
  const [yearsExperience, setYearsExperience] = useState("");
  const [partnerType, setPartnerType] = useState("service_provider");
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [docFile, setDocFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState<{ id: string; company: string } | null>(null);

  function toggleCategory(cat: string) {
    setCategories((prev) => (prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]));
  }

  function goNext() {
    setError("");
    if (!companyName.trim() || !contactName.trim() || !email.trim() || !phone.trim() || !location.trim() || !country.trim()) {
      setError("Please complete all required business fields before continuing.");
      return;
    }
    setStep(2);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!logoFile) {
      setError("Please upload your company logo.");
      return;
    }
    if (!docFile) {
      setError("Please upload your company registration document.");
      return;
    }
    if (!servicesOffered.trim()) {
      setError("Please describe the services you offer.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const form = new FormData();
      form.append("company_name", companyName);
      form.append("contact_name", contactName);
      form.append("email", email);
      form.append("phone", phone);
      form.append("location", location);
      form.append("country", country);
      form.append("services_offered", servicesOffered);
      form.append("service_categories", categories.join(", "));
      form.append("description", description);
      form.append("website", website);
      if (yearsExperience) form.append("years_experience", yearsExperience);
      form.append("partner_type", partnerType);
      form.append("logo", logoFile);
      form.append("registration_doc", docFile);

      const result = await api.registerPartner(form);
      setSuccess({
        id: result.id,
        company: String(result.provider?.company_name || companyName),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit application");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="iid-card partner-success">
        <p className="font-display text-xl font-bold text-emerald-400">Application received.</p>
        <p className="muted mt-3">
          <strong>{success.company}</strong> is registered for review (ID: {success.id}). Once we verify your documents,
          your logo and company name can appear in the partner section.
        </p>
        <p className="text-sm muted mt-4">We will contact you at {email} when your listing is approved.</p>
      </div>
    );
  }

  return (
    <form className="iid-card partner-form space-y-5" onSubmit={onSubmit}>
      <div className="partner-steps" aria-label="Application progress">
        <span className={step === 1 ? "is-active" : ""}>1. Business info</span>
        <span className={step === 2 ? "is-active" : ""}>2. Services &amp; documents</span>
      </div>
      <p className="text-xs muted">Fields marked <abbr title="required">*</abbr> are required.</p>

      {step === 1 ? (
        <div className="partner-form-grid">
          <label className="partner-field">
            <Req>Company / business name</Req>
            <input className="iid-input" value={companyName} onChange={(e) => setCompanyName(e.target.value)} required />
          </label>
          <label className="partner-field">
            <Req>Contact name</Req>
            <input className="iid-input" value={contactName} onChange={(e) => setContactName(e.target.value)} required />
          </label>
          <label className="partner-field">
            <Req>Email</Req>
            <input className="iid-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label className="partner-field">
            <Req>Phone</Req>
            <input className="iid-input" type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} required />
          </label>
          <label className="partner-field">
            <Req>City / region</Req>
            <input className="iid-input" value={location} onChange={(e) => setLocation(e.target.value)} required />
          </label>
          <label className="partner-field">
            <Req>Country</Req>
            <input className="iid-input" value={country} onChange={(e) => setCountry(e.target.value)} required />
          </label>
          <label className="partner-field">
            <span>Website (optional)</span>
            <input className="iid-input" type="url" value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://" />
          </label>
          <label className="partner-field">
            <span>Years in business (optional)</span>
            <input
              className="iid-input"
              type="number"
              min={0}
              max={80}
              value={yearsExperience}
              onChange={(e) => setYearsExperience(e.target.value)}
              placeholder="e.g. 5"
            />
          </label>
        </div>
      ) : (
        <div className="partner-form-grid">
          <label className="partner-field partner-field-full">
            <Req>Partner type</Req>
            <select className="iid-input" value={partnerType} onChange={(e) => setPartnerType(e.target.value)} required>
              {PARTNER_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label className="partner-field partner-field-full">
            <Req>What services do you offer?</Req>
            <textarea
              className="iid-input min-h-[100px]"
              value={servicesOffered}
              onChange={(e) => setServicesOffered(e.target.value)}
              placeholder="e.g. GST filing, company registration, digital marketing for D2C brands..."
              required
            />
          </label>
          <div className="partner-field partner-field-full">
            <span>Categories (optional — tap to select)</span>
            <div className="partner-chips">
              {CATEGORY_SUGGESTIONS.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  className={`partner-chip ${categories.includes(cat) ? "is-on" : ""}`}
                  onClick={() => toggleCategory(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
          <label className="partner-field partner-field-full">
            <span>About your business (optional)</span>
            <textarea
              className="iid-input min-h-[120px]"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Who you serve, pricing model, certifications, languages..."
            />
          </label>
          <label className="partner-field partner-field-full">
            <Req>Company logo (PNG, JPG, SVG — max 2 MB)</Req>
            <input
              className="iid-input file:mr-3 file:rounded-full file:border-0 file:bg-[var(--iid-blue)] file:px-4 file:py-2 file:text-xs file:font-bold file:text-white"
              type="file"
              accept=".png,.jpg,.jpeg,.webp,.svg,image/*"
              onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
              required
            />
            {logoFile ? <span className="text-xs muted">{logoFile.name}</span> : null}
          </label>
          <label className="partner-field partner-field-full">
            <Req>Company registration / incorporation document (PDF or image — max 10 MB)</Req>
            <input
              className="iid-input file:mr-3 file:rounded-full file:border-0 file:bg-[var(--iid-blue)] file:px-4 file:py-2 file:text-xs file:font-bold file:text-white"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.doc,.docx,application/pdf,image/*"
              onChange={(e) => setDocFile(e.target.files?.[0] || null)}
              required
            />
            {docFile ? <span className="text-xs muted">{docFile.name}</span> : null}
          </label>
        </div>
      )}

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <div className="flex flex-wrap gap-2">
        {step === 2 ? (
          <button type="button" className="iid-btn iid-btn-ghost" onClick={() => setStep(1)}>
            Back
          </button>
        ) : null}
        {step === 1 ? (
          <button type="button" className="iid-btn iid-btn-primary" onClick={goNext}>
            Continue
          </button>
        ) : (
          <button className="iid-btn iid-btn-primary" type="submit" disabled={loading}>
            {loading ? "Submitting application…" : "Submit application"}
          </button>
        )}
      </div>
    </form>
  );
}
