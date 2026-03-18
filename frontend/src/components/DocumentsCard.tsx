import { useState } from "react"
import ReactMarkdown from "react-markdown"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { getDocumentContent } from "@/api/client"
import type { DocumentItem } from "@/types"

interface Props {
  documents: DocumentItem[]
}

export function DocumentsCard({ documents }: Props) {
  const [preview, setPreview] = useState<{ fichier: string; contenu: string } | null>(
    null
  )
  const [loading, setLoading] = useState(false)

  const handleOpen = async (fichier: string) => {
    setLoading(true)
    try {
      const data = await getDocumentContent(fichier)
      setPreview(data)
    } catch {
      // Silencieux
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Documents générés</CardTitle>
        </CardHeader>
        <CardContent>
          {documents.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">Aucun document.</p>
          ) : (
            <ul className="space-y-1">
              {documents.map((d) => (
                <li key={d.fichier}>
                  <button
                    onClick={() => void handleOpen(d.fichier)}
                    disabled={loading}
                    className="text-sm text-left w-full truncate hover:text-primary transition-colors"
                  >
                    {d.fichier}
                  </button>
                  <p className="text-xs text-muted-foreground">{d.date}</p>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Dialog open={preview !== null} onOpenChange={(open) => !open && setPreview(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{preview?.fichier}</DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-[60vh]">
            <div className="prose prose-sm dark:prose-invert max-w-none p-1">
              <ReactMarkdown>{preview?.contenu ?? ""}</ReactMarkdown>
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </>
  )
}
