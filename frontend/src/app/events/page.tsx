"use client";

import { useEffect, useState } from "react";
import { EventCard, GenesisCountdown, PageShell, SectionHeading, WinnerCard } from "@/components/genesis-ui";
import type { GenesisEvent } from "@/config/genesis";
import { utcIsoToIST } from "@/lib/genesisTime";

type BackendEvent = {
	id: number;
	name: string;
	description?: string | null;
	start_time?: string | null;
	end_time?: string | null;
	location?: string | null;
	voting_enabled: boolean;
	voting_status: "not_started" | "open" | "closed";
	winner?: string | null;
	winner_photo?: string | null;
	is_competitive: boolean;
};

const API_BASE = "/backend-api";

function dayFromDescription(description: string | null | undefined) {
	return description?.toLowerCase().startsWith("sunday") ? "day2" : "day1";
}

function toGenesisEvent(event: BackendEvent, index: number): GenesisEvent {
	const defaultDate = dayFromDescription(event.description) === "day2" ? "2026-09-13" : "2026-09-12";
	const startIST = event.start_time ? utcIsoToIST(event.start_time) : null;
	const endIST = event.end_time ? utcIsoToIST(event.end_time) : null;
	const date = startIST?.date ?? defaultDate;
	const description = [event.description, event.location].filter(Boolean).join(" · ") || "A Genesis 2.0 programme event.";
	return {
		id: String(event.id),
		title: event.name,
		description,
		date,
		startTime: startIST?.time,
		endTime: endIST?.time,
		category: event.is_competitive ? "Competition" : "Programme",
		visual: String(index + 1).padStart(2, "0"),
		route: event.is_competitive && event.voting_enabled ? `/events/${event.id}/vote` : undefined,
		winner: event.winner,
		votingStatus: event.voting_status,
		isCompetitive: event.is_competitive,
		winnerPhoto: event.winner_photo,
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
			.then(async (data) => {
				const mapped = data.map(toGenesisEvent);
				const leaders = await Promise.all(data.map(async (event) => {
					if (!event.voting_enabled || event.voting_status !== "open") return null;
					const result = await fetch(`${API_BASE}/voting/results?event_id=${event.id}`, { cache: "no-store" });
					if (!result.ok) return null;
					const body = await result.json() as { results?: { name: string; votes: number }[] };
					return body.results?.[0]?.votes ? body.results[0].name : null;
				}));
				setEvents(mapped.map((event, index) => ({ ...event, winner: leaders[index] ?? event.winner })));
			})
			.catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "The event schedule is unavailable right now."))
			.finally(() => setLoading(false));
	}, []);

	const day1 = events.filter((event) => event.date === "2026-09-12");
	const day2 = events.filter((event) => event.date === "2026-09-13");
	const other = events.filter((event) => !day1.includes(event) && !day2.includes(event));

	const renderEvent = (event: GenesisEvent) => <div key={event.id}><EventCard event={event} /><WinnerCard event={event} /></div>;
	return <PageShell><main className="page-main"><section className="page-heading"><span className="eyebrow">THE PROGRAMME</span><h1>Make a date<br /><em>with Genesis.</em></h1><GenesisCountdown /></section><section className="section schedule">{loading && <p className="admin-muted">Loading the live schedule...</p>}{error && <p className="admin-alert" role="alert">{error}</p>}{!loading && !error && <><SectionHeading kicker="DAY 01 / 12 SEPTEMBER" title="Arrive curious." /><div className="event-grid">{day1.map(renderEvent)}</div><SectionHeading kicker="DAY 02 / 13 SEPTEMBER" title="Leave changed." /><div className="event-grid">{day2.map(renderEvent)}</div>{other.length > 0 && <><SectionHeading kicker="THE FULL PROGRAMME" title="More to discover." /><div className="event-grid">{other.map(renderEvent)}</div></>}</>}</section></main></PageShell>;
}