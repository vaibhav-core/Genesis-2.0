"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PageShell } from "@/components/genesis-ui";

const API_BASE = "/backend-api";
type VotingStatus = "not_started" | "open" | "closed";
type EventData = { id: number; name: string; description?: string | null; location?: string | null; voting_enabled: boolean; voting_status: VotingStatus };
type Candidate = { id: number; event_id: number; name: string; gender?: "male" | "female" | "other" | null; photo?: string | null; active: boolean };

type ApiFailure = { reason?: string; message?: string; detail?: string };

function silhouette(gender: Candidate["gender"]) {
  return gender === "male" ? "♂" : gender === "female" ? "♀" : "◇";
}

async function getJson<T>(path: string) {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Unable to load this competition.");
  return body as T;
}

export default function VotePage() {
  const params = useParams<{ eventId: string }>();
  const eventId = Number(params.eventId);
  const [event, setEvent] = useState<EventData | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<number | null>(null);
  const [mode, setMode] = useState<"registered" | "free">("registered");
  const [rollNumber, setRollNumber] = useState("");
  const [studentName, setStudentName] = useState("");
  const [voterIdentifier, setVoterIdentifier] = useState("");
  const [verified, setVerified] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [feedbackTone, setFeedbackTone] = useState<"error" | "success">("error");
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const loadCompetition = async () => {
    setLoading(true);
    setFeedback("");
    try {
      const [eventData, candidateData] = await Promise.all([
        getJson<EventData>(`/events/${eventId}`),
        getJson<Candidate[]>("/voting/candidates"),
      ]);
      setEvent(eventData);
      setCandidates(candidateData.filter((candidate) => candidate.event_id === eventId && candidate.active));
      setVerified(false);
    } catch (caught) {
      setFeedback(caught instanceof Error ? caught.message : "Unable to load this competition.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (Number.isFinite(eventId)) void loadCompetition();
    // The event ID identifies the page resource.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId]);

  const verify = async () => {
    setChecking(true); setFeedback("");
    const payload = mode === "registered"
      ? { mode, roll_number: rollNumber, name: studentName, event_id: eventId, candidate_id: selectedCandidate }
      : { mode, voter_identifier: voterIdentifier, event_id: eventId, candidate_id: selectedCandidate };
    try {
      const response = await fetch(`${API_BASE}/voting/verify`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const body = await response.json() as ApiFailure & { valid?: boolean };
      if (!response.ok || !body.valid) throw new Error(body.message ?? body.detail ?? "Verification failed.");
      setVerified(true); setFeedback("Identity checked. Submit your vote when ready."); setFeedbackTone("success");
    } catch (caught) { setVerified(false); setFeedback(caught instanceof Error ? caught.message : "Verification failed."); setFeedbackTone("error"); }
    finally { setChecking(false); }
  };

  const submit = async () => {
    setChecking(true); setFeedback("");
    const payload = mode === "registered"
      ? { mode, roll_number: rollNumber, name: studentName, event_id: eventId, candidate_id: selectedCandidate }
      : { mode, voter_identifier: voterIdentifier, event_id: eventId, candidate_id: selectedCandidate };
    try {
      const response = await fetch(`${API_BASE}/voting/vote`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const body = await response.json() as ApiFailure & { success?: boolean };
      if (!response.ok || !body.success) throw new Error(body.message ?? body.detail ?? "Vote submission failed.");
      setSubmitted(true); setFeedback("Your vote has been recorded."); setFeedbackTone("success");
    } catch (caught) { setFeedback(caught instanceof Error ? caught.message : "Vote submission failed."); setFeedbackTone("error"); }
    finally { setChecking(false); }
  };

  if (loading) return <PageShell><main className="vote-page"><p className="eyebrow">LOADING COMPETITION</p></main></PageShell>;
  if (!event) return <PageShell><main className="vote-page"><p className="admin-alert">{feedback || "Competition not found."}</p></main></PageShell>;

  const closedMessage = event.voting_status === "not_started" ? "Voting hasn't opened yet." : "Voting has closed for this competition.";
  return <PageShell><main className="vote-page"><header className="vote-heading"><span className="eyebrow">GENESIS VOTE · {event.location || "LIVE COMPETITION"}</span><h1>{event.name}</h1><p>{event.description || "Choose your competitor and cast one considered vote."}</p><button className="admin-ghost-button" onClick={() => void loadCompetition()} type="button">Re-check voting status</button></header>{!event.voting_enabled ? <section className="vote-state"><h2>Voting is not enabled.</h2><p>This event is not accepting votes.</p></section> : event.voting_status !== "open" ? <section className="vote-state"><h2>{closedMessage}</h2><p>The organiser controls when this competition accepts votes.</p></section> : <section className="vote-content"><div className="vote-section-heading"><span className="eyebrow">01 / CHOOSE</span><h2>Select a competitor</h2></div><div className="public-candidate-grid">{candidates.map((candidate) => <button className={selectedCandidate === candidate.id ? "public-candidate selected" : "public-candidate"} key={candidate.id} onClick={() => { setSelectedCandidate(candidate.id); setVerified(false); }} type="button"><div className="candidate-photo">{candidate.photo ? <img alt="" src={candidate.photo} /> : <span aria-label={`${candidate.gender ?? "generic"} silhouette`}>{silhouette(candidate.gender)}</span>}</div><strong>{candidate.name}</strong><small>{candidate.gender || "Competitor"}</small></button>)}</div>{candidates.length === 0 && <p className="admin-muted">No active competitors have been added yet.</p>}<div className="vote-section-heading"><span className="eyebrow">02 / IDENTIFY</span><h2>How are you voting?</h2></div><div className="vote-mode-tabs"><button className={mode === "registered" ? "selected" : ""} onClick={() => { setMode("registered"); setVerified(false); setFeedback(""); }} type="button">I'm a registered student</button><button className={mode === "free" ? "selected" : ""} onClick={() => { setMode("free"); setVerified(false); setFeedback(""); }} type="button">Vote without registration</button></div>{mode === "registered" ? <div className="vote-form"><label>Roll number<input value={rollNumber} onChange={(input) => { setRollNumber(input.target.value); setVerified(false); }} placeholder="24ME001" /></label><label>Name<input value={studentName} onChange={(input) => { setStudentName(input.target.value); setVerified(false); }} placeholder="Your full name" /></label></div> : <div className="vote-form"><label>Identifier <span>Use an ID you will remember to prevent duplicate votes.</span><input value={voterIdentifier} onChange={(input) => { setVoterIdentifier(input.target.value); setVerified(false); }} placeholder="24CS099 or any identifier" /></label></div>}{feedback && <p className={feedbackTone === "success" ? "vote-feedback success" : "vote-feedback"} role="status">{feedback}</p>}<div className="vote-actions"><button className="button" disabled={!selectedCandidate || checking || submitted} onClick={() => void verify()} type="button">{checking ? "Checking..." : "Verify details"}</button><button className="button button-light" disabled={!selectedCandidate || !verified || checking || submitted} onClick={() => void submit()} type="button">{submitted ? "Vote recorded" : "Submit vote"}</button></div></section>}<Link className="text-link" href="/events">← Back to events</Link></main></PageShell>;
}
