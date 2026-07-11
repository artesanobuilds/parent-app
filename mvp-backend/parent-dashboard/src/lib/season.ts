// Discovery season, derived from the calendar instead of a hardcoded string
// (the old `season: 'summer 2026'` went stale the day summer ended).
//
// Camp-planning reality: parents plan the NEXT big break. Through July the
// target is this summer; Aug–Oct it's fall break/programs; from November the
// target rolls to next summer (registration season starts in winter).
export function currentSeason(now: Date = new Date()): string {
  const month = now.getMonth() + 1; // 1-12
  const year = now.getFullYear();
  if (month <= 7) return `summer ${year}`;
  if (month <= 10) return `fall ${year}`;
  return `summer ${year + 1}`;
}
