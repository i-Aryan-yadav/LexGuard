import { Layout } from "@/components/Layout";
import { motion } from "framer-motion";
import { Brain, Sparkles, Shield, Layers, ChevronDown } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const techStack = [
  { icon: Brain, title: "LegalBERT", desc: "Fine-tuned transformer model for legal clause classification across 11+ clause types." },
  { icon: Sparkles, title: "Google Gemini AI", desc: "Generates plain-English risk explanations and clause rewrite suggestions for high-risk clauses." },
  { icon: Shield, title: "10-Signal Risk Engine", desc: "Comprehensive risk scoring system analyzing 10 distinct legal risk signals per clause." },
  { icon: Layers, title: "Hierarchy-Aware Segmentation", desc: "Intelligent clause extraction preserving document structure, nesting, and clause numbering." },
];

const riskSignals = [
  { name: "Unlimited Liability", desc: "Clause exposes a party to unlimited financial liability.", category: "Financial Exposure" },
  { name: "Forfeiture Right", desc: "Allows one party to reclaim assets or rights without due process.", category: "Financial Exposure" },
  { name: "One-sided Termination", desc: "Grants termination rights exclusively to one party.", category: "Power Imbalance" },
  { name: "Unqualified Discretion", desc: "Gives one party unrestricted decision-making power.", category: "Power Imbalance" },
  { name: "Power Reservation", desc: "Reserves critical rights or powers for a single party.", category: "Power Imbalance" },
  { name: "Forced Arbitration", desc: "Mandates arbitration, potentially limiting legal recourse.", category: "Dispute Risk" },
  { name: "Biased Arbitration", desc: "Arbitration setup favors one party in venue, rules, or selection.", category: "Dispute Risk" },
  { name: "Broad Indemnity", desc: "Requires indemnification for a wide range of claims.", category: "Financial Exposure" },
  { name: "Financial Deposit Risk", desc: "Requires significant upfront financial deposits with limited return conditions.", category: "Financial Exposure" },
  { name: "Penalty Clause", desc: "Imposes penalties that may be disproportionate to actual damages.", category: "Financial Exposure" },
];

const clauseTypes = [
  "Termination", "Indemnity", "Financial Risk", "Dispute Resolution",
  "Liability", "Governing Law", "Confidentiality", "Force Majeure",
  "Payment", "Renewal", "Assignment",
];

const scoreScale = [
  { range: "0–3", label: "Low Risk", color: "bg-risk-low" },
  { range: "4–6", label: "Medium Risk", color: "bg-risk-medium" },
  { range: "7–10", label: "High Risk", color: "bg-risk-high" },
];

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.5 } }),
};

export default function AboutPage() {
  return (
    <Layout>
      <div className="container py-16 max-w-4xl">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-3xl font-bold mb-2">How LexiGuard AI Works</h1>
          <p className="text-muted-foreground mb-12">Understanding the technology behind our contract risk analysis engine.</p>

          {/* Tech Stack */}
          <section className="mb-16">
            <h2 className="text-xl font-bold mb-6">Technology Stack</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {techStack.map((t, i) => (
                <motion.div key={t.title} custom={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} className="glass-card-hover p-6">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                    <t.icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="font-semibold mb-2">{t.title}</h3>
                  <p className="text-sm text-muted-foreground">{t.desc}</p>
                </motion.div>
              ))}
            </div>
          </section>

          {/* Risk Signals */}
          <section className="mb-16">
            <h2 className="text-xl font-bold mb-6">10 Risk Signals Explained</h2>
            <Accordion type="multiple" className="space-y-2">
              {riskSignals.map((s) => (
                <AccordionItem key={s.name} value={s.name} className="glass-card border-border px-4">
                  <AccordionTrigger className="text-sm font-medium hover:no-underline">
                    <div className="flex items-center gap-3">
                      <span>{s.name}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-muted text-muted-foreground">{s.category}</span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="text-sm text-muted-foreground">
                    {s.desc}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </section>

          {/* Clause Types */}
          <section className="mb-16">
            <h2 className="text-xl font-bold mb-6">Clause Types Detected</h2>
            <div className="flex flex-wrap gap-2">
              {clauseTypes.map((t) => (
                <span key={t} className="px-3 py-1.5 rounded-full text-sm font-medium bg-muted text-muted-foreground border border-border">
                  {t}
                </span>
              ))}
            </div>
          </section>

          {/* Risk Score Scale */}
          <section className="mb-16">
            <h2 className="text-xl font-bold mb-6">Risk Score Scale</h2>
            <div className="glass-card p-6">
              <div className="flex rounded-full overflow-hidden h-4 mb-4">
                <div className="flex-1 bg-risk-low" />
                <div className="flex-1 bg-risk-medium" />
                <div className="flex-1 bg-risk-high" />
              </div>
              <div className="flex justify-between">
                {scoreScale.map((s) => (
                  <div key={s.range} className="text-center">
                    <div className={`inline-block w-3 h-3 rounded-full ${s.color} mb-1`} />
                    <div className="text-sm font-medium">{s.label}</div>
                    <div className="text-xs text-muted-foreground">{s.range}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </motion.div>
      </div>
    </Layout>
  );
}
