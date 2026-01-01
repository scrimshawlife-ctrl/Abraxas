import { 
  Sidebar, 
  SidebarContent, 
  SidebarGroup, 
  SidebarGroupContent, 
  SidebarGroupLabel, 
  SidebarMenu, 
  SidebarMenuButton, 
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { SimpleTooltip } from "@/components/ui/tooltip";
import {
  PlayCircle,
  Eye,
  Wand2,
  Hash,
  Activity,
  History,
  Sparkles,
  Settings,
  TrendingUp,
  Palette,
  LayoutDashboard
} from "lucide-react";

const menuItems = [
  {
    title: "Dashboard Lens",
    url: "/dashboard",
    icon: LayoutDashboard,
    description: "Browse + diff + audit artifacts"
  },
  {
    title: "Ritual Chamber",
    url: "/ritual",
    icon: PlayCircle,
    description: "Run mystical market rituals"
  },
  {
    title: "VC Oracle",
    url: "/vc-oracle", 
    icon: Eye,
    description: "Divine venture capital patterns"
  },
  {
    title: "Social Oracle",
    url: "/social-trends",
    icon: Hash,
    description: "Monitor digital zeitgeist"
  },
  {
    title: "Sigil Forge",
    url: "/sigil-forge",
    icon: Wand2,
    description: "Transform intentions into symbols"
  },
  {
    title: "System Metrics", 
    url: "/metrics",
    icon: Activity,
    description: "Abraxas performance data"
  },
  {
    title: "Grimoire",
    url: "/grimoire",
    icon: History,
    description: "Historical ritual records"
  },
  {
    title: "Market Watchlist",
    url: "/watchlist",
    icon: TrendingUp,
    description: "Dynamic equity & FX analysis"
  },
  {
    title: "Config",
    url: "/config",
    icon: Settings,
    description: "Tune mystical algorithm weights"
  },
  {
    title: "AAL Demo",
    url: "/aal-demo",
    icon: Palette,
    description: "Design system showcase"
  }
];

interface AppSidebarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
}

export function AppSidebar({ currentPath, onNavigate }: AppSidebarProps) {
  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="flex items-center gap-2 text-primary">
            <Sparkles className="w-4 h-4" />
            ABRAXAS
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton
                    onClick={() => onNavigate(item.url)}
                    className={currentPath === item.url ? 'bg-sidebar-accent' : ''}
                    data-testid={`nav-${item.title.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    <item.icon className="w-4 h-4" />
                    <div>
                      <div className="font-medium">{item.title}</div>
                      <div className="text-xs text-muted-foreground">{item.description}</div>
                    </div>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}