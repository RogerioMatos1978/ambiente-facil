"use client";
import { useEffect, useRef, useState } from "react";
import { useAuthStore } from "@/store/auth";
import { API_BASE_URL } from "@/lib/api";

export interface EventoPainel {
  tipo: string;
  ambiente_id?: number;
  reserva_id?: number;
  status?: string;
  [key: string]: unknown;
}

/**
 * Conecta ao WebSocket do painel em tempo real (Django Channels) e mantém
 * o último evento recebido, para atualizar o status livre/ocupado dos ambientes.
 */
export function usePainelTempoReal() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [ultimoEvento, setUltimoEvento] = useState<EventoPainel | null>(null);
  const [conectado, setConectado] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!accessToken) return;

    const wsBase = API_BASE_URL.replace(/^http/, "ws");
    const socket = new WebSocket(`${wsBase}/ws/painel-ambientes/?token=${accessToken}`);
    socketRef.current = socket;

    socket.onopen = () => setConectado(true);
    socket.onclose = () => setConectado(false);
    socket.onmessage = (event) => {
      try {
        setUltimoEvento(JSON.parse(event.data));
      } catch {
        // ignora mensagens inválidas
      }
    };

    return () => socket.close();
  }, [accessToken]);

  return { ultimoEvento, conectado };
}
