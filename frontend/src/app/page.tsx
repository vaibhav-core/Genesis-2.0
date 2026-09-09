"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { GENESIS_START, SITE_INFO, type GenesisEvent } from "@/config/genesis";
import { Countdown, EventCard, PageShell, SectionHeading } from "@/components/genesis-ui";

type BackendEvent = { id: number; name: string; description?: string | null; start_time?: string | null; end_time?: string | null; location?: string | null; voting_enabled: boolean };

function toPreviewEvent(event: BackendEvent, index: number): GenesisEvent {
  const date = event.start_time?.slice(0, 10) ?? (event.description?.toLowerCase().startsWith("sunday") ? "2026-09-13" : "2026-09-12");
  return { id: String(event.id), title: event.name, description: [event.description, event.location].filter(Boolean).join(" · ") || "A Genesis 2.0 programme event.", date, startTime: event.start_time ?? undefined, endTime: event.end_time ?? undefined, category: event.voting_enabled ? "Competition" : "Programme", visual: String(index + 1).padStart(2, "0"), route: event.voting_enabled ? `/events/${event.id}/vote` : undefined };
}

export default function Home() {
  const [events, setEvents] = useState<GenesisEvent[]>([]);
  useEffect(() => { fetch("/backend-api/events", { cache: "no-store" }).then((response) => response.json() as Promise<BackendEvent[]>).then((data) => setEvents(data.map(toPreviewEvent))).catch(() => undefined); }, []);
  const day1 = events.filter((event) => event.date === "2026-09-12").slice(0, 4);
  const day2 = events.filter((event) => event.date === "2026-09-13").slice(0, 4);
  return <PageShell><main><section className="hero"><div className="hero-grid"><span className="eyebrow">IIT DHARWAD · PRESENTS</span><h1>GENESIS <em>2.0</em></h1><div className="hero-details"><p>Freshers 2026</p><p>{SITE_INFO.dates}</p></div><div className="hero-count"><span className="eyebrow">THE GATES OPEN IN</span><Countdown target={GENESIS_START} /></div></div><div className="hero-mark">G<br />2</div></section><section className="intro section"><SectionHeading kicker="01 / THE BEGINNING" title="Every story has a first night." copy="Genesis is the first page of your IIT Dharwad story. Two days of music, movement, and the people who will make this campus feel like home." /><Link className="button" href="/about">Discover Genesis <span>↗</span></Link></section><section className="section"><SectionHeading kicker="02 / ON THE HORIZON" title="Two days. One beginning." /><div className="day-label">DAY 01 — 12 SEPTEMBER</div><div className="event-grid preview-grid">{day1.map(event => <EventCard event={event} key={event.id} />)}</div><div className="day-label">DAY 02 — 13 SEPTEMBER</div><div className="event-grid preview-grid">{day2.map(event => <EventCard event={event} key={event.id} />)}</div><Link className="text-link centered" href="/events">View full schedule <span>↗</span></Link></section><section className="pass-preview section"><div><span className="eyebrow">03 / YOUR ENTRY</span><h2>Carry the beginning<br /><em>with you.</em></h2><p>Passes unlock when Genesis begins.</p></div><Countdown target={GENESIS_START} compact /><Link className="button button-light" href="/passes">Pass access <span>↗</span></Link></section><section className="about-preview section"><SectionHeading kicker="04 / THE PEOPLE BEHIND IT" title="Built by students, for students." copy="Genesis is a welcome from the Student Council and the teams that make IIT Dharwad move." /><Link className="text-link" href="/about">Meet the team <span>↗</span></Link></section></main></PageShell>;
}
