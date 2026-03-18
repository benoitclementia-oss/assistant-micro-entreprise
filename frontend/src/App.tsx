import { useCallback, useEffect, useMemo, useState } from "react"
import { ChatInterface } from "@/components/ChatInterface"
import { Sidebar } from "@/components/Sidebar"
import { LoginPage } from "@/components/LoginPage"
import { WelcomeScreen } from "@/components/WelcomeScreen"
import { useChat } from "@/hooks/useChat"
import { useSidebar } from "@/hooks/useSidebar"
import { checkAuth } from "@/api/client"

type AuthState = "loading" | "login" | "authenticated"

export default function App() {
  const [authState, setAuthState] = useState<AuthState>("loading")
  const [onboardingDone, setOnboardingDone] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { messages, isLoading, error, send, clear, dismissError } = useChat()
  const sidebar = useSidebar()

  // Verification auth au demarrage
  useEffect(() => {
    checkAuth().then((authenticated) => {
      setAuthState(authenticated ? "authenticated" : "login")
    })
  }, [])

  // Determiner si on doit montrer l'onboarding
  const showOnboarding = useMemo(() => {
    return (
      authState === "authenticated" &&
      !onboardingDone &&
      sidebar.profilVide &&
      !sidebar.isLoading
    )
  }, [authState, onboardingDone, sidebar.profilVide, sidebar.isLoading])

  const handleLogin = useCallback(() => {
    setAuthState("authenticated")
    void sidebar.refresh()
  }, [sidebar])

  const handleOnboardingComplete = useCallback(() => {
    setOnboardingDone(true)
    void sidebar.refresh()
  }, [sidebar])

  const handleSend = useCallback(
    async (message: string) => {
      setSidebarOpen(false)
      const ok = await send(message)
      if (ok !== false) {
        void sidebar.refresh()
      }
    },
    [send, sidebar]
  )

  const handleClear = useCallback(async () => {
    await clear()
  }, [clear])

  const handleNewConversation = useCallback(async () => {
    await clear()
    void sidebar.refresh()
    setSidebarOpen(false)
  }, [clear, sidebar])

  if (authState === "loading") {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <p className="text-muted-foreground">Chargement...</p>
      </div>
    )
  }

  if (authState === "login") {
    return <LoginPage onLogin={handleLogin} />
  }

  if (showOnboarding) {
    return <WelcomeScreen onComplete={handleOnboardingComplete} />
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Overlay mobile pour fermer la sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar : cachee sur mobile, visible sur desktop */}
      <div
        className={`
          fixed inset-y-0 left-0 z-40 w-80
          transform transition-transform duration-200 ease-in-out
          lg:relative lg:translate-x-0
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <Sidebar
          data={sidebar.data}
          onNewConversation={() => void handleNewConversation()}
          onRefresh={sidebar.refresh}
          onClose={() => setSidebarOpen(false)}
        />
      </div>

      <main className="flex-1 overflow-hidden">
        <ChatInterface
          messages={messages}
          isLoading={isLoading}
          error={error}
          onSend={(msg) => void handleSend(msg)}
          onClear={() => void handleClear()}
          onMenuToggle={() => setSidebarOpen((prev) => !prev)}
          onDismissError={dismissError}
        />
      </main>
    </div>
  )
}
