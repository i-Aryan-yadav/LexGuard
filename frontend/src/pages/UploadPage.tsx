import { Layout } from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "@/components/RiskBadge";
import { uploadContract, getContract } from "@/lib/api";
import { Contract } from "@/lib/types";
import { useState, useCallback, useRef, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Upload, FileText, Loader2, CheckCircle2, ArrowRight, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { motion, AnimatePresence } from "framer-motion";

const steps = [
  "Extracting text…",
  "Segmenting clauses…",
  "Classifying & scoring…",
  "Generating AI explanations…",
  "Done! ✓",
];

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [recentContracts, setRecentContracts] = useState<Contract[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setStepIndex(0);

    const interval = setInterval(() => {
      setStepIndex((prev) => Math.min(prev + 1, steps.length - 1));
    }, 1500);

    try {
      const { contract_id } = await uploadContract(file);
      clearInterval(interval);
      setStepIndex(steps.length - 1);
      toast({ title: "Contract uploaded successfully", description: "Redirecting to report..." });
      setTimeout(() => navigate(`/contracts/${contract_id}`), 1000);
    } catch {
      clearInterval(interval);
      toast({ title: "Upload failed", description: "Could not connect to analyzer. Check that the backend is running.", variant: "destructive" });
      setUploading(false);
      setStepIndex(0);
    }
  };

  const clearFile = () => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <Layout>
      <div className="container py-16 max-w-3xl">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-3xl font-bold mb-2">Upload Contract</h1>
          <p className="text-muted-foreground mb-8">Upload a PDF, DOCX, or TXT file to get a full AI risk analysis.</p>

          {/* Drop zone */}
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onClick={() => !file && inputRef.current?.click()}
            className={`glass-card p-12 text-center cursor-pointer transition-all duration-300 border-2 border-dashed ${
              dragOver ? "border-primary bg-primary/5" : file ? "border-risk-low/40" : "border-border hover:border-primary/40"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])}
            />
            {file ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="h-8 w-8 text-primary" />
                <div className="text-left">
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
                <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); clearFile(); }}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <>
                <Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4 animate-float" />
                <p className="font-medium mb-1">Drag & drop your contract here</p>
                <p className="text-sm text-muted-foreground">or click to browse — PDF, DOCX, TXT</p>
              </>
            )}
          </div>

          {/* Upload Button */}
          <div className="mt-6">
            <Button
              variant="hero"
              size="lg"
              className="w-full h-12"
              disabled={!file || uploading}
              onClick={handleUpload}
            >
              {uploading ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> {steps[stepIndex]}</>
              ) : (
                <>Analyze Contract <ArrowRight className="ml-2 h-4 w-4" /></>
              )}
            </Button>
          </div>

          {/* Processing Info */}
          <AnimatePresence>
            {uploading && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-6 glass-card p-4"
              >
                <h3 className="text-sm font-semibold mb-3">What's happening:</h3>
                <div className="space-y-2">
                  {steps.map((s, i) => (
                    <div key={s} className={`flex items-center gap-2 text-sm ${i <= stepIndex ? "text-foreground" : "text-muted-foreground/50"}`}>
                      {i < stepIndex ? (
                        <CheckCircle2 className="h-4 w-4 text-risk-low" />
                      ) : i === stepIndex ? (
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border border-border" />
                      )}
                      {s}
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Recent Uploads placeholder */}
          <div className="mt-16">
            <h2 className="text-xl font-semibold mb-4">Recent Uploads</h2>
            <div className="glass-card p-8 text-center text-muted-foreground">
              <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No contracts analyzed yet. Upload your first contract above.</p>
            </div>
          </div>
        </motion.div>
      </div>
    </Layout>
  );
}
