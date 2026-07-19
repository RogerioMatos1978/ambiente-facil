"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

/** Garante que a rota só renderize para usuários autenticados; redireciona para /login caso contrário. */
export function useAuthGuard() {
  const router = useRouter();
  const pathname = usePathname();
  const accessToken = useAuthStore((s) => s.accessToken);
  const [pronto, setPronto] = useState(false);

  useEffect(() => {
    if (!accessToken) {
      const next = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${next}`);
    } else {
      setPronto(true);
    }
  }, [accessToken, pathname, router]);

  return pronto;
}
