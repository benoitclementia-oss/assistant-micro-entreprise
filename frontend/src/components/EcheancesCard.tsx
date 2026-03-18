import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { marquerEcheanceFaite } from "@/api/client"
import type { EcheanceItem } from "@/types"

interface Props {
  echeances: EcheanceItem[]
  onRefresh: () => void
}

const TYPE_COLORS: Record<string, string> = {
  fiscal: "bg-amber-100 text-amber-800",
  social: "bg-blue-100 text-blue-800",
  custom: "bg-gray-100 text-gray-800",
}

export function EcheancesCard({ echeances, onRefresh }: Props) {
  const handleMark = async (id: number) => {
    try {
      await marquerEcheanceFaite(id)
      onRefresh()
    } catch {
      // Silencieux
    }
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">
          Échéances (30 jours)
        </CardTitle>
      </CardHeader>
      <CardContent>
        {echeances.length === 0 ? (
          <p className="text-sm text-muted-foreground italic">
            Aucune échéance à venir.
          </p>
        ) : (
          <ul className="space-y-2">
            {echeances.map((e) => (
              <li key={e.id} className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={e.fait}
                  disabled={e.fait}
                  onChange={() => void handleMark(e.id)}
                  className="mt-0.5 cursor-pointer"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span
                      className={`text-xs font-medium truncate ${e.fait ? "line-through text-muted-foreground" : ""}`}
                    >
                      {e.titre}
                    </span>
                    <Badge
                      variant="outline"
                      className={`text-xs px-1 py-0 ${TYPE_COLORS[e.type] ?? TYPE_COLORS.custom}`}
                    >
                      {e.type}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{e.date}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
