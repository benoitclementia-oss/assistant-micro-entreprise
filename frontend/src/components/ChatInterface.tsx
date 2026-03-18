import { useEffect, useRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ChatInput } from "@/components/ChatInput"
import { ErrorBanner } from "@/components/ErrorBanner"
import { LoadingBubble } from "@/components/LoadingBubble"
import { MessageBubble } from "@/components/MessageBubble"
import type { Message } from "@/types"

interface Props {
  messages: Message[]
  isLoading: boolean
  error: string | null
  onSend: (message: string) => void
  onClear: () => void
  onMenuToggle?: () => void
  onDismissError?: () => void
}

export function ChatInterface({
  messages,
  isLoading,
  error,
  onSend,
  onClear,
  onMenuToggle,
  onDismissError,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 md:px-6 py-4 border-b bg-background">
        <div className="flex items-center gap-3">
          {/* Bouton hamburger — visible uniquement sur mobile */}
          {onMenuToggle && (
            <button
              onClick={onMenuToggle}
              className="lg:hidden text-muted-foreground hover:text-foreground p-1"
              aria-label="Menu"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="4" x2="20" y1="12" y2="12" />
                <line x1="4" x2="20" y1="6" y2="6" />
                <line x1="4" x2="20" y1="18" y2="18" />
              </svg>
            </button>
          )}
          <div>
            <h1 className="text-lg md:text-xl font-bold">Assistant Micro-Entreprise</h1>
            <p className="text-xs md:text-sm text-muted-foreground">
              Assistant juridique & administratif
            </p>
          </div>
        </div>
        <button
          onClick={onClear}
          className="text-xs md:text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Effacer
        </button>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 px-4 md:px-6 py-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            <p>Posez votre première question.</p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isLoading && <LoadingBubble />}

        {error && <ErrorBanner message={error} onDismiss={onDismissError} />}

        <div ref={bottomRef} />
      </ScrollArea>

      {/* Input */}
      <ChatInput onSend={onSend} disabled={isLoading} />
    </div>
  )
}
