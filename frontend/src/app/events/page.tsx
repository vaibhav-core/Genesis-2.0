"use client";

import { useEffect, useState } from "react";
import { EventCard, GenesisCountdown, PageShell, SectionHeading } from "@/components/genesis-ui";
import type { GenesisEvent } from "@/config/genesis";

type BackendEvent = {
	id: number;
	name: string;
	description?: string | null;
	start_time?: string | null;
	end_time?: string | null;
	location?: string | null;
	voting_enabled: boolean;
	voting_status: "not_started" | "open" | "closed";
};

const API_BASE = "/backend-api";

function dayFromDescription(description: string | null | undefined) {
	return description?.toLowerCase().startsWith("sunday") ? "day2" : "day1";
}

function toGenesisEvent(event: BackendEvent, index: number): GenesisEvent {
	const date = dayFromDescription(event.description) === "day2" ? "2026-09-13" : "2026-09-12";
	const description = [event.description, event.location].filter(Boolean).join(" · ") || "A Genesis 2.0 programme event.";
	return {
		id: String(event.id),
		title: event.name,
		description,
		date,
		startTime: event.start_time ?? undefined,
		endTime: event.end_time ?? undefined,
		category: event.voting_enabled ? "Competition" : "Programme",
		visual: String(index + 1).padStart(2, "0"),
		route: event.voting_enabled ? `/events/${event.id}/vote` : undefined,
	};
}

export default function EventsPage() {
	const [events, setEvents] = useState<GenesisEvent[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState("");

	useEffect(() => {
		fetch(`${API_BASE}/events`, { cache: "no-store" })
			.then(async (response) => {
				if (!response.ok) throw new Error("The event schedule is unavailable right now.");
				return response.json() as Promise<BackendEvent[]>;
			})
			.then((data) => setEvents(data.map(toGenesisEvent)))
			.catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "The event schedule is unavailable right now."))
			.finally(() => setLoading(false));
	}, []);

	const day1 = events.filter((event) => event.date === "2026-09-12");
	const day2 = events.filter((event) => event.date === "2026-09-13");
	const other = events.filter((event) => !day1.includes(event) && !day2.includes(event));

	return <PageShell><main className="page-main"><section className="page-heading"><span className="eyebrow">THE PROGRAMME</span><h1>Make a date<br /><em>with Genesis.</em></h1><GenesisCountdown /></section><section className="section schedule">{loading && <p className="admin-muted">Loading the live schedule...</p>}{error && <p className="admin-alert" role="alert">{error}</p>}{!loading && !error && <><SectionHeading kicker="DAY 01 / 12 SEPTEMBER" title="Arrive curious." /><div className="event-grid">{day1.map((event) => <EventCard key={event.id} event={event} />)}</div><SectionHeading kicker="DAY 02 / 13 SEPTEMBER" title="Leave changed." /><div className="event-grid">{day2.map((event) => <EventCard key={event.id} event={event} />)}</div>{other.length > 0 && <><SectionHeading kicker="THE FULL PROGRAMME" title="More to discover." /><div className="event-grid">{other.map((event) => <EventCard key={event.id} event={event} />)}</div></>}</>}</section></main></PageShell>;
}