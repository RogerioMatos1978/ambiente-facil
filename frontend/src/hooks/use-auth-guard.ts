"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

/** Garante que a rota só renderize para usuários autenticados; redireciona para /login caso contrário. */
export function useAuthGuard() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const [pronto, setPronto] = useState(false);

  useEffect(() => {
    if (!accessToken) {
      router.replace("/login");
    } else {
      setPronto(true);
    }
  }, [accessToken, router]);

  return pronto;
}
