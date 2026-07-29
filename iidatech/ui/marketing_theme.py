"""IIDATECH marketing — magnetic Business OS typography + working nav."""

FIGMA_DESIGN_URL = "https://www.figma.com/design/2BzVQuE3l29YkGiotdXeau/IIDATECH-Founder-App?node-id=9-2"
WIX_REFERENCE_URL = "https://vidhugupta1996.wixstudio.com/my-site-5"

MARKETING_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
  --iid-ink: #05070f;
  --iid-navy: #0a1020;
  --iid-panel: #101828;
  --iid-panel-2: #162033;
  --iid-blue: #0b5fff;
  --iid-blue-dark: #0846b7;
  --iid-sky: #a8c0ff;
  --iid-text: #f7f9ff;
  --iid-muted: #9aa8c2;
  --iid-line: #243049;
  --iid-max: 1160px;
  --font-display: 'Syne', system-ui, sans-serif;
  --font-body: 'Plus Jakarta Sans', system-ui, sans-serif;
}

html { scroll-behavior: smooth; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container {
  padding: 0 1.25rem 3.5rem !important;
  max-width: var(--iid-max) !important;
}
html, body, [data-testid="stAppViewContainer"] {
  background: var(--iid-ink) !important;
  font-family: var(--font-body) !important;
  -webkit-font-smoothing: antialiased;
  color: var(--iid-text) !important;
}

.iid-page { color: var(--iid-text); }

/* ===== NAV with real anchors ===== */
.iid-nav-shell {
  position: sticky; top: 0; z-index: 1000;
  background: rgba(5,7,15,0.9);
  backdrop-filter: blur(18px) saturate(140%);
  border-bottom: 1px solid rgba(36,48,73,0.9);
  margin: 0 -1.25rem;
  padding: 0.85rem 1.25rem;
}
.iid-nav {
  max-width: var(--iid-max); margin: 0 auto;
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
}
.iid-logo {
  font-family: var(--font-display);
  font-size: 1.05rem; font-weight: 800; letter-spacing: 0.2em;
  text-transform: uppercase; color: var(--iid-text); margin: 0; white-space: nowrap;
}
.iid-logo span { color: var(--iid-blue); }
.iid-nav-links {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: 0.35rem 0.9rem;
}
.iid-nav-links a {
  font-family: var(--font-body);
  font-size: 0.78rem; font-weight: 600; letter-spacing: 0.04em;
  color: var(--iid-muted); text-decoration: none;
  padding: 0.35rem 0.2rem;
  transition: color 0.15s ease;
}
.iid-nav-links a:hover { color: #fff; }
.iid-nav-cta {
  display: inline-flex; align-items: center; justify-content: center;
  font-family: var(--font-body) !important;
  font-size: 0.72rem !important; font-weight: 700 !important;
  letter-spacing: 0.08em !important; text-transform: uppercase !important;
  color: #fff !important; text-decoration: none !important;
  background: var(--iid-blue) !important;
  border: none !important; border-radius: 999px !important;
  padding: 0.7rem 1.15rem !important;
  box-shadow: none !important;
  white-space: nowrap;
}
.iid-nav-cta:hover { background: var(--iid-blue-dark) !important; color: #fff !important; }
.iid-nav-start { max-width: 180px; margin: 0.35rem 0 0.75rem auto; }


/* Nav row Streamlit buttons */
div[data-testid="stHorizontalBlock"] button {
  border-radius: 999px !important;
  box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) button[kind="secondary"] {
  background: transparent !important;
  color: var(--iid-muted) !important;
  border: 1px solid transparent !important;
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em !important;
  text-transform: none !important;
  min-height: 2.2rem !important;
}
div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
  color: #fff !important;
  background: var(--iid-panel) !important;
  border-color: var(--iid-line) !important;
  box-shadow: none !important;
}

/* ===== HERO ===== */
.iid-hero {
  position: relative;
  background:
    radial-gradient(ellipse 80% 70% at 100% -10%, rgba(11,95,255,0.35), transparent 55%),
    radial-gradient(ellipse 50% 40% at 0% 100%, rgba(11,95,255,0.12), transparent 50%),
    var(--iid-navy);
  border: 1px solid var(--iid-line);
  border-radius: 28px;
  margin: 0.5rem 0 1rem;
  overflow: hidden;
}
.iid-hero-grid {
  position: relative;
  display: grid;
  grid-template-columns: 1.45fr 0.95fr;
  gap: 2.25rem;
  padding: 3.25rem 2.75rem 2.85rem;
  align-items: center;
}
@media (max-width: 860px) {
  .iid-hero-grid { grid-template-columns: 1fr; padding: 2.25rem 1.4rem; gap: 1.75rem; }
}
.iid-hero .eyebrow {
  font-family: var(--font-body);
  font-size: 0.7rem; font-weight: 600; letter-spacing: 0.32em;
  text-transform: uppercase; color: var(--iid-sky); margin: 0 0 1.25rem;
}
.iid-hero h1 {
  font-family: var(--font-display);
  font-size: clamp(2.6rem, 6.2vw, 4.4rem);
  font-weight: 700; letter-spacing: -0.045em;
  line-height: 0.98; margin: 0 0 1.15rem; color: var(--iid-text);
}
.iid-hero h1 .os {
  display: block;
  font-weight: 500; font-size: 0.42em; letter-spacing: -0.02em;
  color: rgba(247,249,255,0.72);
  margin-bottom: 0.35rem; line-height: 1.15;
}
.iid-hero h1 em {
  font-style: normal; font-weight: 800; color: var(--iid-blue);
  display: block; line-height: 0.95; margin: 0;
  letter-spacing: -0.05em;
}
.iid-hero .pipe {
  display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: center;
  margin: 0 0 1.25rem;
  font-family: var(--font-body);
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.16em;
}
.iid-hero .pipe span { color: var(--iid-sky); }
.iid-hero .pipe i { font-style: normal; color: rgba(11,95,255,0.7); margin: 0 0.2rem; }
.iid-hero .lead {
  font-family: var(--font-body);
  font-size: 1.12rem; line-height: 1.7; font-weight: 400;
  color: var(--iid-muted); margin: 0; max-width: 34rem;
}
.iid-hero-panel {
  background: rgba(16,24,40,0.85);
  border: 1px solid var(--iid-line);
  border-radius: 20px;
  padding: 0.5rem 1.5rem;
  backdrop-filter: blur(8px);
}
.iid-hero-panel .stat {
  display: grid; grid-template-columns: auto 1fr; gap: 1rem;
  align-items: center;
  padding: 1.05rem 0;
  border-bottom: 1px solid var(--iid-line);
}
.iid-hero-panel .stat:last-child { border-bottom: none; }
.iid-hero-panel strong {
  font-family: var(--font-display);
  font-size: 1.85rem; font-weight: 800; color: var(--iid-blue);
  letter-spacing: -0.04em; min-width: 3.6rem; line-height: 1;
}
.iid-hero-panel span {
  font-size: 0.9rem; color: var(--iid-muted); line-height: 1.4;
}

.iid-cta-row { max-width: 420px; margin: 0 0 2.75rem; }

/* ===== SECTIONS ===== */
.iid-section { margin-bottom: 3.5rem; scroll-margin-top: 5.5rem; }
.iid-section-dark { scroll-margin-top: 5.5rem; }
.iid-section-head { margin-bottom: 1.75rem; max-width: 780px; }
.iid-label {
  display: block;
  font-family: var(--font-body);
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.26em;
  text-transform: uppercase; color: var(--iid-blue); margin-bottom: 0.85rem;
}
.iid-h2 {
  font-family: var(--font-display);
  font-size: clamp(2rem, 4.4vw, 3.15rem);
  font-weight: 700; letter-spacing: -0.04em;
  line-height: 1.05; margin: 0 0 0.9rem; color: var(--iid-text);
}
.iid-sub {
  font-family: var(--font-body);
  color: var(--iid-muted); line-height: 1.75; font-size: 1.08rem;
  margin: 0; max-width: 38rem;
}

.iid-manifesto {
  background: linear-gradient(160deg, #101828 0%, #0c1424 100%);
  border: 1px solid var(--iid-line);
  border-radius: 24px;
  padding: 2.75rem 2.35rem;
  margin: 0 0 1rem;
  scroll-margin-top: 5.5rem;
}
.iid-manifesto h2 {
  font-family: var(--font-display);
  font-size: clamp(2rem, 4.5vw, 3.2rem);
  font-weight: 700; letter-spacing: -0.04em;
  margin: 0 0 1rem; line-height: 1.05; color: var(--iid-text);
  max-width: 16ch;
}
.iid-manifesto p {
  color: var(--iid-muted); margin: 0; font-size: 1.08rem;
  line-height: 1.75; max-width: 42rem;
}
.iid-pain-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.85rem;
  margin-top: 1.75rem;
}
@media (max-width: 800px) { .iid-pain-row { grid-template-columns: 1fr 1fr; } }
.iid-pain-tile {
  background: rgba(5,7,15,0.55);
  border: 1px solid var(--iid-line);
  border-radius: 16px;
  padding: 1.2rem 1.05rem;
}
.iid-pain-tile strong {
  display: block; font-family: var(--font-display);
  font-size: 1rem; font-weight: 650;
  color: var(--iid-text); line-height: 1.35;
}

.iid-grid-3, .iid-grid-4 { display: grid; gap: 1rem; }
.iid-grid-3 { grid-template-columns: repeat(3, 1fr); }
.iid-grid-4 { grid-template-columns: repeat(4, 1fr); }
@media (max-width: 900px) {
  .iid-grid-3, .iid-grid-4 { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 560px) {
  .iid-grid-3, .iid-grid-4 { grid-template-columns: 1fr; }
}
.iid-card {
  background: var(--iid-panel);
  border: 1px solid var(--iid-line);
  border-radius: 18px;
  padding: 1.55rem 1.35rem;
  height: 100%;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.iid-card:hover { border-color: rgba(11,95,255,0.55); transform: translateY(-2px); }
.iid-card-num {
  font-family: var(--font-display);
  font-size: 1.7rem; font-weight: 800; color: var(--iid-blue);
  margin: 0 0 0.85rem; letter-spacing: -0.04em; line-height: 1;
}
.iid-card .tag {
  display: block; font-size: 0.62rem; font-weight: 700;
  letter-spacing: 0.18em; color: var(--iid-muted); margin-bottom: 0.45rem;
}
.iid-card h3 {
  font-family: var(--font-display);
  margin: 0 0 0.5rem; font-size: 1.15rem; font-weight: 700;
  color: var(--iid-text); letter-spacing: -0.025em;
}
.iid-card p { margin: 0; color: var(--iid-muted); line-height: 1.6; font-size: 0.94rem; }

.iid-section-dark {
  background: var(--iid-panel);
  border: 1px solid var(--iid-line);
  border-radius: 24px;
  margin: 0 0 3.25rem;
  padding: 2.5rem 1.6rem;
}
.iid-services-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.9rem;
}
@media (max-width: 900px) { .iid-services-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 560px) { .iid-services-grid { grid-template-columns: 1fr; } }
.iid-service {
  background: var(--iid-ink);
  border: 1px solid var(--iid-line);
  border-radius: 16px;
  padding: 1.35rem 1.2rem;
  min-height: 148px;
}
.iid-service .tag {
  display: block; font-size: 0.58rem; font-weight: 700;
  letter-spacing: 0.18em; color: var(--iid-blue); margin-bottom: 0.5rem;
}
.iid-service h3 {
  font-family: var(--font-display);
  font-size: 1.1rem; font-weight: 700; margin: 0 0 0.45rem;
  color: var(--iid-text); letter-spacing: -0.02em;
}
.iid-service p { color: var(--iid-muted); font-size: 0.9rem; line-height: 1.55; margin: 0; }

.iid-process {
  display: grid; grid-template-columns: repeat(3, 1fr);
  border: 1px solid var(--iid-line);
  border-radius: 18px;
  overflow: hidden;
  background: var(--iid-panel);
}
@media (max-width: 700px) { .iid-process { grid-template-columns: 1fr; } }
.iid-process-step {
  padding: 1.7rem 1.4rem;
  border-right: 1px solid var(--iid-line);
}
.iid-process-step:last-child { border-right: none; }
@media (max-width: 700px) {
  .iid-process-step { border-right: none; border-bottom: 1px solid var(--iid-line); }
  .iid-process-step:last-child { border-bottom: none; }
}
.iid-step-big {
  font-family: var(--font-display);
  font-size: 2.6rem; font-weight: 800; line-height: 1;
  color: var(--iid-blue); margin: 0 0 0.55rem; letter-spacing: -0.04em;
}
.iid-process-step h4 {
  font-family: var(--font-display);
  font-size: 1.05rem; font-weight: 700; margin: 0 0 0.35rem; color: var(--iid-text);
}
.iid-process-step p { margin: 0; font-size: 0.9rem; color: var(--iid-muted); line-height: 1.5; }

.iid-how-row {
  display: grid; grid-template-columns: 40px 1fr; gap: 1rem;
  padding: 1rem 0; border-bottom: 1px solid var(--iid-line);
  align-items: center;
}
.iid-how-num {
  width: 40px; height: 40px; border-radius: 999px;
  background: var(--iid-blue); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display);
  font-weight: 800; font-size: 0.9rem;
}

.iid-buy-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;
}
@media (max-width: 700px) { .iid-buy-grid { grid-template-columns: 1fr; } }
.iid-buy-card {
  background: var(--iid-panel);
  border: 1px solid var(--iid-line);
  border-radius: 18px;
  padding: 1.7rem 1.5rem;
}
.iid-buy-card .mode {
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.18em;
  color: var(--iid-blue); margin-bottom: 0.55rem;
}
.iid-buy-card h3 {
  font-family: var(--font-display);
  margin: 0 0 0.55rem; color: var(--iid-text); font-size: 1.4rem; letter-spacing: -0.03em;
}
.iid-buy-card p { margin: 0; color: var(--iid-muted); font-size: 0.95rem; line-height: 1.6; }
.iid-buy-card ul { margin: 1rem 0 0; padding: 0; list-style: none; }
.iid-buy-card li {
  color: var(--iid-sky); font-size: 0.9rem; padding: 0.45rem 0;
  border-top: 1px solid var(--iid-line);
}

.iid-pill-row { display: flex; flex-wrap: wrap; gap: 0.45rem; margin: 1rem 0 1.4rem; }
.iid-pill {
  background: var(--iid-panel); color: var(--iid-sky);
  border: 1px solid var(--iid-line);
  border-radius: 999px;
  padding: 0.4rem 0.9rem;
  font-size: 0.74rem; font-weight: 600; letter-spacing: 0.03em;
}

.iid-detail-row {
  display: grid; grid-template-columns: 48px 1fr; gap: 1rem;
  padding: 1.15rem 0; border-bottom: 1px solid var(--iid-line);
}
.iid-detail-letter {
  width: 48px; height: 48px; border-radius: 14px;
  background: var(--iid-blue); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display);
  font-size: 1.1rem; font-weight: 800;
}

