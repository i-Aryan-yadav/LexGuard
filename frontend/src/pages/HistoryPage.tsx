import { Layout } from "@/components/Layout";
import { RiskBadge } from "@/components/RiskBadge";
import { RiskGauge } from "@/components/RiskGauge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { listContracts } from "@/lib/api";
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, FileText, Upload, ArrowRight, ArrowUpDown, Loader2, AlertTriangle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface ContractSummary {
  id: string;
  file_name: string;
  upload_time: string;
  overall_risk_score: number;
  overall_risk_level: string;
  top_risk_drivers: string;
  clause_count: number;
}

export default function HistoryPage() {
  const [contracts, setContracts] = useState<ContractSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"date" | "risk">("date");

  useEffect(() => {
    listContracts()
      .then((data) => { setContracts(data); setLoading(false); })
      .catch(() => { setError("Could not load contracts. Make sure the backend is running."); setLoading(false); });
  }, []);

  const filtered = contracts
    .filter((c) => c.file_name.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === "risk") return b.overall_risk_score - a.overall_risk_score;
      return new Date(b.upload_time).getTime() - new Date(a.upload_time).getTime();
    });

  if (loading) {
    return (
      <Layout>
        <div className="container py-16 space-y-6">
          <Skeleton className="h-8 w-48" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-44" />)}
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container py-16">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-3xl font-bold mb-2">Contract History</h1>
          <p className="text-muted-foreground mb-8">Browse all previously analyzed contracts.</p>

          {error && (
            <div className="glass-card p-6 mb-8 flex items-center gap-3 text-risk-high">
              <AlertTriangle className="h-5 w-5 shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          <div className="flex flex-wrap gap-3 mb-8">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by file name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 bg-card border-border"
              />
            </div>
            <Button
              variant="glass"
              size="sm"
              onClick={() => setSortBy(sortBy === "date" ? "risk" : "date")}
            >
              <ArrowUpDown className="h-4 w-4 mr-2" />
              Sort by {sortBy === "date" ? "Risk Score" : "Date"}
            </Button>
          </div>

          {filtered.length === 0 ? (
            <div className="glass-card p-16 text-center">
              <FileText className="h-16 w-16 text-muted-foreground/30 mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">No contracts yet</h2>
              <p className="text-muted-foreground mb-6">Upload your first contract to see it analyzed here.</p>
              <Button asChild variant="hero">
                <Link to="/upload">
                  <Upload className="h-4 w-4 mr-2" /> Upload Contract
                </Link>
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filtered.map((c) => (
                <div key={c.id} className="glass-card-hover p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1 min-w-0 pr-4">
                      <h3 className="font-semibold truncate">{c.file_name}</h3>
                      <p className="text-xs text-muted-foreground">{new Date(c.upload_time).toLocaleDateString()}</p>
                    </div>
                    <RiskGauge score={c.overall_risk_score} level={c.overall_risk_level as any} size={60} />
                  </div>
                  <div className="flex items-center gap-3 mb-4">
                    <RiskBadge level={c.overall_risk_level as any} />
                    <span className="text-xs text-muted-foreground">{c.clause_count} clauses</span>
                  </div>
                  <Button asChild variant="ghost" size="sm" className="w-full">
                    <Link to={`/contracts/${c.id}`}>
                      Open Report <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </Layout>
  );
}

