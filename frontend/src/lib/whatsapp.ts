/** Monta um link wa.me client-side a partir de telefone e mensagem (fallback quando não usar o endpoint do backend). */
export function montarLinkWhatsApp(telefoneE164: string, mensagem: string): string {
  const numero = telefoneE164.replace(/\D/g, "");
  return `https://wa.me/${numero}?text=${encodeURIComponent(mensagem)}`;
}
