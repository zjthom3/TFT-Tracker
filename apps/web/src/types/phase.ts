export type PhaseState = {
  asset_id: string;
  ticker: string;
  display_ticker?: string | null;
  asset_name?: string | null;
  asset_type: string;
  phase: string;
  confidence?: number | null;
  rationale?: string | null;
  computed_at: string;
  sentiment_score?: number | null;
  sentiment_delta?: number | null;
};
