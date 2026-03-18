export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
}

export interface ChatState {
  messages: Message[]
  isLoading: boolean
  error: string | null
}

export interface ProfilData {
  nom: string
  prenom: string
  nom_entreprise: string
  siret: string
  adresse: string
  code_postal: string
  ville: string
  email: string
  telephone: string
  activite: string
  regime_fiscal: string
  regime_social: string
  date_creation_entreprise: string
}

export interface EcheanceItem {
  id: number
  titre: string
  date: string
  description: string
  type: string
  fait: boolean
}

export interface DocumentItem {
  fichier: string
  taille: number
  date: string
}

export interface SidebarData {
  profil: ProfilData
  echeances: EcheanceItem[]
  documents: DocumentItem[]
}
