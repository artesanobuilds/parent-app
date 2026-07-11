import { getVerticals } from '../api';
import type { VerticalDoor } from '../types';

// Vertical doors with a LAST-GOOD cache (the plan's rule: clients cache and
// never block board render on /cos/verticals — a flag-eval outage or a slow
// network must not blank the "Plan something" affordance).

const CACHE_KEY = 'vertical-doors-v1';

export function cachedDoors(): VerticalDoor[] {
  try {
    return JSON.parse(localStorage.getItem(CACHE_KEY) ?? '[]') as VerticalDoor[];
  } catch {
    return [];
  }
}

export async function fetchDoors(): Promise<VerticalDoor[]> {
  try {
    const { verticals } = await getVerticals();
    localStorage.setItem(CACHE_KEY, JSON.stringify(verticals));
    return verticals;
  } catch {
    return cachedDoors();
  }
}
