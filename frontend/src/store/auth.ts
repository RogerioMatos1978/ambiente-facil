"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Usuario } from "@/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  usuario: Usuario | null;
  setTokens: (access: string, refresh: string) => void;
  setUsuario: (usuario: Usuario) => void;
  logout: () => void;
  isAdmin: () => boolean;
  isVigilante: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      usuario: null,
      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
      setUsuario: (usuario) => set({ usuario }),
      logout: () => set({ accessToken: null, refreshToken: null, usuario: null }),
      isAdmin: () => get().usuario?.papel === "admin",
      isVigilante: () => get().usuario?.papel === "vigilante",
    }),
    { name: "ambiente-facil-auth" }
  )
);
