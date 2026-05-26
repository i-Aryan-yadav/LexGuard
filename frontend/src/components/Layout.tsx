import { Link, useLocation } from "react-router-dom";
import { Scale, Upload, Clock, Info, Wifi } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", label: "Home", icon: Scale },
  { to: "/upload", label: "Upload", icon: Upload },
  { to: "/history", label: "History", icon: Clock },
  { to: "/about", label: "About", icon: Info },
];

export function Navbar() {
  const { pathname } = useLocation();
  return (
    <header className="fixed top-0 inset-x-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <nav className="container flex items-center justify-between h-16">
        <Link to="/" className="flex items-center gap-2 font-bold text-lg">
          <Scale className="h-5 w-5 text-primary" />
          <span className="gradient-text">LexiGuard AI</span>
        </Link>
        <div className="flex items-center gap-1">
          {navItems.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "px-3 py-2 rounded-md text-sm font-medium transition-colors",
                pathname === to ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {label}
            </Link>
          ))}
          <div className="ml-4 flex items-center gap-1.5 text-xs text-muted-foreground">
            <Wifi className="h-3 w-3 text-risk-low" />
            <span>Connected</span>
          </div>
        </div>
      </nav>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-border/50 py-8 mt-20">
      <div className="container flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-primary" />
          <span className="font-semibold gradient-text">LexiGuard AI</span>
        </div>
        <div className="flex gap-6">
          {navItems.map(({ to, label }) => (
            <Link key={to} to={to} className="hover:text-foreground transition-colors">{label}</Link>
          ))}
        </div>
        <p>© 2026 LexiGuard AI. All rights reserved.</p>
      </div>
    </footer>
  );
}

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-16">{children}</main>
      <Footer />
    </div>
  );
}
