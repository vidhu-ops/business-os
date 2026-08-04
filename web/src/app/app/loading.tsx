export default function AppLoading() {
  return (
    <main className="flex min-h-[40vh] flex-col items-center justify-center gap-3 px-6 text-center">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--iid-line)] border-t-[var(--iid-blue)]" />
      <p className="text-sm text-[var(--iid-muted)]">Loading workspace…</p>
      <p className="text-xs text-[var(--iid-muted)] max-w-sm">
        On Render free tier, the server may take up to a minute to wake after idle sleep.
      </p>
    </main>
  );
}
