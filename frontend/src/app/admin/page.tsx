"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import {
  ADMIN_API_BASE,
  type AdminEvent,
  type Candidate,
  type Participant,
  type ResultRow,
  type VoteRecord,
} from "@/config/admin-api";

const TOKEN_KEY = "genesis_admin_token";
const subscribe = () => () => undefined;
const getClientAuth = () => Boolean(sessionStorage.getItem(TOKEN_KEY));
const getServerAuth = () => false;

type MemberDraft = { name: string; roll_number: string };

function apiError(detail: unknown) {
  return typeof detail === "string" ? detail : JSON.stringify(detail);
}

export default function AdminPage() {
  const router = useRouter();
  const authorized = useSyncExternalStore(subscribe, getClientAuth, getServerAuth);
  const [events, setEvents] = useState<AdminEvent[]>([]);
  const [votes, setVotes] = useState<VoteRecord[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const signOut = () => {
    sessionStorage.removeItem(TOKEN_KEY);
    router.replace("/");
  };

  const request = async <T,>(path: string, init: RequestInit = {}) => {
    const response = await fetch(`${ADMIN_API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sessionStorage.getItem(TOKEN_KEY) ?? ""}`,
        ...init.headers,
      },
    });
    if (response.status === 401) {
      signOut();
      throw new Error("SESSION_EXPIRED");
    }
    const body = response.status === 204 ? null : await response.json();
    if (!response.ok) throw new Error(apiError(body?.detail ?? body));
    return body as T;
  };

  const loadParticipants = async (eventId: number) => {
    setSelectedEventId(eventId);
    try {
      setParticipants(await request<Participant[]>(`/admin/events/${eventId}/participants`));
    } catch (caught) {
      if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setError(caught.message);
    }
  };

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [eventData, voteData] = await Promise.all([
        request<AdminEvent[]>("/events"),
        request<VoteRecord[]>("/admin/votes"),
      ]);
      setEvents(eventData);
      setVotes(voteData);
      if (eventData[0]) await loadParticipants(eventData[0].id);
    } catch (caught) {
      if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setError(caught.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authorized) {
      router.replace("/");
      return;
    }
    void loadDashboard();
    // Dashboard requests intentionally run when auth becomes available.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authorized, router]);

  if (!authorized) return <main className="admin-loading">Checking access...</main>;
  if (loading) return <main className="admin-loading">Loading dashboard...</main>;

  const selectedEvent = events.find((event) => event.id === selectedEventId) ?? null;
  const refreshEvent = async () => {
    const refreshed = await request<AdminEvent[]>("/events");
    setEvents(refreshed);
    if (selectedEventId) await loadParticipants(selectedEventId);
  };

  return (
    <main className="admin-page">
      <header className="admin-header">
        <div><span className="eyebrow">GENESIS 2.0 · PRIVATE</span><h1>Admin dashboard</h1></div>
        <button className="admin-ghost-button" onClick={signOut} type="button">Sign out</button>
      </header>
      {error && <div className="admin-alert" role="alert">{error}</div>}
      <section className="admin-layout">
        <div className="admin-main-column">
          <section className="admin-panel">
            <div className="admin-panel-heading">
              <div><span className="eyebrow">OVERVIEW</span><h2>Event schedule</h2></div>
              <span className="admin-count">{events.length} events</span>
            </div>
            <div className="results-list">
              {events.map((event) => (
                <button className={selectedEventId === event.id ? "result-row active" : "result-row"} key={event.id} onClick={() => void loadParticipants(event.id)} type="button">
                  <span><b>{event.name}</b><small>{event.location || "Location not set"} · {event.competition_format || "general schedule"}</small></span>
                  <span className="winner-result"><b>{event.voting_enabled ? "Voting enabled" : "No voting"}</b><small>{event.voting_status}</small></span>
                  <span>→</span>
                </button>
              ))}
            </div>
          </section>
          {selectedEvent && <EventManagement event={selectedEvent} participants={participants} onRefresh={refreshEvent} request={request} />}
        </div>
        <VotesTable votes={votes} />
      </section>
    </main>
  );
}

