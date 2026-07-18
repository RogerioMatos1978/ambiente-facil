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

const RECONEXAO_MS = 3000;

/**
 * Conecta ao WebSocket do painel em tempo real (Django Channels) e mantém
 * o último evento recebido, para atualizar o status livre/ocupado dos ambientes.
 *
 * Reconecta automaticamente se a conexão cair (ex.: timeout momentâneo do
 * Redis usado pelo channel layer), em vez de ficar "Desconectado" até o
 * usuário recarregar a página manualmente.
 */
export function usePainelTempoReal() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [ultimoEvento, setUltimoEvento] = useState<EventoPainel | null>(null);
  const [conectado, setConectado] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconectarTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const montadoRef = useRef(true);

  useEffect(() => {
    montadoRef.current = true;

    if (!accessToken) return;

    function conectar() {
      const wsBase = API_BASE_URL.replace(/^http/, "ws");
      const socket = new WebSocket(`${wsBase}/ws/painel-ambientes/?token=${accessToken}`);
      socketRef.current = socket;

      socket.onopen = () => setConectado(true);

      socket.onclose = () => {
        setConectado(false);
        // Só tenta reconectar se o componente ainda estiver montado e o
        // usuário ainda estiver autenticado (fechamento intencional via
        // logout não deve gerar retries).
        if (montadoRef.current && useAuthStore.getState().accessToken) {
          reconectarTimeoutRef.current = setTimeout(conectar, RECONEXAO_MS);
        }
      };

      socket.onerror = () => {
        socket.close();
      };

      socket.onmessage = (event) => {
        try {
          setUltimoEvento(JSON.parse(event.data));
        } catch {
          // ignora mensagens inválidas
        }
      };
    }

    conectar();

    return () => {
      montadoRef.current = false;
      if (reconectarTimeoutRef.current) {
        clearTimeout(reconectarTimeoutRef.current);
      }
      socketRef.current?.close();
    };
  }, [accessToken]);

  return { ultimoEvento, conectado };
}
