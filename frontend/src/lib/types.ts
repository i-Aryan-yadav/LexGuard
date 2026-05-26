export type RiskLevel = "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL";

export interface Clause {
  id: string;
  clause_index: number;
  clause_number: string;
  heading: string;
  depth: number;
  parent_clause: string | null;
  clause_text: string;
  clause_type: string;
  confidence_score: number;
  risk_score: number;
  risk_level: RiskLevel;
  risk_category: string;
  risky_snippet: string;
  exposed_party: string;
  explanation: string | null;
  rewrite: string | null;
}

export interface Contract {
  id: string;
  file_name: string;
  upload_time: string;
  extracted_text: string;
  overall_risk_score: number;
  overall_risk_level: RiskLevel;
  top_risk_drivers: string;
  clauses: Clause[];
}
