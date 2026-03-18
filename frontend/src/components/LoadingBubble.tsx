export function LoadingBubble() {
  return (
    <div className="flex items-start gap-2 mb-4">
      <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3 max-w-[80%]">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.3s]" />
            <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.15s]" />
            <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
          </div>
          <span className="text-sm text-muted-foreground">Recherche en cours...</span>
        </div>
      </div>
    </div>
  )
}
