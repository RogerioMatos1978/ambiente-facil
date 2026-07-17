"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import {
  LayoutDashboard, CalendarDays, Building2, ClipboardList, Users, ShieldCheck,
} from "lucide-react";

const itens = [
  { href: "/dashboard", label: "Dashboard", icone: LayoutDashboard, adminOnly: false },
  { href: "/calendario", label: "Calendário", icone: CalendarDays, adminOnly: false },
  { href: "/reservas", label: "Reservas", icone: ClipboardList, adminOnly: false },
  { href: "/ambientes", label: "Ambientes", icone: Building2, adminOnly: false },
  { href: "/usuarios", label: "Usuários", icone: Users, adminOnly: true },
  { href: "/auditoria", label: "Auditoria", icone: ShieldCheck, adminOnly: true },
];

export function Sidebar() {
  const pathname = usePathname();
  const isAdmin = useAuthStore((s) => s.isAdmin());

  return (
    <aside className="hidden w-64 shrink-0 border-r bg-card md:flex md:flex-col">
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
          AF
        </div>
        <span className="font-semibold">Ambiente Fácil</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {itens
          .filter((item) => !item.adminOnly || isAdmin)
          .map((item) => {
            const ativo = pathname?.startsWith(item.href);
            const Icone = item.icone;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  ativo ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icone className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
      </nav>
    </aside>
  );
}
