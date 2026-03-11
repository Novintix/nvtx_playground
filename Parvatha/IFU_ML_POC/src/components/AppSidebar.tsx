import {
  Home,
  FileText,
  Type,
  FolderOpen,
  BarChart3,
  Settings,
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useLocation } from "react-router-dom";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

const items = [
  { title: "Home", url: "/", icon: Home },
  { title: "Doc Translation", url: "/doc-translation", icon: FileText },
  { title: "Text Translation", url: "/text-translation", icon: Type },
  { title: "Files", url: "/files", icon: FolderOpen },
  { title: "Statistics", url: "/statistics", icon: BarChart3 },
  { title: "Settings", url: "/settings", icon: Settings },
];

export function AppSidebar() {
  const location = useLocation();

  return (
    <Sidebar className="border-r border-sidebar-border">
      <div className="px-5 py-5">
        <h1 className="text-lg font-bold text-foreground tracking-tight">
          DocTranslate
        </h1>
      </div>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => {
                const isActive =
                  item.url === "/"
                    ? location.pathname === "/"
                    : location.pathname.startsWith(item.url);
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      className={
                        isActive
                          ? "bg-accent text-accent-foreground font-medium"
                          : "text-sidebar-foreground hover:bg-muted"
                      }
                    >
                      <NavLink
                        to={item.url}
                        end={item.url === "/"}
                        className=""
                        activeClassName=""
                      >
                        <item.icon className="mr-3 h-4 w-4" />
                        <span>{item.title}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
