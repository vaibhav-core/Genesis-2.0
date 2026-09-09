export const ADMIN_API_BASE = "/backend-api";

export interface AdminEvent {
  id: number;
  name: string;
  description?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  location?: string | null;
  competition_format?: "individual" | "team" | null;
  voting_enabled: boolean;
  voting_status: "not_started" | "open" | "closed";
  winner?: string | null;
  winner_participant_id?: number | null;
}

export interface TeamMember {
  id: number;
  name: string;
  roll_number?: string | null;
}

export interface Participant {
  id: number;
  event_id: number;
  participant_type: "individual" | "team";
  name: string;
  roll_number?: string | null;
  members: TeamMember[];
}

export interface VoteRecord {
  voter_name: string;
  voter_roll_number?: string | null;
  candidate_name: string;
  event_id: number;
  created_at: string;
  free_voter_identifier?: string | null;
}

export interface Candidate {
  id: number;
  event_id: number;
  name: string;
  gender?: "male" | "female" | "other" | null;
  photo?: string | null;
  active: boolean;
}

export interface ResultRow {
  candidate_id: number;
  name: string;
  votes: number;
}