.iid-footer-dark {
  background: #03050c; color: var(--iid-muted);
  border-top: 1px solid var(--iid-line);
  padding: 2.75rem 1.25rem 1.6rem;
  margin: 2rem -1.25rem 0;
}
.iid-footer-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem; margin: 0 auto 1.5rem; max-width: var(--iid-max);
}
@media (max-width: 700px) { .iid-footer-grid { grid-template-columns: 1fr; } }
.iid-footer-dark h4 {
  font-family: var(--font-display);
  color: var(--iid-text); font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.16em; text-transform: uppercase; margin: 0 0 0.8rem;
}
.iid-footer-dark p { margin: 0; line-height: 1.85; font-size: 0.9rem; }
.iid-footer-dark a { color: var(--iid-sky); text-decoration: none; }
.iid-footer-dark a:hover { color: #fff; }
.iid-footer-copy {
  font-size: 0.76rem; color: #5b6780;
  border-top: 1px solid var(--iid-line); padding-top: 1.15rem;
  max-width: var(--iid-max); margin: 0 auto;
}

/* BUTTONS — solid rounded no shadow */
button,
div[data-testid="stHorizontalBlock"] button,
.stButton > button,
.stFormSubmitButton > button,
[data-testid="baseButton-primary"],
[data-testid="baseButton-secondary"] {
  border-radius: 999px !important;
  font-family: var(--font-body) !important;
  font-weight: 700 !important;
  font-size: 0.8rem !important;
  letter-spacing: 0.04em !important;
  box-shadow: none !important;
  text-shadow: none !important;
  filter: none !important;
  transform: none !important;
}
button[kind="primary"], [data-testid="baseButton-primary"] {
  background: var(--iid-blue) !important;
  color: #fff !important;
  border: 1.5px solid var(--iid-blue) !important;
}
button[kind="primary"]:hover { background: var(--iid-blue-dark) !important; border-color: var(--iid-blue-dark) !important; box-shadow: none !important; }
button[kind="secondary"], [data-testid="baseButton-secondary"] {
  background: var(--iid-panel-2) !important;
  color: #fff !important;
  border: 1.5px solid var(--iid-line) !important;
  box-shadow: none !important;
}
.iid-svc-actions { margin-top: 1rem; }

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
  background: var(--iid-panel) !important;
  color: var(--iid-text) !important;
  border: 1px solid var(--iid-line) !important;
  border-radius: 12px !important;
}

