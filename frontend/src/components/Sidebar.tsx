import { Separator } from "@/components/ui/separator"
import { DocumentsCard } from "@/components/DocumentsCard"
import { EcheancesCard } from "@/components/EcheancesCard"
import { ProfilCard } from "@/components/ProfilCard"
import type { SidebarData } from "@/types"

interface Props {
  data: SidebarData
  onNewConversation: () => void
  onRefresh: () => void
  onClose?: () => void
}

export function Sidebar({ data, onNewConversation, onRefresh, onClose }: Props) {
  return (
    <aside className="w-80 border-r bg-sidebar flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-4 py-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <span className="text-lg font-bold">&#x2696;&#xFE0F; Assistant Micro-Entreprise</span>
          {onClose && (
            <button
              onClick={onClose}
              className="lg:hidden text-muted-foreground hover:text-foreground p-1"
              aria-label="Fermer le menu"
            >
              &#x2715;
            </button>
          )}
        </div>
        <button
          onClick={onNewConversation}
          className="w-full text-sm bg-primary text-primary-foreground rounded-lg px-3 py-2 hover:bg-primary/90 transition-colors"
        >
          + Nouvelle conversation
        </button>
      </div>

      {/* Cards scrollables */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <ProfilCard profil={data.profil} />
        <Separator />
        <EcheancesCard echeances={data.echeances} onRefresh={onRefresh} />
        <Separator />
        <DocumentsCard documents={data.documents} />
      </div>
    </aside>
  )
}
