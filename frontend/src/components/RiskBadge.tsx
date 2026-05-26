import { RiskLevel } from "@/lib/types";
import { cn } from "@/lib/utils";

const riskConfig: Record<RiskLevel, { label: string; className: string }> = {
  HIGH: { label: "High Risk", className: "bg-risk-high/15 text-risk-high border-risk-high/30" },
  MEDIUM: { label: "Medium Risk", className: "bg-risk-medium/15 text-risk-medium border-risk-medium/30" },
  LOW: { label: "Low Risk", className: "bg-risk-low/15 text-risk-low border-risk-low/30" },
  INFORMATIONAL: { label: "Info", className: "bg-risk-info/15 text-risk-info border-risk-info/30" },
};

export function RiskBadge({ level, className }: { level: RiskLevel | string; className?: string }) {
  const config = riskConfig[(level?.toUpperCase() as RiskLevel)] ?? riskConfig["INFORMATIONAL"];
  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border", config.className, className)}>
      {config.label}
    </span>
  );
}

export function RiskScoreBar({ score, className }: { score: number; className?: string }) {
  const pct = (score / 10) * 100;
  const color = score >= 7 ? "bg-risk-high" : score >= 4 ? "bg-risk-medium" : "bg-risk-low";
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={cn("h-full rounded-full transition-all duration-500", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-muted-foreground w-8">{score.toFixed(1)}</span>
    </div>
  );
}