function EventManagement({
  event,
  participants,
  onRefresh,
  request,
}: {
  event: AdminEvent;
  participants: Participant[];
  onRefresh: () => Promise<void>;
  request: <T>(path: string, init?: RequestInit) => Promise<T>;
}) {
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState(event.name);
  const [description, setDescription] = useState(event.description ?? "");
  const [location, setLocation] = useState(event.location ?? "");
  const [startTime, setStartTime] = useState(event.start_time?.slice(0, 16) ?? "");
  const [endTime, setEndTime] = useState(event.end_time?.slice(0, 16) ?? "");
  const [format, setFormat] = useState<"" | "individual" | "team">(event.competition_format ?? "");
  const [votingEnabled, setVotingEnabled] = useState(event.voting_enabled);
  const [type, setType] = useState<"individual" | "team">("individual");
  const [participantName, setParticipantName] = useState("");
  const [rollNumber, setRollNumber] = useState("");
  const [members, setMembers] = useState<MemberDraft[]>([{ name: "", roll_number: "" }]);
  const [winnerParticipantId, setWinnerParticipantId] = useState("");
  const [manualWinner, setManualWinner] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [results, setResults] = useState<ResultRow[]>([]);
  const [candidateName, setCandidateName] = useState("");
  const [candidateGender, setCandidateGender] = useState("");
  const [candidatePhoto, setCandidatePhoto] = useState("");

  const publicRequest = async <T,>(path: string) => {
    const response = await fetch(`${ADMIN_API_BASE}${path}`);
    const body = await response.json();
    if (!response.ok) throw new Error(apiError(body?.detail ?? body));
    return body as T;
  };

  const loadVotingData = async () => {
    if (!event.voting_enabled) return;
    try {
      const [candidateData, resultData] = await Promise.all([
        publicRequest<Candidate[]>("/voting/candidates"),
        event.voting_status === "not_started" ? Promise.resolve({ results: [] } as { results: ResultRow[] }) : publicRequest<{ results: ResultRow[] }>(`/voting/results?event_id=${event.id}`),
      ]);
      setCandidates(candidateData.filter((candidate) => candidate.event_id === event.id));
      setResults(resultData.results);
    } catch (caught) {
      if (caught instanceof Error) setFormError(caught.message);
    }
  };

  useEffect(() => {
    setName(event.name); setDescription(event.description ?? ""); setLocation(event.location ?? "");
    setStartTime(event.start_time?.slice(0, 16) ?? ""); setEndTime(event.end_time?.slice(0, 16) ?? "");
    setFormat(event.competition_format ?? ""); setVotingEnabled(event.voting_enabled);
    void loadVotingData();
    // Event identity/status changes are the intended refresh trigger.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [event.id, event.voting_enabled, event.voting_status]);

  const saveEvent = async (formEvent: React.FormEvent) => {
    formEvent.preventDefault(); setSaving(true); setFormError("");
    try {
      await request(`/admin/events/${event.id}`, { method: "PATCH", body: JSON.stringify({ name, description: description || null, location: location || null, start_time: startTime ? new Date(startTime).toISOString() : null, end_time: endTime ? new Date(endTime).toISOString() : null, competition_format: format || null, voting_enabled: votingEnabled }) });
      await onRefresh();
    } catch (caught) { if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setFormError(caught.message); }
    finally { setSaving(false); }
  };

  const changeVoting = async (action: "start" | "stop") => {
    setFormError("");
    try { await request(`/admin/events/${event.id}/voting/${action}`, { method: "POST" }); await onRefresh(); }
    catch (caught) { if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setFormError(caught.message); }
  };

  const addParticipant = async (formEvent: React.FormEvent) => {
    formEvent.preventDefault(); setFormError("");
    const payload = type === "individual" ? { participant_type: type, name: participantName, roll_number: rollNumber || null } : { participant_type: type, name: participantName, members: members.filter((member) => member.name.trim()) };
    try { await request(`/admin/events/${event.id}/participants`, { method: "POST", body: JSON.stringify(payload) }); setParticipantName(""); setRollNumber(""); setMembers([{ name: "", roll_number: "" }]); await onRefresh(); }
    catch (caught) { if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setFormError(caught.message); }
  };

  const addCandidate = async (formEvent: React.FormEvent) => {
    formEvent.preventDefault(); setFormError("");
    try { await request("/admin/candidates", { method: "POST", body: JSON.stringify({ event_id: event.id, name: candidateName, gender: candidateGender === "prefer" ? null : candidateGender || null, photo: candidatePhoto || null }) }); setCandidateName(""); setCandidateGender(""); setCandidatePhoto(""); await loadVotingData(); }
    catch (caught) { if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setFormError(caught.message); }
  };

  const deactivateCandidate = async (candidate: Candidate) => {
    try { await request(`/admin/candidates/${candidate.id}`, { method: "PATCH", body: JSON.stringify({ active: false }) }); await loadVotingData(); }
    catch (caught) { if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setFormError(caught.message); }
  };

  const setWinner = async (formEvent: React.FormEvent) => {
    formEvent.preventDefault(); setFormError("");
    const payload = winnerParticipantId ? { winner_participant_id: Number(winnerParticipantId) } : { winner: manualWinner };
    try { await request(`/admin/events/${event.id}/winner`, { method: "POST", body: JSON.stringify(payload) }); setWinnerParticipantId(""); setManualWinner(""); await onRefresh(); }
    catch (caught) { if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setFormError(caught.message); }
  };

  return (
    <section className="admin-panel event-management">
      <div className="admin-panel-heading"><div><span className="eyebrow">EVENT MANAGEMENT</span><h2>{event.name}</h2></div><span className="admin-count">{participants.length} registered</span></div>
      {formError && <div className="admin-alert" role="alert">{formError}</div>}
      <form className="admin-form event-edit-form" onSubmit={saveEvent}>
        <h3>Edit event</h3>
        <label>Name<input value={name} onChange={(input) => setName(input.target.value)} required /></label>
        <label>Description<textarea value={description} onChange={(input) => setDescription(input.target.value)} /></label>
        <label>Location<input value={location} onChange={(input) => setLocation(input.target.value)} /></label>
        <div className="admin-form-grid"><label>Start<input type="datetime-local" value={startTime} onChange={(input) => setStartTime(input.target.value)} /></label><label>End<input type="datetime-local" value={endTime} onChange={(input) => setEndTime(input.target.value)} /></label></div>
        <label>Competition format<select value={format} onChange={(input) => setFormat(input.target.value as "" | "individual" | "team")}><option value="">None</option><option value="individual">Individual</option><option value="team">Team</option></select></label>
        <label className="checkbox-label"><input type="checkbox" checked={votingEnabled} onChange={(input) => setVotingEnabled(input.target.checked)} /> Voting enabled</label>
        <button className="admin-primary-button" disabled={saving} type="submit">{saving ? "Saving..." : "Save event"}</button>
      </form>
      {event.voting_enabled && <section className="voting-admin-section"><div className="admin-subheading"><h3>Voting controls</h3><span className={`voting-status status-${event.voting_status}`}>{event.voting_status}</span></div><div className="control-row"><button className="admin-primary-button" disabled={event.voting_status === "open"} onClick={() => void changeVoting("start")} type="button">Start voting</button><button className="admin-ghost-button" disabled={event.voting_status !== "open"} onClick={() => void changeVoting("stop")} type="button">Stop voting</button></div></section>}
      <section className="participant-list"><h3>Participants</h3>{participants.length === 0 && <p className="admin-muted">No participants registered yet.</p>}{participants.map((participant) => <div className="participant-row" key={participant.id}><div><strong>{participant.name}</strong><span className="type-pill">{participant.participant_type}</span>{participant.roll_number && <small>{participant.roll_number}</small>}{participant.members.length > 0 && <div className="member-list">{participant.members.map((member) => <span key={member.id}>{member.name}{member.roll_number ? ` · ${member.roll_number}` : ""}</span>)}</div>}</div><div className="participant-actions"><button className="mini-button" onClick={() => { setWinnerParticipantId(String(participant.id)); setManualWinner(""); }} type="button">Set winner</button><button className="delete-button" onClick={() => { void request(`/admin/events/${event.id}/participants/${participant.id}`, { method: "DELETE" }).then(onRefresh); }} type="button">Remove</button></div></div>)}</section>
      <div className="admin-forms"><form className="admin-form" onSubmit={addParticipant}><h3>Add participant</h3><div className="segmented"><button className={type === "individual" ? "selected" : ""} onClick={() => setType("individual")} type="button">Individual</button><button className={type === "team" ? "selected" : ""} onClick={() => setType("team")} type="button">Team</button></div><label>Name or team name<input value={participantName} onChange={(input) => setParticipantName(input.target.value)} required /></label>{type === "individual" ? <label>Roll number <span>(optional)</span><input value={rollNumber} onChange={(input) => setRollNumber(input.target.value)} /></label> : <div className="member-drafts"><span className="form-label">Team members</span>{members.map((member, index) => <div className="member-draft" key={index}><input aria-label="Member name" placeholder="Name" value={member.name} onChange={(input) => setMembers(members.map((item, itemIndex) => itemIndex === index ? { ...item, name: input.target.value } : item))} /><input aria-label="Member roll number" placeholder="Roll number" value={member.roll_number} onChange={(input) => setMembers(members.map((item, itemIndex) => itemIndex === index ? { ...item, roll_number: input.target.value } : item))} /><button className="delete-button" onClick={() => setMembers(members.filter((_, itemIndex) => itemIndex !== index))} type="button">×</button></div>)}<button className="add-member" onClick={() => setMembers([...members, { name: "", roll_number: "" }])} type="button">Add member</button></div>}<button className="admin-primary-button" type="submit">Register participant</button></form>
        <form className="admin-form" onSubmit={setWinner}><h3>Winner</h3><label>Participant<select value={winnerParticipantId} onChange={(input) => { setWinnerParticipantId(input.target.value); setManualWinner(""); }}><option value="">Choose a participant</option>{participants.map((participant) => <option key={participant.id} value={participant.id}>{participant.name}</option>)}</select></label><span className="or-divider">or enter a name</span><input value={manualWinner} onChange={(input) => { setManualWinner(input.target.value); setWinnerParticipantId(""); }} placeholder="Manual winner name" /><button className="admin-primary-button" disabled={!winnerParticipantId && !manualWinner.trim()} type="submit">Save winner</button></form>
      </div>
      {event.voting_enabled && <section className="candidate-admin-section"><div className="admin-subheading"><h3>Competitors</h3><button className="admin-ghost-button" onClick={() => void loadVotingData()} type="button">Refresh results</button></div><div className="candidate-admin-list">{candidates.map((candidate) => <div className="candidate-admin-row" key={candidate.id}><div><strong>{candidate.name}</strong><small>{candidate.gender || "No gender set"} · {candidate.photo ? "Photo provided" : "No photo"}</small></div><button className="delete-button" onClick={() => void deactivateCandidate(candidate)} type="button">Deactivate</button></div>)}</div><form className="admin-form" onSubmit={addCandidate}><h3>Add competitor</h3><label>Name<input value={candidateName} onChange={(input) => setCandidateName(input.target.value)} required /></label><label>Gender<select value={candidateGender} onChange={(input) => setCandidateGender(input.target.value)}><option value="">Select</option><option value="male">Male</option><option value="female">Female</option><option value="other">Other</option><option value="prefer">Prefer not to say</option></select></label><label>Photo URL <span>(optional)</span><input value={candidatePhoto} onChange={(input) => setCandidatePhoto(input.target.value)} /></label><button className="admin-primary-button" type="submit">Add competitor</button></form>{event.voting_status !== "not_started" && <div className="admin-results"><h3>Live results</h3>{results.length === 0 ? <p className="admin-muted">No votes recorded.</p> : results.map((result) => <div className="result-bar" key={result.candidate_id}><span>{result.name}</span><b>{result.votes}</b></div>)}</div>}</section>}
    </section>
  );
}

function VotesTable({ votes }: { votes: VoteRecord[] }) {
  return <section className="admin-panel votes-panel"><div className="admin-panel-heading"><div><span className="eyebrow">VOTING LOG</span><h2>Votes</h2></div><span className="admin-count">{votes.length} votes</span></div><div className="votes-table-wrap"><table><thead><tr><th>Voter</th><th>Roll number</th><th>Candidate</th><th>Event</th><th>Timestamp</th></tr></thead><tbody>{votes.length === 0 ? <tr><td colSpan={5} className="admin-muted">No votes recorded.</td></tr> : votes.map((vote, index) => <tr key={`${vote.voter_roll_number}-${vote.created_at}-${index}`}><td>{vote.voter_name}</td><td>{vote.voter_roll_number}</td><td>{vote.candidate_name}</td><td>{vote.event_id}</td><td>{new Date(vote.created_at).toLocaleString()}</td></tr>)}</tbody></table></div></section>;
}
