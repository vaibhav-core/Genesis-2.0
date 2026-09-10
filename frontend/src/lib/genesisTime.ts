/**
 * genesisTime.ts
 *
 * Single source of truth for all event time operations.
 *
 * Two representations — never conflated:
 *   A. Display string  — pure string math on the IST wall-clock "HH:mm" value.
 *      No Date object, no timezone conversion.
 *   B. Absolute instant — a real Date, constructed with an explicit +05:30 offset
 *      so the moment is unambiguous regardless of the viewer's timezone.
 */

/**
 * Formats a "HH:mm" 24-hour IST string as a 12-hour display string.
 * e.g. "08:00" → "8:00 AM", "13:00" → "1:00 PM"
 *
 * Pure string/number math — NO Date object, NO timezone conversion.
 * The input is already the IST wall-clock time we want to show; converting
 * it through anything is how the display bug happens.
 */
export function formatISTDisplayTime(time: string): string {
  const [hourStr, minuteStr] = time.split(":");
  const hour24 = parseInt(hourStr, 10);
  const minute = (minuteStr ?? "00").padStart(2, "0");
  const period = hour24 >= 12 ? "PM" : "AM";
  const hour12 = hour24 % 12 === 0 ? 12 : hour24 % 12;
  return `${hour12}:${minute} ${period}`;
}

/**
 * Converts a "YYYY-MM-DD" IST date + "HH:mm" IST wall-clock time into the
 * correct absolute instant — a real Date representing that moment, regardless
 * of the browser's own timezone.
 *
 * Uses an explicit +05:30 offset. This is the only correct way to do this
 * conversion; never add/subtract 5.5 hours manually elsewhere.
 */
export function getISTInstant(date: string, time: string): Date {
  return new Date(`${date}T${time}:00+05:30`);
}

/**
 * Converts a UTC ISO string returned by the backend (e.g. "2026-09-12T02:30:00"
 * or "2026-09-12T02:30:00Z") into { date: "YYYY-MM-DD", time: "HH:mm" } in IST.
 *
 * The backend stores datetimes as UTC-naive (no timezone suffix). We treat them
 * as UTC by appending "Z" before parsing.
 */
export function utcIsoToIST(utcIso: string): { date: string; time: string } {
  // Ensure the string is parsed as UTC, not as local time
  const normalized = /[zZ]|[+-]\d{2}:?\d{2}$/.test(utcIso)
    ? utcIso
    : `${utcIso}Z`;
  const d = new Date(normalized);
  // Format in IST
  const datePart = d.toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" }); // "YYYY-MM-DD"
  const timePart = d.toLocaleTimeString("en-GB", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }); // "HH:mm"
  return { date: datePart, time: timePart };
}
