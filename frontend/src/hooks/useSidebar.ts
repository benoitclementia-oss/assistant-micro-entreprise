import { useCallback, useEffect, useState } from "react"
import { getSidebarData } from "@/api/client"
import type { ProfilData, SidebarData } from "@/types"

const EMPTY: SidebarData = {
  profil: {
    nom: "",
    prenom: "",
    nom_entreprise: "",
    siret: "",
    adresse: "",
    code_postal: "",
    ville: "",
    email: "",
    telephone: "",
    activite: "",
    regime_fiscal: "",
    regime_social: "",
    date_creation_entreprise: "",
  },
  echeances: [],
  documents: [],
}

function isProfilEmpty(profil: ProfilData): boolean {
  const filled = Object.values(profil).filter((v) => v && v.trim() !== "")
  return filled.length < 2
}

export function useSidebar() {
  const [data, setData] = useState<SidebarData>(EMPTY)
  const [isLoading, setIsLoading] = useState(false)
  const [profilVide, setProfilVide] = useState(false)

  const refresh = useCallback(async () => {
    setIsLoading(true)
    try {
      const result = await getSidebarData()
      setData(result)
      setProfilVide(isProfilEmpty(result.profil))
    } catch {
      // Silencieux — sidebar non critique
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { data, isLoading, profilVide, refresh }
}
