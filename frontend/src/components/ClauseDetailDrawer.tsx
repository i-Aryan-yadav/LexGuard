import { Clause } from "@/lib/types";
import { RiskBadge, RiskScoreBar } from "./RiskBadge";
import { X, Copy, Check } from "lucide-react";
import { Button } from "./ui/button";
import { useState } from "react";
import { ScrollArea } from "./ui/scroll-area";

export function ClauseDetailDrawer({ clause, onClose }: { clause: Clause; onClose: () => void }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const highlightSnippet = (text: string, snippet: string) => {
    if (!snippet) return text;
    const idx = text.indexOf(snippet);
    if (idx === -1) return text;
    return (
      <>
        {text.slice(0, idx)}
        <mark className="bg-risk-high/20 text-risk-high px-0.5 rounded">{snippet}</mark>
        {text.slice(idx + snippet.length)}
      </>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-background/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-lg bg-card border-l border-border animate-in slide-in-from-right duration-300">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h3 className="font-semibold">Clause {clause.clause_number}</h3>
            <p className="text-sm text-muted-foreground">{clause.heading || clause.clause_type}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <ScrollArea className="h-[calc(100vh-73px)]">
          <div className="p-4 space-y-6">
            <div className="flex items-center gap-3">
              <RiskBadge level={clause.risk_level} />
              <span className="text-sm font-mono text-muted-foreground">Score: {clause.risk_score}/10</span>
              <span className="text-xs text-muted-foreground">Confidence: {(clause.confidence_score * 100).toFixed(0)}%</span>
            </div>

            <div className="space-y-1">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Clause Text</h4>
              <div className="glass-card p-4 text-sm leading-relaxed">
                {highlightSnippet(clause.clause_text, clause.risky_snippet)}
              </div>
            </div>

            {clause.risk_category && (
              <div className="space-y-1">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Risk Category</h4>
                <p className="text-sm">{clause.risk_category}</p>
              </div>
            )}

            {clause.exposed_party && (
              <div className="space-y-1">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Exposed Party</h4>
                <p className="text-sm">{clause.exposed_party}</p>
              </div>
            )}

            {clause.explanation && (
              <div className="space-y-1">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">AI Explanation</h4>
                <div className="glass-card p-4 border-l-2 border-primary text-sm leading-relaxed italic">
                  {clause.explanation}
                </div>
              </div>
            )}

            {clause.rewrite && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Suggested Rewrite</h4>
                  <Button variant="ghost" size="sm" onClick={() => handleCopy(clause.rewrite!)}>
                    {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                    <span className="ml-1 text-xs">{copied ? "Copied" : "Copy"}</span>
                  </Button>
                </div>
                <div className="glass-card p-4 font-mono text-sm leading-relaxed border-l-2 border-risk-low">
                  {clause.rewrite}
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
