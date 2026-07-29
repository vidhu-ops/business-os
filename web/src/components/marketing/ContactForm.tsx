"use client";
import { FormEvent, useState } from "react";

export function ContactForm() {
  const [sent, setSent] = useState(false);
  function onSubmit(e: FormEvent) { e.preventDefault(); setSent(true); }
  if (sent) {
    return (<div className="iid-card"><p className="font-display text-lg font-bold text-emerald-300">Thanks - we will contact you soon.</p></div>);
  }
  return (
    <form className="iid-card space-y-3" onSubmit={onSubmit}>
      <input className="iid-input" placeholder="Name" required />
      <input className="iid-input" type="email" placeholder="Email" required />
      <textarea className="iid-input min-h-28" placeholder="Message" required />
      <button className="iid-btn iid-btn-primary w-full" type="submit">Submit</button>
    </form>
  );
}