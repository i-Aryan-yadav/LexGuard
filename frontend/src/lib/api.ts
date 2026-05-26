import { Contract } from "./types";

const BASE_URL = "http://localhost:8000";

export async function uploadContract(file: File): Promise<{ contract_id: string; message: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/api/contracts/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function getContract(contractId: string): Promise<Contract> {
  const res = await fetch(`${BASE_URL}/api/contracts/${contractId}`);
  if (!res.ok) throw new Error("Failed to fetch contract");
  return res.json();
}

export async function listContracts(): Promise<
  Array<{
    id: string;
    file_name: string;
    upload_time: string;
    overall_risk_score: number;
    overall_risk_level: string;
    top_risk_drivers: string;
    clause_count: number;
  }>
> {
  const res = await fetch(`${BASE_URL}/api/contracts/`);
  if (!res.ok) throw new Error("Failed to fetch contracts");
  return res.json();
}
