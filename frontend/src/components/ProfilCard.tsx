import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { ProfilData } from "@/types"

interface Props {
  profil: ProfilData
}

export function ProfilCard({ profil }: Props) {
  const nom = profil.nom_entreprise || [profil.prenom, profil.nom].filter(Boolean).join(" ")
  const ville = [profil.code_postal, profil.ville].filter(Boolean).join(" ")

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">Profil</CardTitle>
      </CardHeader>
      <CardContent className="text-sm space-y-1">
        {nom ? (
          <p className="font-medium truncate">{nom}</p>
        ) : (
          <p className="text-muted-foreground italic">Profil non configuré</p>
        )}
        {profil.siret && (
          <p className="text-muted-foreground text-xs">SIRET : {profil.siret}</p>
        )}
        {profil.activite && (
          <p className="text-muted-foreground text-xs truncate">{profil.activite}</p>
        )}
        {ville && (
          <p className="text-muted-foreground text-xs">{ville}</p>
        )}
        {!nom && (
          <p className="text-xs text-muted-foreground mt-1">
            Complétez votre profil via le chat.
          </p>
        )}
      </CardContent>
    </Card>
  )
}
