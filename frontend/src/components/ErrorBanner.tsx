interface Props {
  message: string
  onDismiss?: () => void
}

const ERROR_MAP: Record<string, string> = {
  "Failed to fetch":
    "Impossible de contacter le serveur. Verifiez que le serveur est bien demarre.",
  "API 500":
    "Le serveur a rencontre une erreur interne. Reessayez dans quelques instants.",
  "API 503":
    "Un service est temporairement indisponible (base de donnees ou IA). Reessayez dans un moment.",
  "API 504":
    "La requete a mis trop de temps. Essayez de reformuler votre question plus simplement.",
  "API 401":
    "Votre session a expire. Veuillez vous reconnecter.",
  "AbortError":
    "La requete a ete annulee car elle prenait trop de temps (plus de 2 minutes).",
  "TimeoutError":
    "La requete a ete annulee car elle prenait trop de temps (plus de 2 minutes).",
}

function translateError(raw: string): string {
  for (const [key, msg] of Object.entries(ERROR_MAP)) {
    if (raw.includes(key)) return msg
  }
  if (raw.includes("API 4") || raw.includes("API 5")) {
    return `Erreur serveur : ${raw}`
  }
  return raw
}

export function ErrorBanner({ message, onDismiss }: Props) {
  const translated = translateError(message)

  return (
    <div className="bg-destructive/10 border border-destructive/20 rounded-lg px-4 py-3 mb-4 flex items-start gap-3">
      <span className="text-destructive text-lg shrink-0">&#x26A0;</span>
      <div className="flex-1">
        <p className="text-sm text-destructive">{translated}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-destructive/60 hover:text-destructive text-sm shrink-0"
        >
          &#x2715;
        </button>
      )}
    </div>
  )
}
