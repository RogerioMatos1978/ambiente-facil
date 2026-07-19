export type Papel = "admin" | "user";

export interface Usuario {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  papel: Papel;
  telefone: string;
  departamento: string;
  ativo_institucional: boolean;
  is_active: boolean;
  date_joined: string;
}

export type TipoAmbiente = "sala_aula" | "auditorio" | "laboratorio" | "sala_reuniao" | "outro";

export interface Ambiente {
  id: number;
  nome: string;
  tipo: TipoAmbiente;
  localizacao: string;
  capacidade: number;
  recursos: string[];
  descricao: string;
  foto: string | null;
  ativo: boolean;
  exige_checkin: boolean;
  tolerancia_checkin_minutos: number;
  status_atual: "livre" | "ocupado";
  criado_em: string;
  atualizado_em: string;
}

export type StatusReserva = "pendente" | "confirmada" | "cancelada" | "concluida" | "expirada";

export interface Reserva {
  id: number;
  ambiente: number;
  ambiente_detalhe: Ambiente;
  solicitante: number;
  solicitante_nome: string;
  titulo: string;
  descricao: string;
  data_inicio: string;
  data_fim: string;
  status: StatusReserva;
  status_display: string;
  motivo_cancelamento: string;
  cancelado_por: number | null;
  cancelado_em: string | null;
  notificar_email: boolean;
  checkin_confirmado_em: string | null;
  precisa_checkin: boolean;
  prazo_checkin: string;
  criado_em: string;
  atualizado_em: string;
}

export interface LogAuditoria {
  id: number;
  usuario: number | null;
  usuario_nome: string;
  acao: string;
  entidade: string;
  entidade_id: string | null;
  descricao: string;
  detalhes: Record<string, unknown>;
  endereco_ip: string | null;
  criado_em: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
