import { MARKETING_PHOTOS, type MarketingPhotoId } from "./marketingImages";

type Props = { className?: string };

export function GlowOrb({ className = "" }: Props) {
  return (
    <div className={`mkt-glow-orb ${className}`} aria-hidden="true">
      <span className="mkt-glow-orb-a" />
      <span className="mkt-glow-orb-b" />
    </div>
  );
}

export function HeroVisual() {
  return (
    <div className="mkt-hero-visual" aria-hidden="true">
      <div className="mkt-hero-device">
        <div className="mkt-hero-device-top">
          <span className="dot r" /><span className="dot y" /><span className="dot g" />
          <span className="mkt-device-title">Founder workspace</span>
        </div>
        <div className="mkt-hero-device-body">
          <div className="mkt-device-sidebar">
            {["Dashboard", "Research", "Plan", "Team"].map((l) => (
              <span key={l} className="mkt-device-nav">{l}</span>
            ))}
          </div>
          <div className="mkt-device-main">
            <div className="mkt-device-kpis">
              <div><strong>40+</strong><span>Report pages</span></div>
              <div><strong>18</strong><span>Topics</span></div>
              <div><strong>6</strong><span>AI agents</span></div>
            </div>
            <div className="mkt-device-chart">
              {[38, 62, 48, 78, 55, 88, 64].map((h, i) => (
                <span key={i} style={{ height: `${h}%` }} />
              ))}
            </div>
            <div className="mkt-device-rows">
              <span /><span /><span />
            </div>
          </div>
        </div>
      </div>
      <div className="mkt-float-card mkt-float-card-a">
        <span className="mkt-float-label">TAM / SAM</span>
        <strong>₹2,400 Cr</strong>
      </div>
      <div className="mkt-float-card mkt-float-card-b">
        <span className="mkt-float-label">Sources</span>
        <strong>24 verified</strong>
      </div>
    </div>
  );
}

export function DocPreview({ variant = "report" }: { variant?: "report" | "plan" | "exec" }) {
  const accent = variant === "exec" ? "#34d399" : variant === "plan" ? "#a78bfa" : "#60a5fa";
  return (
    <div className="mkt-doc-preview" style={{ ["--doc-accent" as string]: accent }}>
      <div className="mkt-doc-line title" />
      <div className="mkt-doc-line w90" />
      <div className="mkt-doc-line w70" />
      <div className="mkt-doc-chart">
        {[45, 72, 58, 85, 50].map((h, i) => (
          <span key={i} style={{ height: `${h}%` }} />
        ))}
      </div>
      <div className="mkt-doc-line w80 accent" />
      <div className="mkt-doc-line w60 accent" />
    </div>
  );
}

export function AgentBadge({ initials, tone }: { initials: string; tone: string }) {
  return <div className={`mkt-agent-badge tone-${tone}`}>{initials}</div>;
}

const HUMAN_IMAGES: Record<"founder" | "team" | "mobile", MarketingPhotoId> = {
  founder: "founder-team",
  team: "strategy-meeting",
  mobile: "mobile-founder",
};

export function MarketingPhoto({
  id,
  className = "",
  rounded = "xl",
}: {
  id: MarketingPhotoId;
  className?: string;
  rounded?: "lg" | "xl" | "2xl";
}) {
  const photo = MARKETING_PHOTOS[id];
  return (
    <figure className={`mkt-photo mkt-photo-${rounded} ${className}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={photo.src} alt={photo.alt} className="mkt-photo-img" loading="lazy" />
      {photo.caption ? <figcaption className="mkt-photo-caption">{photo.caption}</figcaption> : null}
    </figure>
  );
}

export function PhotoCollage({ ids }: { ids: MarketingPhotoId[] }) {
  return (
    <div className="mkt-photo-collage" aria-hidden={false}>
      {ids.map((id, i) => (
        <MarketingPhoto key={id} id={id} className={i === 0 ? "mkt-photo-collage-main" : ""} />
      ))}
    </div>
  );
}

export function PhotoStrip({ ids }: { ids: MarketingPhotoId[] }) {
  return (
    <div className="mkt-photo-strip">
      {ids.map((id) => (
        <MarketingPhoto key={id} id={id} rounded="lg" />
      ))}
    </div>
  );
}

export function HumanScene({
  variant = "founder",
  photoId,
  cardA,
  cardB,
}: {
  variant?: "founder" | "team" | "mobile";
  photoId?: MarketingPhotoId;
  cardA?: { label: string; value: string };
  cardB?: { label: string; value: string };
}) {
  const id = photoId || HUMAN_IMAGES[variant];
  const photo = MARKETING_PHOTOS[id];
  const a = cardA || { label: "Live research", value: "18 topics sourced" };
  const b = cardB || { label: "Team ready", value: "6 AI employees" };
  return (
    <div className="mkt-human-scene">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={photo.src} alt={photo.alt} className="mkt-human-photo" loading="lazy" />
      <div className="mkt-human-card mkt-human-card-a">
        <span>{a.label}</span>
        <strong>{a.value}</strong>
      </div>
      <div className="mkt-human-card mkt-human-card-b">
        <span>{b.label}</span>
        <strong>{b.value}</strong>
      </div>
    </div>
  );
}

type StepVariant = "signup" | "research" | "plan" | "reference" | "team" | "ship";

const STEP_COLORS: Record<StepVariant, string> = {
  signup: "#60a5fa",
  research: "#34d399",
  plan: "#a78bfa",
  reference: "#f472b6",
  team: "#fbbf24",
  ship: "#0b5fff",
};

export function StepIllustration({ variant }: { variant: StepVariant }) {
  return (
    <div className="mkt-step-illus" style={{ ["--step-accent" as string]: STEP_COLORS[variant] }}>
      <div className="mkt-step-illus-icon" />
      <div className="mkt-step-illus-bars">
        <span /><span /><span />
      </div>
      <div className="mkt-step-illus-chart">
        {[40, 65, 50, 80, 55].map((h, i) => (
          <span key={i} style={{ height: `${h}%` }} />
        ))}
      </div>
    </div>
  );
}

export function VideoShowcase({
  title,
  subtitle,
  videoId,
}: {
  title: string;
  subtitle: string;
  videoId: string;
}) {
  return (
    <div className="mkt-video-block">
      <div className="mkt-video-copy">
        <h2 className="mkt-h2">{title}</h2>
        <p className="mkt-sub">{subtitle}</p>
      </div>
      <div className="mkt-video-frame">
        <iframe
          title={title}
          src={`https://www.youtube.com/embed/${videoId}?rel=0`}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
    </div>
  );
}

export function ProductVideo({
  poster,
  src,
}: {
  poster: string;
  src: string;
}) {
  return (
    <div className="mkt-inline-video">
      <video poster={poster} controls playsInline preload="metadata" className="mkt-inline-video-el">
        <source src={src} type="video/mp4" />
      </video>
    </div>
  );
}
