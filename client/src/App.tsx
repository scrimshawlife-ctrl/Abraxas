import { useState } from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppSidebar } from "@/components/app-sidebar";
import { Moon, Sun } from "lucide-react";

// Import all the mystical components
import RitualRunner from "@/components/RitualRunner";
import VCOracle from "@/components/VCOracle";
import SocialTrendsPanel from "@/components/SocialTrendsPanel";
import SigilGenerator from "@/components/SigilGenerator";
import MetricsPanel from "@/components/MetricsPanel";
import GrimoireView from "@/components/GrimoireView";
import Config from "@/components/Config";

function App() {
  const [currentPath, setCurrentPath] = useState("/ritual");
  const [darkMode, setDarkMode] = useState(true);

  // Custom sidebar width for mystical application
  const style = {
    "--sidebar-width": "22rem",       
    "--sidebar-width-icon": "4rem",   
  };

  const toggleTheme = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle("dark");
    console.log('Theme toggled:', !darkMode ? 'dark' : 'light');
  };

  const renderCurrentView = () => {
    switch (currentPath) {
      case "/ritual":
        return <RitualRunner />;
      case "/vc-oracle":
        return <VCOracle />;
      case "/social-trends":
        return <SocialTrendsPanel />;
      case "/sigil-forge":
        return <SigilGenerator />;
      case "/metrics":
        return <MetricsPanel />;
      case "/grimoire":
        return <GrimoireView />;
      case "/config":
        return <Config />;
      default:
        return <RitualRunner />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <SidebarProvider style={style as React.CSSProperties}>
          <div className="flex h-screen w-full">
            <AppSidebar 
              currentPath={currentPath} 
              onNavigate={setCurrentPath} 
            />
            
            <div className="flex flex-col flex-1">
              <header className="flex items-center justify-between p-4 border-b bg-background/80 backdrop-blur-sm">
                <div className="flex items-center gap-4">
                  <SidebarTrigger data-testid="button-sidebar-toggle" />
                  <div className="text-lg font-bold text-primary">
                    ⟟ ABRAXAS ⟟
                  </div>
                </div>
                
                <Button 
                  onClick={toggleTheme}
                  size="icon"
                  variant="ghost"
                  data-testid="button-theme-toggle"
                >
                  {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </Button>
              </header>
              
              <main className="flex-1 overflow-auto p-6 bg-background">
                <div className="max-w-6xl mx-auto">
                  {renderCurrentView()}
                </div>
              </main>
              
              <footer className="p-4 text-center text-xs text-muted-foreground border-t bg-background/80 backdrop-blur-sm">
                ⟟Σ ABRAXAS • Mystical Trading Oracle • Sources & methods sealed • Not financial advice Σ⟟
              </footer>
            </div>
          </div>
        </SidebarProvider>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;