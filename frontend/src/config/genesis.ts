import { formatISTDisplayTime, getISTInstant } from "@/lib/genesisTime";

export const GENESIS_START = getISTInstant("2026-09-12", "08:00");
export const PASS_UNLOCK_DATE = getISTInstant("2026-09-12", "08:00");
export const COUNTDOWN_WINDOW_HOURS = 24;

export interface GenesisEvent {
  id: string;
  title: string;
  description: string;
  /** IST calendar date, "YYYY-MM-DD" */
  date: string;
  /** IST wall-clock start time, "HH:mm" */
  startTime?: string;
  /** IST wall-clock end time, "HH:mm" */
  endTime?: string;
  category: string;
  visual: string;
  route?: string;
  winner?: string | null;
  votingStatus?: "not_started" | "open" | "closed";
  isCompetitive?: boolean;
  winnerPhoto?: string | null;
}

export const EVENTS: { day1: GenesisEvent[]; day2: GenesisEvent[] } = {
  day1: [
    { id: "opening", title: "Opening Ceremony", description: "A bright beginning to two days of new names and shared stories.", date: "2026-09-12", startTime: "18:00", endTime: "19:00", category: "Ceremony", visual: "01" },
    { id: "freshie-mixer", title: "Freshie Mixer", description: "Music, games, and the first collision of campus energy.", date: "2026-09-12", startTime: "19:30", endTime: "21:00", category: "Social", visual: "02" },
  ],
  day2: [
    { id: "talent-night", title: "Talent Night", description: "The stage belongs to every voice, rhythm, and unexpected trick.", date: "2026-09-13", startTime: "18:00", endTime: "20:00", category: "Performance", visual: "03" },
    { id: "mister-miss", title: "Mister & Miss Freshie", description: "A celebration of confidence, character, and campus charm.", date: "2026-09-13", startTime: "20:30", endTime: "22:00", category: "Spotlight", visual: "04", route: "/events/mister-miss-freshie" },
  ],
};

export interface VotingCategory { id: string; name: string; description?: string }
export const VOTING_CATEGORIES: VotingCategory[] = [
  { id: "dressed", name: "Best Dressed", description: "Own the room with your signature look." },
  { id: "crowd", name: "Crowd Favourite", description: "The energy that brings everyone together." },
  { id: "intro", name: "Best Introduction", description: "Make your first impression unforgettable." },
  { id: "talent", name: "Best Talent", description: "A moment only you could create." },
];

export const SITE_INFO = { eventName: "Genesis 2.0", college: "IIT Dharwad", dates: "12–13 September 2026" };

/**
 * Formats a "HH:mm" IST wall-clock time for display.
 * Delegates to formatISTDisplayTime — no Date object, no timezone conversion.
 */
export function formatEventTime(time?: string | null): string {
  if (!time) return "";
  return formatISTDisplayTime(time);
}

/**
 * Converts an admin datetime-local string ("YYYY-MM-DDThh:mm") to a UTC ISO
 * string to store in the backend. The datetime-local value is interpreted as IST.
 */
export function toEventIsoWithTimezone(dateTimeLocal: string | null | undefined): string | null {
  if (!dateTimeLocal) return null;
  const match = dateTimeLocal.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})$/);
  if (!match) return dateTimeLocal;
  const [, date, time] = match;
  return getISTInstant(date, time).toISOString();
}

export function isGenesisEventName(name?: string | null): boolean {
  if (!name) return false;
  return name.toLowerCase().includes("genesis");
}

export type EventStatus = "ENDED" | "LIVE" | "COUNTDOWN" | "UPCOMING";

/**
 * Determines the live status of an event.
 * startTime and endTime are "HH:mm" IST wall-clock strings; date is "YYYY-MM-DD".
 */
export function getEventStatus(startTime: string, endTime: string, date: string, now = new Date()): EventStatus {
  const start = getISTInstant(date, startTime).getTime();
  const end = getISTInstant(date, endTime).getTime();
  const current = now.getTime();
  if (current > end) return "ENDED";
  if (current >= start && current <= end) return "LIVE";
  if (start - current <= COUNTDOWN_WINDOW_HOURS * 60 * 60 * 1000) return "COUNTDOWN";
  return "UPCOMING";
}