import { useCallback, useState } from "react"
import { v4 as uuidv4 } from "uuid"
import { clearHistory, sendMessage } from "@/api/client"
import type { Message } from "@/types"

const ERROR_MESSAGES: Record<string, string> = {
  "Failed to fetch":
    "Impossible de contacter le serveur. Verifiez que le serveur est bien demarre.",
  "API 401":
    "Votre session a expire. Veuillez recharger la page.",
  "TimeoutError":
    "La reponse a pris trop de temps (plus de 2 minutes). Essayez de reformuler.",
  "AbortError":
    "La reponse a pris trop de temps (plus de 2 minutes). Essayez de reformuler.",
}

function translateError(raw: string): string {
  for (const [key, msg] of Object.entries(ERROR_MESSAGES)) {
    if (raw.includes(key)) return msg
  }
  return raw
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const send = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return

    const userMsg: Message = { id: uuidv4(), role: "user", content: text }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)
    setError(null)

    try {
      const response = await sendMessage(text)
      const assistantMsg: Message = {
        id: uuidv4(),
        role: "assistant",
        content: response,
      }
      setMessages((prev) => [...prev, assistantMsg])
      return true
    } catch (err) {
      const raw = err instanceof Error ? err.message : "Erreur inconnue"
      setError(translateError(raw))
      return false
    } finally {
      setIsLoading(false)
    }
  }, [isLoading])

  const clear = useCallback(async () => {
    await clearHistory()
    setMessages([])
    setError(null)
  }, [])

  const dismissError = useCallback(() => {
    setError(null)
  }, [])

  return { messages, isLoading, error, send, clear, dismissError }
}
