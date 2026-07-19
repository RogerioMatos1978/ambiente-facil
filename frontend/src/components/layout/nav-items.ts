import {
  LayoutDashboard, CalendarDays, Building2, ClipboardList, Users, ShieldCheck, BarChart3, type LucideIcon,
} from "lucide-react";

export interface ItemNavegacao {
  href: string;
  label: string;
  icone: LucideIcon;
  adminOnly: boolean;
}

export const itensNavegacao: ItemNavegacao[] = [
  { href: "/dashboard", label: "Dashboard", icone: LayoutDashboard, adminOnly: false },
  { href: "/calendario", label: "Calendário", icone: CalendarDays, adminOnly: false },
  { href: "/reservas", label: "Reservas", icone: ClipboardList, adminOnly: false },
  { href: "/relatorios", label: "Relatórios", icone: BarChart3, adminOnly: false },
  { href: "/ambientes", label: "Ambientes", icone: Building2, adminOnly: false },
  { href: "/usuarios", label: "Usuários", icone: Users, adminOnly: true },
  { href: "/auditoria", label: "Auditoria", icone: ShieldCheck, adminOnly: true },
];
