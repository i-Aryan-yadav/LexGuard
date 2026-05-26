import { useMemo } from "react";
import { RiskLevel } from "@/lib/types";

const riskColors: Record<string, string> = {
  HIGH: "hsl(0 86% 60%)",
  MEDIUM: "hsl(38 92% 50%)",
  LOW: "hsl(160 84% 39%)",
};

export function RiskGauge({ score, level, size = 120 }: { score: number; level: RiskLevel | string; size?: number }) {
  const color = riskColors[level?.toUpperCase()] || "hsl(220 9% 46%)";
  const pct = score / 10;
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - pct * 0.75); // 270deg arc

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-[135deg]">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="hsl(220 20% 16%)" strokeWidth={8}
          strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
          strokeLinecap="round"
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={color} strokeWidth={8}
          strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-2xl font-bold" style={{ color }}>{score.toFixed(1)}</span>
        <span className="text-[10px] text-muted-foreground font-medium">/ 10</span>
      </div>
    </div>
  );
}
