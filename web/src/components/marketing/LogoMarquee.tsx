export type LogoMarqueeItem = {
  name: string;
  src: string;
};

type Props = {
  items: readonly LogoMarqueeItem[];
  ariaLabel: string;
  className?: string;
  itemClassName?: string;
};

/** One-line auto-scrolling logo row (same pattern as industries). */
export function LogoMarquee({ items, ariaLabel, className = "", itemClassName = "" }: Props) {
  const loop = [...items, ...items];
  return (
    <div className={`mkt-logo-marquee ${className}`.trim()} aria-label={ariaLabel}>
      <div className="mkt-logo-marquee-track">
        {loop.map((logo, i) => (
          <div
            key={`${logo.name}-${i}`}
            className={`mkt-logo-marquee-item ${itemClassName}`.trim()}
            aria-hidden={i >= items.length ? true : undefined}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={logo.src} alt={i < items.length ? `${logo.name} logo` : ""} loading="lazy" />
            {i < items.length ? <span className="sr-only">{logo.name}</span> : null}
          </div>
        ))}
      </div>
    </div>
  );
}
