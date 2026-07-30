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

export function PartnerForm() {
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
          your logo and company name will appear in the homepage partner banner.
        </p>
        <p className="text-sm muted mt-4">We will contact you at {email} when your listing is approved.</p>
      </div>
    );
  }

  return (
    <form className="iid-card partner-form space-y-5" onSubmit={onSubmit}>
      <div className="partner-form-grid">
        <label className="partner-field">
          <span>Company / business name</span>
          <input className="iid-input" value={companyName} onChange={(e) => setCompanyName(e.target.value)} required />
        </label>
        <label className="partner-field">
          <span>Contact name</span>
          <input className="iid-input" value={contactName} onChange={(e) => setContactName(e.target.value)} required />
        </label>
        <label className="partner-field">
          <span>Email</span>
          <input className="iid-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label className="partner-field">
          <span>Phone</span>
          <input className="iid-input" type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} required />
        </label>
        <label className="partner-field">
          <span>City / region</span>
          <input className="iid-input" value={location} onChange={(e) => setLocation(e.target.value)} required />
        </label>
        <label className="partner-field">
          <span>Country</span>
          <input className="iid-input" value={country} onChange={(e) => setCountry(e.target.value)} required />
        </label>
        <label className="partner-field partner-field-full">
          <span>Company logo (PNG, JPG, SVG — max 2 MB)</span>
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
          <span>Company registration / incorporation document (PDF or image — max 10 MB)</span>
          <input
            className="iid-input file:mr-3 file:rounded-full file:border-0 file:bg-[var(--iid-blue)] file:px-4 file:py-2 file:text-xs file:font-bold file:text-white"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.doc,.docx,application/pdf,image/*"
            onChange={(e) => setDocFile(e.target.files?.[0] || null)}
            required
          />
          {docFile ? <span className="text-xs muted">{docFile.name}</span> : null}
        </label>
        <label className="partner-field partner-field-full">
          <span>Partner type</span>
          <select className="iid-input" value={partnerType} onChange={(e) => setPartnerType(e.target.value)}>
            {PARTNER_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        <label className="partner-field partner-field-full">
          <span>What services do you offer?</span>
          <textarea
            className="iid-input min-h-[100px]"
            value={servicesOffered}
            onChange={(e) => setServicesOffered(e.target.value)}
            placeholder="e.g. GST filing, company registration, digital marketing for D2C brands..."
            required
          />
        </label>
        <div className="partner-field partner-field-full">
          <span>Categories (tap to select)</span>
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
          <span>About your business</span>
          <textarea
            className="iid-input min-h-[120px]"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Who you serve, pricing model, certifications, languages..."
          />
        </label>
        <label className="partner-field">
          <span>Website (optional)</span>
          <input className="iid-input" type="url" value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://" />
        </label>
        <label className="partner-field">
          <span>Years in business</span>
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

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <button className="iid-btn iid-btn-primary w-full sm:w-auto" type="submit" disabled={loading}>
        {loading ? "Submitting application…" : "Submit service provider application"}
      </button>
    </form>
  );
}
