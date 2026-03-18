import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { updateProfil } from "@/api/client"

interface Props {
  onComplete: () => void
}

type Step = 1 | 2 | 3

export function WelcomeScreen({ onComplete }: Props) {
  const [step, setStep] = useState<Step>(1)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    prenom: "",
    nom: "",
    nom_entreprise: "",
    siret: "",
    adresse: "",
    code_postal: "",
    ville: "",
    activite: "",
    regime_fiscal: "",
    email: "",
    telephone: "",
  })

  const update = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const fields: Record<string, string> = {}
      for (const [k, v] of Object.entries(form)) {
        if (v.trim()) fields[k] = v.trim()
      }
      if (Object.keys(fields).length > 0) {
        await updateProfil(fields)
      }
      onComplete()
    } catch {
      onComplete()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center h-screen bg-background px-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <div className="text-4xl mb-2">&#x2696;&#xFE0F;</div>
          <CardTitle className="text-xl">
            Bienvenue sur Assistant Micro-Entreprise
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Configurons votre profil en quelques secondes
          </p>
          {/* Indicateur d'étape */}
          <div className="flex justify-center gap-2 mt-4">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-2 w-12 rounded-full transition-colors ${
                  s <= step ? "bg-primary" : "bg-muted"
                }`}
              />
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="font-medium">Qui etes-vous ?</h3>
              <div className="grid grid-cols-2 gap-3">
                <Input
                  placeholder="Prenom"
                  value={form.prenom}
                  onChange={(e) => update("prenom", e.target.value)}
                  autoFocus
                />
                <Input
                  placeholder="Nom"
                  value={form.nom}
                  onChange={(e) => update("nom", e.target.value)}
                />
              </div>
              <Input
                placeholder="Email"
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
              />
              <Input
                placeholder="Telephone"
                value={form.telephone}
                onChange={(e) => update("telephone", e.target.value)}
              />
              <Button className="w-full" onClick={() => setStep(2)}>
                Suivant
              </Button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h3 className="font-medium">Votre entreprise</h3>
              <Input
                placeholder="Nom de l'entreprise"
                value={form.nom_entreprise}
                onChange={(e) => update("nom_entreprise", e.target.value)}
                autoFocus
              />
              <Input
                placeholder="SIRET (14 chiffres)"
                value={form.siret}
                onChange={(e) => update("siret", e.target.value)}
              />
              <Input
                placeholder="Activite (ex: Developpement web)"
                value={form.activite}
                onChange={(e) => update("activite", e.target.value)}
              />
              <Input
                placeholder="Regime fiscal (ex: micro-BNC, micro-BIC)"
                value={form.regime_fiscal}
                onChange={(e) => update("regime_fiscal", e.target.value)}
              />
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(1)}>
                  Retour
                </Button>
                <Button className="flex-1" onClick={() => setStep(3)}>
                  Suivant
                </Button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h3 className="font-medium">Adresse professionnelle</h3>
              <Input
                placeholder="Adresse"
                value={form.adresse}
                onChange={(e) => update("adresse", e.target.value)}
                autoFocus
              />
              <div className="grid grid-cols-2 gap-3">
                <Input
                  placeholder="Code postal"
                  value={form.code_postal}
                  onChange={(e) => update("code_postal", e.target.value)}
                />
                <Input
                  placeholder="Ville"
                  value={form.ville}
                  onChange={(e) => update("ville", e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(2)}>
                  Retour
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleSubmit}
                  disabled={loading}
                >
                  {loading ? "Enregistrement..." : "Terminer"}
                </Button>
              </div>
            </div>
          )}

          {step === 1 && (
            <button
              onClick={onComplete}
              className="w-full text-center text-sm text-muted-foreground mt-4 hover:underline"
            >
              Passer cette etape
            </button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
