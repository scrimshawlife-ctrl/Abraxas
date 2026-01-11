import { useState } from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider, SimpleTooltip } from "@/components/ui/tooltip";
import { AppSidebar } from "@/components/app-sidebar";
import { Moon, Sun, LogOut } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import Landing from "@/pages/Landing";

// Import all the mystical components
import RitualRunner from "@/components/RitualRunner";
import VCOracle from "@/components/VCOracle";
import SocialTrendsPanel from "@/components/SocialTrendsPanel";
import SigilGenerator from "@/components/SigilGenerator";
import MetricsPanel from "@/components/MetricsPanel";
import GrimoireView from "@/components/GrimoireView";
import Config from "@/components/Config";
import DynamicWatchlist from "@/components/DynamicWatchlist";
import AalDemo from "@/pages/AalDemo";
import DashboardLens from "@/components/DashboardLens";
import ArtifactsDashboard from "@/components/dashboard/ArtifactsDashboard";
import DashboardLens from "@/components/DashboardLens";
import AdminTrainingPanel from "@/components/AdminTrainingPanel";

function AuthenticatedApp() {
  const [currentPath, setCurrentPath] = useState("/ritual");
  const [darkMode, setDarkMode] = useState(true);
  const { user } = useAuth();

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
      case "/dashboard":
        return <DashboardLens />;
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
      case "/watchlist":
        return <DynamicWatchlist />;
      case "/config":
        return <Config />;
      case "/aal-demo":
        return <AalDemo />;
      case "/artifacts":
        return <ArtifactsDashboard />;
      case "/training-admin":
        return <AdminTrainingPanel />;
      default:
        return <RitualRunner />;
    }
  };

  return (
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
                  <SimpleTooltip content="Toggle navigation sidebar" side="bottom">
                    <SidebarTrigger data-testid="button-sidebar-toggle" />
                  </SimpleTooltip>
                  <SimpleTooltip content="Abraxas Mystical Trading Oracle - Sources & methods sealed" side="bottom">
                    <div className="text-lg font-bold text-primary cursor-help">
                      ⟟ ABRAXAS ⟟
                    </div>
                  </SimpleTooltip>
                </div>
                
                <div className="flex items-center gap-2">
                  {user && (
                    <div className="flex items-center gap-2 mr-4">
                      {user.profileImageUrl && (
                        <img 
                          src={user.profileImageUrl} 
                          alt="Profile" 
                          className="w-6 h-6 rounded-full object-cover"
                        />
                      )}
                      <span className="text-sm text-muted-foreground">
                        {user.firstName || user.email}
                      </span>
                      <SimpleTooltip content="Logout" side="bottom">
                        <Button 
                          onClick={() => window.location.href = '/api/logout'}
                          size="icon"
                          variant="ghost"
                          data-testid="button-logout"
                        >
                          <LogOut className="w-4 h-4" />
                        </Button>
                      </SimpleTooltip>
                    </div>
                  )}
                  
                  <SimpleTooltip content={`Switch to ${darkMode ? 'light' : 'dark'} mode`} side="bottom">
                    <Button 
                      onClick={toggleTheme}
                      size="icon"
                      variant="ghost"
                      data-testid="button-theme-toggle"
                    >
                      {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                    </Button>
                  </SimpleTooltip>
                </div>
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
    );
  
}

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-lg font-semibold">Loading...</div>
          <div className="text-sm text-muted-foreground">Connecting to the Oracle</div>
        </div>
      </div>
    );
  }

  return isAuthenticated ? <AuthenticatedApp /> : <Landing />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
