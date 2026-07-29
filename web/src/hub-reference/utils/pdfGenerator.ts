// @ts-nocheck
/**
 * PDF Generator Utility
 *
 * Opens browser print dialog for all report types:
 * - Research Reports
 * - Action Plans (Plan It Out)
 * - Solutions
 * - Business Plans
 *
 * Programmatically unlocks all overflow / height constraints before printing
 * so that the FULL document is rendered across multiple pages — not just
 * the visible viewport.
 */

/** Snapshot of an element's inline style properties we may need to restore */
interface StyleSnapshot {
  el: HTMLElement;
  overflow: string;
  overflowX: string;
  overflowY: string;
  height: string;
  maxHeight: string;
  minHeight: string;
  position: string;
  display: string;
  visibility: string;
  opacity: string;
}

/** Take a snapshot and then unlock an element's constraints */
function unlockElement(el: HTMLElement, snapshots: StyleSnapshot[]): void {
  snapshots.push({
    el,
    overflow: el.style.overflow,
    overflowX: el.style.overflowX,
    overflowY: el.style.overflowY,
    height: el.style.height,
    maxHeight: el.style.maxHeight,
    minHeight: el.style.minHeight,
    position: el.style.position,
    display: el.style.display,
    visibility: el.style.visibility,
    opacity: el.style.opacity,
  });

  el.style.overflow = 'visible';
  el.style.overflowX = 'visible';
  el.style.overflowY = 'visible';
  el.style.maxHeight = 'none';
  el.style.height = 'auto';
  // Don't touch minHeight – it rarely causes clipping
}

/** Restore all element snapshots */
function restoreSnapshots(snapshots: StyleSnapshot[]): void {
  for (const s of snapshots) {
    s.el.style.overflow = s.overflow;
    s.el.style.overflowX = s.overflowX;
    s.el.style.overflowY = s.overflowY;
    s.el.style.height = s.height;
    s.el.style.maxHeight = s.maxHeight;
    s.el.style.minHeight = s.minHeight;
    s.el.style.position = s.position;
    s.el.style.display = s.display;
    s.el.style.visibility = s.visibility;
    s.el.style.opacity = s.opacity;
  }
}

/**
 * Core print routine.
 *
 * Steps:
 *  1. Switch to light mode.
 *  2. Unlock html / body overflow so the browser can paginate everything.
 *  3. Unlock every element whose *computed* overflow clips content, or whose
 *     Tailwind class name suggests a constrained height / overflow.
 *  4. Make hidden tab panels and inactive Radix UI content visible
 *     (removes the HTML `hidden` attribute + forces display:block).
 *  5. Call window.print().
 *  6. Restore all mutations after the print dialog closes.
 */
