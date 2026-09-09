export const GENESIS_START = "2026-09-12T18:00:00+05:30";
export const PASS_UNLOCK_DATE = "2026-09-12T18:00:00+05:30";
export const COUNTDOWN_WINDOW_HOURS = 24;

export interface GenesisEvent {
  id: string;
  title: string;
  description: string;
  date: string;
  startTime: string;
  endTime: string;
  category: string;
  visual: string;
  route?: string;
}

export const EVENTS: { day1: GenesisEvent[]; day2: GenesisEvent[] } = {
  day1: [
    { id: "opening", title: "Opening Ceremony", description: "A bright beginning to two days of new names and shared stories.", date: "2026-09-12", startTime: "2026-09-12T18:00:00+05:30", endTime: "2026-09-12T19:00:00+05:30", category: "Ceremony", visual: "01" },
    { id: "freshie-mixer", title: "Freshie Mixer", description: "Music, games, and the first collision of campus energy.", date: "2026-09-12", startTime: "2026-09-12T19:30:00+05:30", endTime: "2026-09-12T21:00:00+05:30", category: "Social", visual: "02" },
  ],
  day2: [
    { id: "talent-night", title: "Talent Night", description: "The stage belongs to every voice, rhythm, and unexpected trick.", date: "2026-09-13", startTime: "2026-09-13T18:00:00+05:30", endTime: "2026-09-13T20:00:00+05:30", category: "Performance", visual: "03" },
    { id: "mister-miss", title: "Mister & Miss Freshie", description: "A celebration of confidence, character, and campus charm.", date: "2026-09-13", startTime: "2026-09-13T20:30:00+05:30", endTime: "2026-09-13T22:00:00+05:30", category: "Spotlight", visual: "04", route: "/events/mister-miss-freshie" },
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
export type EventStatus = "ENDED" | "LIVE" | "COUNTDOWN" | "UPCOMING";
export function getEventStatus(startTime: string, endTime: string, now = new Date()): EventStatus {
  const start = new Date(startTime).getTime();
  const end = new Date(endTime).getTime();
  const current = now.getTime();
  if (current > end) return "ENDED";
  if (current >= start && current <= end) return "LIVE";
  if (start - current <= COUNTDOWN_WINDOW_HOURS * 60 * 60 * 1000) return "COUNTDOWN";
  return "UPCOMING";
}