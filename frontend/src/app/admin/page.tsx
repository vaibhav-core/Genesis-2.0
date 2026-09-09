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
  const [showCreateEvent, setShowCreateEvent] = useState(false);
  const [showWipeVotes, setShowWipeVotes] = useState(false);
  const [wipeConfirmation, setWipeConfirmation] = useState("");

  const signOut = () => {
    sessionStorage.removeItem(TOKEN_KEY);
    router.replace("/");
  };

  const request = async <T,>(path: string, init: RequestInit = {}) => {
    const isMultipart = init.body instanceof FormData;
    const response = await fetch(`${ADMIN_API_BASE}${path}`, {
      ...init,
      headers: {
        ...(isMultipart ? {} : { "Content-Type": "application/json" }),
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

  const createEvent = async (formEvent: React.FormEvent<HTMLFormElement>) => {
    formEvent.preventDefault();
    const form = new FormData(formEvent.currentTarget);
    try {
      await request("/admin/events", { method: "POST", body: JSON.stringify({
        name: String(form.get("name")),
        description: String(form.get("description") || "") || null,
        location: String(form.get("location") || "") || null,
        start_time: form.get("start_time") ? new Date(String(form.get("start_time"))).toISOString() : null,
        end_time: form.get("end_time") ? new Date(String(form.get("end_time"))).toISOString() : null,
        competition_format: form.get("competition_format") || null,
        voting_enabled: form.get("voting_enabled") === "on",
      }) });
      setShowCreateEvent(false);
      await loadDashboard();
    } catch (caught) {
      if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setError(caught.message);
    }
  };

  const wipeVotes = async () => {
    if (wipeConfirmation !== "DELETE") return;
    try {
      await request("/admin/votes", { method: "DELETE" });
      setShowWipeVotes(false);
      setWipeConfirmation("");
      await loadDashboard();
    } catch (caught) {
      if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setError(caught.message);
    }
  };

  return (
    <main className="admin-page">
      <header className="admin-header">
        <div><span className="eyebrow">GENESIS 2.0 · PRIVATE</span><h1>Admin dashboard</h1></div>
        <button className="admin-ghost-button" onClick={signOut} type="button">Sign out</button>
      </header>
      {error && <div className="admin-alert" role="alert">{error}</div>}
      <div className="admin-danger-zone"><button className="danger-button" onClick={() => setShowWipeVotes(true)} type="button">Wipe all votes</button></div>
      {showWipeVotes && <div className="admin-modal-backdrop" role="presentation"><dialog className="admin-login danger-modal" open><span className="eyebrow">IRREVERSIBLE ACTION</span><h2>Wipe all votes?</h2><p>This deletes registered and free-mode votes across every event and clears winner fields. Type DELETE to confirm.</p><input value={wipeConfirmation} onChange={(input) => setWipeConfirmation(input.target.value)} placeholder="DELETE" /><div className="control-row"><button className="admin-ghost-button" onClick={() => { setShowWipeVotes(false); setWipeConfirmation(""); }} type="button">Cancel</button><button className="danger-button" disabled={wipeConfirmation !== "DELETE"} onClick={() => void wipeVotes()} type="button">Delete votes</button></div></dialog></div>}
      <section className="admin-layout">
        <div className="admin-main-column">
          <section className="admin-panel">
            <div className="admin-panel-heading">
              <div><span className="eyebrow">OVERVIEW</span><h2>Event schedule</h2></div>
              <span className="admin-count">{events.length} events</span>
            </div>
            <button className="admin-primary-button" onClick={() => setShowCreateEvent(!showCreateEvent)} type="button">{showCreateEvent ? "Close form" : "Add event"}</button>
            {showCreateEvent && <form className="admin-form create-event-form" onSubmit={createEvent}><h3>New event</h3><label>Name<input name="name" required /></label><label>Description<textarea name="description" /></label><label>Location<input name="location" /></label><div className="admin-form-grid"><label>Start<input name="start_time" type="datetime-local" /></label><label>End<input name="end_time" type="datetime-local" /></label></div><label>Format<select name="competition_format"><option value="">None</option><option value="individual">Individual</option><option value="team">Team</option></select></label><label className="checkbox-label"><input name="voting_enabled" type="checkbox" /> Voting enabled</label><button className="admin-primary-button" type="submit">Create event</button></form>}
            <div className="results-list">
              {events.map((event) => (
                <button className={selectedEventId === event.id ? "result-row active" : "result-row"} key={event.id} onClick={() => void loadParticipants(event.id)} type="button">
                  <span><b>{event.name}</b><small>{event.location || "Location not set"} · {event.competition_format || "general schedule"}</small></span>
                  <span className="winner-result"><b>{event.winner ? (event.voting_status === "open" ? `Leading: ${event.winner}` : `Winner: ${event.winner}`) : event.voting_enabled ? "No leader yet" : "No winner set"}</b><small>{event.voting_enabled ? event.voting_status : "No voting"}</small></span>
                  <span>→</span>
                </button>
              ))}
            </div>
          </section>
          {selectedEvent && <EventManagement event={selectedEvent} participants={participants} onRefresh={refreshEvent} request={request} onDelete={async () => { if (!window.confirm(`Remove ${selectedEvent.name}?`)) return; await request(`/admin/events/${selectedEvent.id}`, { method: "DELETE" }); setSelectedEventId(null); await loadDashboard(); }} />}
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
  onDelete,
}: {
  event: AdminEvent;
  participants: Participant[];
  onRefresh: () => Promise<void>;
  request: <T>(path: string, init?: RequestInit) => Promise<T>;
  onDelete: () => Promise<void>;
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
  const [participantPhoto, setParticipantPhoto] = useState<File | null>(null);
  const [winnerParticipantId, setWinnerParticipantId] = useState("");
  const [manualWinner, setManualWinner] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [results, setResults] = useState<ResultRow[]>([]);
  const [candidateName, setCandidateName] = useState("");
  const [candidateGender, setCandidateGender] = useState("");
  const [candidatePhoto, setCandidatePhoto] = useState("");
  const [passOverride, setPassOverride] = useState(event.pass_distribution_enabled_override);
  const [winnerPhoto, setWinnerPhoto] = useState<File | null>(null);

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
    setFormat(event.competition_format ?? ""); setVotingEnabled(event.voting_enabled); setPassOverride(event.pass_distribution_enabled_override);
    void loadVotingData();
    // Event identity/status changes are the intended refresh trigger.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [event.id, event.voting_enabled, event.voting_status]);

  const saveEvent = async (formEvent: React.FormEvent) => {
    formEvent.preventDefault(); setSaving(true); setFormError("");
    try {
      await request(`/admin/events/${event.id}`, { method: "PATCH", body: JSON.stringify({ name, description: description || null, location: location || null, start_time: startTime ? new Date(startTime).toISOString() : null, end_time: endTime ? new Date(endTime).toISOString() : null, competition_format: format || null, voting_enabled: votingEnabled, is_competitive: Boolean(format || votingEnabled), pass_distribution_enabled_override: passOverride }) });
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
    try { const created = await request<Participant>(`/admin/events/${event.id}/participants`, { method: "POST", body: JSON.stringify(payload) }); if (participantPhoto) { const photoBody = new FormData(); photoBody.append("photo", participantPhoto); await request(`/admin/events/${event.id}/participants/${created.id}/photo`, { method: "POST", body: photoBody }); } setParticipantName(""); setRollNumber(""); setParticipantPhoto(null); setMembers([{ name: "", roll_number: "" }]); await onRefresh(); }
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
  const uploadWinnerPhoto = async () => {
    if (!winnerPhoto) return;
    const body = new FormData(); body.append("photo", winnerPhoto);
    try { await request(`/admin/events/${event.id}/winner/photo`, { method: "POST", headers: { Authorization: `Bearer ${sessionStorage.getItem(TOKEN_KEY) ?? ""}` }, body }); setWinnerPhoto(null); await onRefresh(); }
    catch (caught) { if (caught instanceof Error && caught.message !== "SESSION_EXPIRED") setFormError(caught.message); }
  };
  const competitive = event.is_competitive || event.voting_enabled || Boolean(event.competition_format);

  return (
    <section className="admin-panel event-management">
      <div className="admin-panel-heading"><div><span className="eyebrow">EVENT MANAGEMENT</span><h2>{event.name}</h2></div><div className="event-heading-actions"><span className="admin-count">{participants.length} registered</span><button className="delete-button" onClick={() => void onDelete()} type="button">Remove event</button></div></div>
      {formError && <div className="admin-alert" role="alert">{formError}</div>}
      <form className="admin-form event-edit-form" onSubmit={saveEvent}>
        <h3>Edit event</h3>
        <label>Name<input value={name} onChange={(input) => setName(input.target.value)} required /></label>
        <label>Description<textarea value={description} onChange={(input) => setDescription(input.target.value)} /></label>
        <label>Location<input value={location} onChange={(input) => setLocation(input.target.value)} /></label>
        <div className="admin-form-grid"><label>Start<input type="datetime-local" value={startTime} onChange={(input) => setStartTime(input.target.value)} /></label><label>End<input type="datetime-local" value={endTime} onChange={(input) => setEndTime(input.target.value)} /></label></div>
        <label>Competition format<select value={format} onChange={(input) => setFormat(input.target.value as "" | "individual" | "team")}><option value="">None</option><option value="individual">Individual</option><option value="team">Team</option></select></label>
        <label className="checkbox-label"><input type="checkbox" checked={votingEnabled} onChange={(input) => setVotingEnabled(input.target.checked)} /> Voting enabled</label>
        <label className="checkbox-label"><input type="checkbox" checked={passOverride} onChange={(input) => setPassOverride(input.target.checked)} /> Enable pass distribution early</label>
        <button className="admin-primary-button" disabled={saving} type="submit">{saving ? "Saving..." : "Save event"}</button>
      </form>
      <section className="pass-template-stub"><h3>Pass template</h3><p>Template upload coming soon.</p></section>
      {competitive && event.voting_enabled && <section className="voting-admin-section"><div className="admin-subheading"><h3>Voting controls</h3><span className={`voting-status status-${event.voting_status}`}>{event.voting_status}</span></div><div className="control-row"><button className="admin-primary-button" disabled={event.voting_status === "open"} onClick={() => void changeVoting("start")} type="button">Start voting</button><button className="admin-ghost-button" disabled={event.voting_status !== "open"} onClick={() => void changeVoting("stop")} type="button">Stop voting</button></div></section>}
      <section className="participant-list"><h3>Participants</h3>{participants.length === 0 && <p className="admin-muted">No participants registered yet.</p>}{participants.map((participant) => <div className="participant-row" key={participant.id}><div><strong>{participant.name}</strong><span className="type-pill">{participant.participant_type}</span>{participant.roll_number && <small>{participant.roll_number}</small>}{participant.members.length > 0 && <div className="member-list">{participant.members.map((member) => <span key={member.id}>{member.name}{member.roll_number ? ` · ${member.roll_number}` : ""}</span>)}</div>}</div><div className="participant-actions"><button className="mini-button" onClick={() => { setWinnerParticipantId(String(participant.id)); setManualWinner(""); }} type="button">Set winner</button><button className="delete-button" onClick={() => { void request(`/admin/events/${event.id}/participants/${participant.id}`, { method: "DELETE" }).then(onRefresh); }} type="button">Remove</button></div></div>)}</section>
      <div className="admin-forms"><form className="admin-form" onSubmit={addParticipant}><h3>Add participant</h3><div className="segmented"><button className={type === "individual" ? "selected" : ""} onClick={() => setType("individual")} type="button">Individual</button><button className={type === "team" ? "selected" : ""} onClick={() => setType("team")} type="button">Team</button></div><label>Name or team name<input value={participantName} onChange={(input) => setParticipantName(input.target.value)} required /></label>{type === "individual" ? <label>Roll number <span>(optional)</span><input value={rollNumber} onChange={(input) => setRollNumber(input.target.value)} /></label> : <div className="member-drafts"><span className="form-label">Team members</span>{members.map((member, index) => <div className="member-draft" key={index}><input aria-label="Member name" placeholder="Name" value={member.name} onChange={(input) => setMembers(members.map((item, itemIndex) => itemIndex === index ? { ...item, name: input.target.value } : item))} /><input aria-label="Member roll number" placeholder="Roll number" value={member.roll_number} onChange={(input) => setMembers(members.map((item, itemIndex) => itemIndex === index ? { ...item, roll_number: input.target.value } : item))} /><button className="delete-button" onClick={() => setMembers(members.filter((_, itemIndex) => itemIndex !== index))} type="button">×</button></div>)}<button className="add-member" onClick={() => setMembers([...members, { name: "", roll_number: "" }])} type="button">Add member</button></div>}<label>Photo <span>(optional device image)</span><input accept="image/*" onChange={(input) => setParticipantPhoto(input.target.files?.[0] ?? null)} type="file" /></label><button className="admin-primary-button" type="submit">Register participant</button></form>
        {competitive && <form className="admin-form" onSubmit={setWinner}><h3>Winner</h3><label>Participant<select value={winnerParticipantId} onChange={(input) => { setWinnerParticipantId(input.target.value); setManualWinner(""); }}><option value="">Choose a participant</option>{participants.map((participant) => <option key={participant.id} value={participant.id}>{participant.name}</option>)}</select></label><span className="or-divider">or enter a name</span><input value={manualWinner} onChange={(input) => { setManualWinner(input.target.value); setWinnerParticipantId(""); }} placeholder="Manual winner name" /><button className="admin-primary-button" disabled={!winnerParticipantId && !manualWinner.trim()} type="submit">Save winner</button>{event.winner && <><label>Winner photo <span>(optional device image)</span><input accept="image/*" onChange={(input) => setWinnerPhoto(input.target.files?.[0] ?? null)} type="file" /></label><button className="admin-ghost-button" disabled={!winnerPhoto} onClick={() => void uploadWinnerPhoto()} type="button">Upload winner photo</button></>}</form>}
      </div>
      {event.voting_enabled && <section className="candidate-admin-section"><div className="admin-subheading"><h3>Competitors</h3><button className="admin-ghost-button" onClick={() => void loadVotingData()} type="button">Refresh results</button></div><div className="candidate-admin-list">{candidates.map((candidate) => <div className="candidate-admin-row" key={candidate.id}><div><strong>{candidate.name}</strong><small>{candidate.gender || "No gender set"} · {candidate.photo ? "Photo provided" : "No photo"}</small></div><button className="delete-button" onClick={() => void deactivateCandidate(candidate)} type="button">Deactivate</button></div>)}</div><form className="admin-form" onSubmit={addCandidate}><h3>Add competitor</h3><label>Name<input value={candidateName} onChange={(input) => setCandidateName(input.target.value)} required /></label><label>Gender<select value={candidateGender} onChange={(input) => setCandidateGender(input.target.value)}><option value="">Select</option><option value="male">Male</option><option value="female">Female</option><option value="other">Other</option><option value="prefer">Prefer not to say</option></select></label><label>Photo URL <span>(optional)</span><input value={candidatePhoto} onChange={(input) => setCandidatePhoto(input.target.value)} /></label><button className="admin-primary-button" type="submit">Add competitor</button></form>{event.voting_status !== "not_started" && <VoteSummary results={results} />}</section>}
    </section>
  );
}

function VoteSummary({ results }: { results: ResultRow[] }) {
  const total = results.reduce((sum, result) => sum + result.votes, 0);
  const leader = [...results].sort((a, b) => b.votes - a.votes)[0];
  const slices = results.reduce<{ value: number; color: string }[]>((items, result, index) => { const start = items.at(-1)?.value ?? 0; return [...items, { value: start + (total ? result.votes / total * 100 : 0), color: ["#d8ff3e", "#ff7045", "#657346", "#9ca095"][index % 4] }]; }, []);
  const gradient = slices.length ? `conic-gradient(${slices.map((slice, index) => `${slice.color} ${index ? slices[index - 1].value : 0}% ${slice.value}%`).join(", ")})` : "#d4d6cc";
  return <div className="admin-results"><h3>Live results</h3>{leader && <p className="leader-callout">Leading: <strong>{leader.name}</strong> · {leader.votes} vote{leader.votes === 1 ? "" : "s"}</p>}<div className="vote-chart-row"><div className="vote-pie" style={{ background: gradient }} aria-label={`Vote distribution across ${total} votes`} /><div className="vote-legend">{results.map((result, index) => <div key={result.candidate_id}><i style={{ background: ["#d8ff3e", "#ff7045", "#657346", "#9ca095"][index % 4] }} />{result.name}<b>{result.votes}</b></div>)}</div></div></div>;
}

function VotesTable({ votes }: { votes: VoteRecord[] }) {
  return <section className="admin-panel votes-panel"><div className="admin-panel-heading"><div><span className="eyebrow">VOTING LOG</span><h2>Votes</h2></div><span className="admin-count">{votes.length} votes</span></div><div className="votes-table-wrap"><table><thead><tr><th>Voter</th><th>Identifier</th><th>Candidate</th><th>Event</th><th>Timestamp</th></tr></thead><tbody>{votes.length === 0 ? <tr><td colSpan={5} className="admin-muted">No votes recorded.</td></tr> : votes.map((vote, index) => <tr key={`${vote.voter_roll_number ?? vote.free_voter_identifier}-${vote.created_at}-${index}`}><td>{vote.voter_name}</td><td>{vote.voter_roll_number || vote.free_voter_identifier || "—"}</td><td>{vote.candidate_name}</td><td>{vote.event_id}</td><td>{new Date(vote.created_at).toLocaleString()}</td></tr>)}</tbody></table></div></section>;
}