async function openPrintDialog(): Promise<void> {
  const html = document.documentElement;
  const body = document.body;
  const wasDarkMode = html.classList.contains('dark');

  // ── 1. Light mode ───────────────────────────────────────────────────────────
  if (wasDarkMode) {
    html.classList.remove('dark');
  }

  // ── 2. Unlock html / body ───────────────────────────────────────────────────
  const rootSnapshots: StyleSnapshot[] = [];
  unlockElement(html, rootSnapshots);
  unlockElement(body, rootSnapshots);

  // Additional root overrides that inline styles can't express via unlockElement
  const htmlPrev = { maxWidth: html.style.maxWidth, width: html.style.width };
  const bodyPrev = { maxWidth: body.style.maxWidth, width: body.style.width };
  html.style.maxWidth = 'none';
  html.style.width = '100%';
  body.style.maxWidth = 'none';
  body.style.width = '100%';

  // ── 3. Unlock every potentially clipping element ────────────────────────────
  const snapshots: StyleSnapshot[] = [];

  // Select by Tailwind class name patterns that might constrain height
  const clampSelectors = [
    '[class*="overflow-hidden"]',
    '[class*="overflow-y-"]',
    '[class*="overflow-x-"]',
    '[class*="overflow-auto"]',
    '[class*="overflow-scroll"]',
    '[class*="h-screen"]',
    '[class*="h-[calc"]',
    '[class*="max-h-"]',
    '[class*="min-h-screen"]',
  ].join(',');

  document.querySelectorAll<HTMLElement>(clampSelectors).forEach(el => {
    unlockElement(el, snapshots);
  });

  // Also catch anything whose *computed* overflow actually hides content
  document.querySelectorAll<HTMLElement>('*').forEach(el => {
    const cs = window.getComputedStyle(el);
    if (cs.overflow === 'hidden' || cs.overflowY === 'hidden' || cs.overflowX === 'hidden') {
      if (!snapshots.find(s => s.el === el) && el !== html && el !== body) {
        unlockElement(el, snapshots);
      }
    }
  });

  // ── 4. Make all tab panels / hidden sections visible ────────────────────────
  const hiddenPanelInfo: Array<{ el: HTMLElement; hadHidden: boolean; prevDisplay: string; prevVisibility: string; prevOpacity: string; prevPosition: string; prevHeight: string }> = [];

  // Radix UI / shadcn tabs set [hidden] attribute on inactive panels
  document.querySelectorAll<HTMLElement>('[role="tabpanel"], [data-state="inactive"], [data-slot="tabs-content"]').forEach(el => {
    const hadHidden = el.hasAttribute('hidden');
    hiddenPanelInfo.push({
      el,
      hadHidden,
      prevDisplay: el.style.display,
      prevVisibility: el.style.visibility,
      prevOpacity: el.style.opacity,
      prevPosition: el.style.position,
      prevHeight: el.style.height,
    });
    el.removeAttribute('hidden');
    el.style.display = 'block';
    el.style.visibility = 'visible';
    el.style.opacity = '1';
    el.style.position = 'static';
    el.style.height = 'auto';
  });

  // Hide tab triggers (navigation tabs are useless on paper)
  const tabLists = document.querySelectorAll<HTMLElement>('[role="tablist"], [data-slot="tabs-list"]');
  const tabListPrevDisplay: string[] = [];
  tabLists.forEach(el => {
    tabListPrevDisplay.push(el.style.display);
    el.style.display = 'none';
  });

  // ── 5. Wait for layout to settle, then print ────────────────────────────────
  await new Promise<void>(resolve => setTimeout(resolve, 400));

  window.print();

  // ── 6. Restore everything ~1 s after print dialog opens ────────────────────
  setTimeout(() => {
    if (wasDarkMode) {
      html.classList.add('dark');
    }

    // Restore root snapshots
    restoreSnapshots(rootSnapshots);
    html.style.maxWidth = htmlPrev.maxWidth;
    html.style.width = htmlPrev.width;
    body.style.maxWidth = bodyPrev.maxWidth;
    body.style.width = bodyPrev.width;

    // Restore all element snapshots
    restoreSnapshots(snapshots);

    // Restore tab panels
    hiddenPanelInfo.forEach(({ el, hadHidden, prevDisplay, prevVisibility, prevOpacity, prevPosition, prevHeight }) => {
      if (hadHidden) el.setAttribute('hidden', '');
      el.style.display = prevDisplay;
      el.style.visibility = prevVisibility;
      el.style.opacity = prevOpacity;
      el.style.position = prevPosition;
      el.style.height = prevHeight;
    });

    // Restore tab lists
    tabLists.forEach((el, i) => {
      el.style.display = tabListPrevDisplay[i];
    });
  }, 1200);
}

// ── Public API ────────────────────────────────────────────────────────────────

/** Generate PDF for Business Report */
export async function downloadBusinessReport(reportTitle: string, topic: string): Promise<void> {
  await openPrintDialog();
}

/** Generate PDF for Action Plan */
export async function downloadActionPlan(topic: string, location: string): Promise<void> {
  await openPrintDialog();
}

/** Generate PDF for Solutions */
export async function downloadSolutions(problem: string, location: string): Promise<void> {
  await openPrintDialog();
}

/** Generate PDF for Business Plan */
export async function downloadBusinessPlan(businessIdea: string): Promise<void> {
  await openPrintDialog();
}
