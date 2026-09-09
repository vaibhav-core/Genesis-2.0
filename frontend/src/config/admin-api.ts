export const ADMIN_API_BASE = "/backend-api";

export interface AdminEvent {
  id: number;
  name: string;
  description?: string | null;
  start_time?: string | null;
  end_time?: string | null;
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
  voter_roll_number: string;
  candidate_name: string;
  category: string;
  created_at: string;
}