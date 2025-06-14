import { useState } from "react"
import { ThemeProvider } from "@/components/theme-provider";
import PdfUploader from "@/components/PdfUploader";
import Documents from "@/components/documents";
import { AppSidebar } from "@/components/app-sidebar";
import {
  SidebarProvider,
  SidebarInset,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Toaster } from "@/components/ui/sonner"

export default function App() {
  const [activeView, setActiveView] = useState("upload")

  return (
    <>
      <Toaster position="bottom-center" richColors />
      <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
        <SidebarProvider>
          <AppSidebar onNavigate={setActiveView} />
          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center gap-2">
              <div className="flex items-center gap-2 px-4">
                <SidebarTrigger className="-ml-1" />
              </div>
            </header>
            {/* Компонент загрузки документов */}
            {activeView === "upload" && <PdfUploader setActiveView={setActiveView} />}
            {activeView === "documents" && <Documents />}
          </SidebarInset>
        </SidebarProvider>
      </ThemeProvider>
    </>
  )
}