import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LucideIcon } from "lucide-react";

export function KpiCard({
  titulo, valor, icone: Icone, corIcone = "text-primary",
}: { titulo: string; valor: string | number; icone: LucideIcon; corIcone?: string }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{titulo}</CardTitle>
        <Icone className={`h-5 w-5 ${corIcone}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{valor}</div>
      </CardContent>
    </Card>
  );
}
