import { Layout } from "@/components/Layout";
import { RiskBadge, RiskScoreBar } from "@/components/RiskBadge";
import { RiskGauge } from "@/components/RiskGauge";
import { ClauseDetailDrawer } from "@/components/ClauseDetailDrawer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getContract } from "@/lib/api";
import { Contract, Clause, RiskLevel } from "@/lib/types";
import { useParams } from "react-router-dom";
import { useEffect, useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Download, Copy, Share2, Search, ChevronRight,
  FileText, Clock, AlertTriangle, Filter
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const CLAUSES_PER_PAGE = 25;

export default function ContractReportPage() {
  const { id } = useParams<{ id: string }>();
  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClause, setSelectedClause] = useState<Clause | null>(null);
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const { toast } = useToast();

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getContract(id)
      .then((c) => { setContract(c); setLoading(false); })
      .catch(() => { setError("Could not load contract. Make sure the backend is running."); setLoading(false); });
  }, [id]);

  const topDrivers = useMemo(() => {
    if (!contract) return [];
    try { return JSON.parse(contract.top_risk_drivers); } catch { return []; }
  }, [contract]);

  const clauseTypes = useMemo(() => {
    if (!contract) return [];
    return [...new Set(contract.clauses.map((c) => c.clause_type))];
  }, [contract]);

  const filteredClauses = useMemo(() => {
    if (!contract) return [];
    return contract.clauses.filter((c) => {
      if (riskFilter !== "ALL" && c.risk_level?.toUpperCase() !== riskFilter) return false;
      if (typeFilter !== "ALL" && c.clause_type !== typeFilter) return false;
      if (search && !c.clause_text.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [contract, riskFilter, typeFilter, search]);

  const paginatedClauses = filteredClauses.slice((page - 1) * CLAUSES_PER_PAGE, page * CLAUSES_PER_PAGE);
  const totalPages = Math.ceil(filteredClauses.length / CLAUSES_PER_PAGE);

  const riskDistribution = useMemo(() => {
    if (!contract) return { HIGH: 0, MEDIUM: 0, LOW: 0, INFORMATIONAL: 0 };
    const dist: Record<string, number> = { HIGH: 0, MEDIUM: 0, LOW: 0, INFORMATIONAL: 0 };
    contract.clauses.forEach((c) => {
      const key = c.risk_level?.toUpperCase() || "INFORMATIONAL";
      dist[key] = (dist[key] || 0) + 1;
    });
    return dist;
  }, [contract]);

  const categoryBreakdown = useMemo(() => {
    if (!contract) return {};
    const cats: Record<string, number> = {};
    contract.clauses.forEach((c) => { cats[c.risk_category] = (cats[c.risk_category] || 0) + 1; });
    return cats;
  }, [contract]);

  const copyId = () => {
    if (id) navigator.clipboard.writeText(id);
    toast({ title: "Contract ID copied" });
  };

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    toast({ title: "Link copied to clipboard" });
  };

  if (loading) {
    return (
      <Layout>
        <div className="container py-16 space-y-6">
          <Skeleton className="h-8 w-64" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Skeleton className="h-48" /><Skeleton className="h-48" /><Skeleton className="h-48" />
          </div>
          <Skeleton className="h-96" />
        </div>
      </Layout>
    );
  }

  if (error || !contract) {
    return (
      <Layout>
        <div className="container py-16 text-center">
          <AlertTriangle className="h-12 w-12 text-risk-high mx-auto mb-4" />
          <h1 className="text-xl font-semibold mb-2">Error Loading Contract</h1>
          <p className="text-muted-foreground">{error}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container py-10">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-start gap-6 mb-10">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <FileText className="h-5 w-5 text-primary" />
                <h1 className="text-2xl font-bold">{contract.file_name}</h1>
              </div>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {new Date(contract.upload_time).toLocaleString()}</span>
                <span>{contract.clauses.length} clauses analyzed</span>
              </div>
              <div className="flex flex-wrap gap-2 mt-3">
                <RiskBadge level={contract.overall_risk_level} className="text-sm px-3 py-1" />
                {topDrivers.map((d: string) => (
                  <span key={d} className="px-2 py-1 rounded-md bg-muted text-xs font-medium">{d}</span>
                ))}
              </div>
            </div>
            <RiskGauge score={contract.overall_risk_score} level={contract.overall_risk_level} size={130} />
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3 mb-10">
            <Button variant="glass" size="sm"><Download className="h-4 w-4 mr-2" /> Download Report</Button>
            <Button variant="glass" size="sm" onClick={copyId}><Copy className="h-4 w-4 mr-2" /> Copy ID</Button>
            <Button variant="glass" size="sm" onClick={copyLink}><Share2 className="h-4 w-4 mr-2" /> Share</Button>
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            {/* Risk Distribution */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold mb-4">Risk Distribution</h3>
              <div className="space-y-3">
                {(["HIGH", "MEDIUM", "LOW", "INFORMATIONAL"] as RiskLevel[]).map((level) => (
                  <div key={level} className="flex items-center gap-3">
                    <RiskBadge level={level} />
                    <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${level === "HIGH" ? "bg-risk-high" : level === "MEDIUM" ? "bg-risk-medium" : level === "LOW" ? "bg-risk-low" : "bg-risk-info"
                          }`}
                        style={{ width: `${contract.clauses.length ? (riskDistribution[level] / contract.clauses.length) * 100 : 0}%` }}
                      />
                    </div>
                    <span className="text-sm font-mono w-6 text-right">{riskDistribution[level]}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Clause Types */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold mb-4">Clause Types</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                {clauseTypes.map((t) => {
                  const count = contract.clauses.filter((c) => c.clause_type === t).length;
                  return (
                    <div key={t} className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">{t}</span>
                      <span className="font-mono">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Category Breakdown */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold mb-4">Category Breakdown</h3>
              <div className="space-y-3">
                {Object.entries(categoryBreakdown).map(([cat, count]) => (
                  <div key={cat} className="flex items-center justify-between text-sm">
                    <span>{cat}</span>
                    <span className="font-mono text-muted-foreground">{count as number} clauses</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Clause Explorer */}
          <div className="mb-6">
            <h2 className="text-xl font-bold mb-4">Clause Explorer</h2>
            <div className="flex flex-wrap gap-3 mb-4">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search clauses..."
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                  className="pl-9 bg-card border-border"
                />
              </div>
              <Select value={riskFilter} onValueChange={(v) => { setRiskFilter(v); setPage(1); }}>
                <SelectTrigger className="w-40 bg-card"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Levels</SelectItem>
                  <SelectItem value="HIGH">High Risk</SelectItem>
                  <SelectItem value="MEDIUM">Medium Risk</SelectItem>
                  <SelectItem value="LOW">Low Risk</SelectItem>
                  <SelectItem value="INFORMATIONAL">Informational</SelectItem>
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={(v) => { setTypeFilter(v); setPage(1); }}>
                <SelectTrigger className="w-44 bg-card"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  {clauseTypes.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            {/* Clause List */}
            <div className="space-y-2">
              {paginatedClauses.map((clause) => (
                <div
                  key={clause.id}
                  onClick={() => setSelectedClause(clause)}
                  className="glass-card-hover p-4 cursor-pointer flex items-center gap-4"
                >
                  <span className="text-sm font-mono text-muted-foreground w-12 shrink-0">{clause.clause_number}</span>
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-muted">{clause.clause_type}</span>
                  <RiskBadge level={clause.risk_level} />
                  <div className="flex-1 min-w-0">
                    <RiskScoreBar score={clause.risk_score} />
                  </div>
                  <span className="text-xs text-muted-foreground hidden md:block">{clause.risk_category}</span>
                  <span className="text-xs text-muted-foreground hidden lg:block">{clause.exposed_party}</span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </div>
              ))}
              {paginatedClauses.length === 0 && (
                <div className="glass-card p-8 text-center text-muted-foreground">
                  No clauses match your filters.
                </div>
              )}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <Button variant="ghost" size="sm" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</Button>
                <span className="text-sm text-muted-foreground">Page {page} of {totalPages}</span>
                <Button variant="ghost" size="sm" disabled={page === totalPages} onClick={() => setPage(page + 1)}>Next</Button>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Clause Detail Drawer */}
      {selectedClause && (
        <ClauseDetailDrawer clause={selectedClause} onClose={() => setSelectedClause(null)} />
      )}
    </Layout>
  );
}