/* ===== VISUAL ENHANCEMENTS ===== */
.iid-trust-bar {
  display: flex; flex-wrap: wrap; align-items: center; gap: 1rem 1.5rem;
  padding: 1.1rem 1.4rem; margin: 0 0 2.5rem;
  background: rgba(16,24,40,0.6);
  border: 1px solid var(--iid-line);
  border-radius: 16px;
}
.iid-trust-bar > span {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--iid-muted); white-space: nowrap;
}
.iid-trust-logos { display: flex; flex-wrap: wrap; gap: 0.5rem 0.75rem; }
.iid-trust-chip {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.35rem 0.75rem; border-radius: 999px;
  background: var(--iid-panel); border: 1px solid var(--iid-line);
  font-size: 0.78rem; font-weight: 600; color: var(--iid-sky);
}
.iid-trust-chip svg { width: 14px; height: 14px; flex-shrink: 0; opacity: 0.85; }

.iid-hero-mockup {
  background: linear-gradient(145deg, #0d1528 0%, #101828 100%);
  border: 1px solid var(--iid-line);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 48px rgba(0,0,0,0.35);
}
.iid-mockup-chrome {
  display: flex; align-items: center; gap: 0.35rem;
  padding: 0.65rem 0.9rem;
  background: rgba(5,7,15,0.8);
  border-bottom: 1px solid var(--iid-line);
}
.iid-mockup-dot { width: 8px; height: 8px; border-radius: 50%; }
.iid-mockup-dot.r { background: #ff5f57; }
.iid-mockup-dot.y { background: #febc2e; }
.iid-mockup-dot.g { background: #28c840; }
.iid-mockup-body { padding: 1.1rem 1rem 1.25rem; }
.iid-mockup-row { display: flex; gap: 0.5rem; margin-bottom: 0.55rem; }
.iid-mockup-bar {
  height: 8px; border-radius: 4px;
  background: linear-gradient(90deg, var(--iid-blue), rgba(11,95,255,0.35));
}
.iid-mockup-bar.short { width: 38%; opacity: 0.5; background: var(--iid-line); }
.iid-mockup-bar.mid { width: 62%; }
.iid-mockup-bar.long { width: 88%; }
.iid-mockup-chart {
  display: flex; align-items: flex-end; gap: 0.35rem;
  height: 72px; margin: 0.85rem 0 0.65rem;
  padding: 0.5rem; background: rgba(5,7,15,0.45);
  border-radius: 10px; border: 1px solid var(--iid-line);
}
.iid-mockup-chart span {
  flex: 1; border-radius: 4px 4px 0 0;
  background: linear-gradient(180deg, var(--iid-blue), rgba(11,95,255,0.25));
}
.iid-mockup-tags { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.iid-mockup-tag {
  font-size: 0.62rem; font-weight: 700; letter-spacing: 0.08em;
  padding: 0.25rem 0.5rem; border-radius: 6px;
  background: rgba(11,95,255,0.15); color: var(--iid-sky);
  border: 1px solid rgba(11,95,255,0.25);
}

.iid-svg-icon {
  width: 36px; height: 36px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(11,95,255,0.12);
  border: 1px solid rgba(11,95,255,0.28);
  margin-bottom: 0.85rem;
}
.iid-svg-icon svg { width: 18px; height: 18px; stroke: var(--iid-blue); fill: none; }

.iid-pain-tile .icon {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(11,95,255,0.1);
  border: 1px solid rgba(11,95,255,0.22);
  margin-bottom: 0.7rem;
  font-size: 0 !important; letter-spacing: 0 !important;
}
.iid-pain-tile .icon svg { width: 20px; height: 20px; stroke: var(--iid-blue); fill: none; }

.iid-agent-head {
  display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.65rem;
}
.iid-agent-avatar {
  width: 42px; height: 42px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 0.72rem; font-weight: 800;
  color: #fff; flex-shrink: 0;
  border: 2px solid rgba(255,255,255,0.12);
}
.iid-agent-avatar.c1 { background: linear-gradient(135deg, #0b5fff, #0846b7); }
.iid-agent-avatar.c2 { background: linear-gradient(135deg, #7c3aed, #5b21b6); }
.iid-agent-avatar.c3 { background: linear-gradient(135deg, #059669, #047857); }
.iid-agent-avatar.c4 { background: linear-gradient(135deg, #ea580c, #c2410c); }
.iid-agent-avatar.c5 { background: linear-gradient(135deg, #db2777, #be185d); }
.iid-agent-avatar.c6 { background: linear-gradient(135deg, #0891b2, #0e7490); }

.iid-reviews-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
  margin-top: 0.5rem;
}
@media (max-width: 900px) { .iid-reviews-grid { grid-template-columns: 1fr; } }
.iid-review-card {
  background: var(--iid-panel);
  border: 1px solid var(--iid-line);
  border-radius: 18px;
  padding: 1.5rem 1.35rem;
  display: flex; flex-direction: column; gap: 0.85rem;
  height: 100%;
}
.iid-stars { color: #fbbf24; font-size: 0.9rem; letter-spacing: 0.12em; }
.iid-review-quote {
  margin: 0; font-size: 0.98rem; line-height: 1.65;
  color: var(--iid-text); flex: 1;
}
.iid-reviewer {
  display: flex; align-items: center; gap: 0.75rem;
  padding-top: 0.65rem; border-top: 1px solid var(--iid-line);
}
.iid-reviewer .av {
  width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 800; color: #fff;
  background: linear-gradient(135deg, var(--iid-blue), #5b8def);
  flex-shrink: 0;
}
.iid-reviewer strong { display: block; font-size: 0.88rem; color: var(--iid-text); }
.iid-reviewer span { font-size: 0.78rem; color: var(--iid-muted); }

.iid-metrics-strip {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.85rem;
  margin: 1.5rem 0 0;
}
@media (max-width: 800px) { .iid-metrics-strip { grid-template-columns: 1fr 1fr; } }
.iid-metric-tile {
  text-align: center; padding: 1.1rem 0.75rem;
  background: rgba(5,7,15,0.45);
  border: 1px solid var(--iid-line);
  border-radius: 14px;
}
.iid-metric-tile strong {
  display: block; font-family: var(--font-display);
  font-size: 1.6rem; font-weight: 800; color: var(--iid-blue);
  letter-spacing: -0.03em; line-height: 1;
}
.iid-metric-tile span { font-size: 0.78rem; color: var(--iid-muted); margin-top: 0.35rem; display: block; }

.iid-industry-grid {
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.65rem;
  margin: 1rem 0 1.4rem;
}
@media (max-width: 900px) { .iid-industry-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 500px) { .iid-industry-grid { grid-template-columns: repeat(2, 1fr); } }
.iid-industry-tile {
  display: flex; flex-direction: column; align-items: center; gap: 0.45rem;
  padding: 1rem 0.5rem;
  background: var(--iid-panel);
  border: 1px solid var(--iid-line);
  border-radius: 14px;
  text-align: center;
  transition: border-color 0.15s ease;
}
.iid-industry-tile:hover { border-color: rgba(11,95,255,0.45); }
.iid-industry-tile .ico {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(11,95,255,0.1);
}
.iid-industry-tile .ico svg { width: 18px; height: 18px; stroke: var(--iid-blue); fill: none; }
.iid-industry-tile span {
  font-size: 0.72rem; font-weight: 600; color: var(--iid-sky);
  letter-spacing: 0.02em;
}

.iid-process-step .step-icon {
  width: 48px; height: 48px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(11,95,255,0.12);
  border: 1px solid rgba(11,95,255,0.25);
  margin-bottom: 0.65rem;
}
.iid-process-step .step-icon svg { width: 22px; height: 22px; stroke: var(--iid-blue); fill: none; }

.iid-service .svc-icon {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(11,95,255,0.1);
  border: 1px solid rgba(11,95,255,0.22);
  margin-bottom: 0.65rem;
}
.iid-service .svc-icon svg { width: 20px; height: 20px; stroke: var(--iid-blue); fill: none; }

.iid-buy-card .buy-icon {
  width: 44px; height: 44px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(11,95,255,0.12);
  border: 1px solid rgba(11,95,255,0.28);
  margin-bottom: 0.85rem;
}
.iid-buy-card .buy-icon svg { width: 22px; height: 22px; stroke: var(--iid-blue); fill: none; }

.iid-samples-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
}
@media (max-width: 900px) { .iid-samples-grid { grid-template-columns: 1fr; } }
.iid-sample-card {
  background: var(--iid-panel);
  border: 1px solid var(--iid-line);
  border-radius: 18px;
  overflow: hidden;
  height: 100%;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.iid-sample-card:hover { border-color: rgba(11,95,255,0.5); transform: translateY(-2px); }
.iid-sample-preview {
  background: linear-gradient(160deg, #0c1424, #101828);
  border-bottom: 1px solid var(--iid-line);
  padding: 1rem 1rem 0.75rem;
  min-height: 148px;
}
.iid-sample-doc {
  background: #fff;
  border-radius: 8px 8px 0 0;
  padding: 0.65rem 0.75rem 0.85rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}
.iid-sample-doc .line {
  height: 5px; border-radius: 3px; margin-bottom: 0.35rem;
  background: #e8ecf4;
}
.iid-sample-doc .line.title { width: 55%; background: var(--iid-blue); height: 7px; margin-bottom: 0.55rem; }
.iid-sample-doc .line.w80 { width: 80%; }
.iid-sample-doc .line.w60 { width: 60%; }
.iid-sample-doc .line.w40 { width: 40%; }
.iid-sample-doc .mini-chart {
  display: flex; align-items: flex-end; gap: 3px;
  height: 36px; margin: 0.5rem 0 0.35rem;
}
.iid-sample-doc .mini-chart span {
  flex: 1; border-radius: 2px 2px 0 0;
  background: linear-gradient(180deg, var(--iid-blue), #a8c0ff);
}
.iid-sample-body { padding: 1.15rem 1.2rem 1.35rem; }
.iid-sample-body .tag {
  display: block; font-size: 0.58rem; font-weight: 700;
  letter-spacing: 0.18em; color: var(--iid-blue); margin-bottom: 0.4rem;
}
.iid-sample-body h3 {
  font-family: var(--font-display);
  font-size: 1.05rem; font-weight: 700; margin: 0 0 0.4rem;
  color: var(--iid-text); letter-spacing: -0.02em;
}
.iid-sample-body p { margin: 0; font-size: 0.88rem; color: var(--iid-muted); line-height: 1.55; }
.iid-sample-meta {
  display: flex; gap: 0.5rem; margin-top: 0.65rem; flex-wrap: wrap;
}
.iid-sample-meta span {
  font-size: 0.68rem; font-weight: 600; color: var(--iid-sky);
  background: rgba(11,95,255,0.1); border: 1px solid rgba(11,95,255,0.2);
  border-radius: 6px; padding: 0.2rem 0.45rem;
}

.iid-how-row .iid-how-icon {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(11,95,255,0.12);
  border: 1px solid rgba(11,95,255,0.25);
}
.iid-how-row .iid-how-icon svg { width: 18px; height: 18px; stroke: var(--iid-blue); fill: none; }

.iid-stat-row {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.85rem;
  margin: 1.75rem 0 0;
}
@media (max-width: 700px) { .iid-stat-row { grid-template-columns: 1fr; } }
.iid-stat-box {
  background: rgba(11,95,255,0.08);
  border: 1px solid rgba(11,95,255,0.22);
  border-radius: 14px;
  padding: 1.1rem 1rem;
  text-align: center;
}
.iid-stat-box strong {
  display: block; font-family: var(--font-display);
  font-size: 1.75rem; font-weight: 800; color: var(--iid-blue);
  letter-spacing: -0.03em; line-height: 1;
}
.iid-stat-box span { font-size: 0.78rem; color: var(--iid-muted); margin-top: 0.35rem; display: block; }

.iid-contact-grid {
  display: grid; grid-template-columns: 1fr 1.2fr; gap: 1.5rem;
  align-items: start; margin-bottom: 1.5rem;
}
@media (max-width: 800px) { .iid-contact-grid { grid-template-columns: 1fr; } }
.iid-contact-cards { display: flex; flex-direction: column; gap: 0.75rem; }
.iid-contact-card {
  display: flex; align-items: center; gap: 0.85rem;
  background: var(--iid-panel);
  border: 1px solid var(--iid-line);
  border-radius: 14px;
  padding: 1rem 1.1rem;
}
.iid-contact-card .ico {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(11,95,255,0.12);
  border: 1px solid rgba(11,95,255,0.25);
  flex-shrink: 0;
}
.iid-contact-card .ico svg { width: 18px; height: 18px; stroke: var(--iid-blue); fill: none; }
.iid-contact-card strong { display: block; font-size: 0.82rem; color: var(--iid-text); }
.iid-contact-card a, .iid-contact-card span {
  font-size: 0.88rem; color: var(--iid-sky); text-decoration: none;
}
.iid-contact-card a:hover { color: #fff; }

.iid-cta-banner {
  background:
    radial-gradient(ellipse 70% 80% at 100% 0%, rgba(11,95,255,0.28), transparent 55%),
    linear-gradient(160deg, #101828 0%, #0c1424 100%);
  border: 1px solid var(--iid-line);
  border-radius: 24px;
  padding: 2.25rem 2rem 0.5rem;
  margin: 0 0 2.5rem;
}
.iid-cta-banner-inner { max-width: 520px; }
</style>
"""
