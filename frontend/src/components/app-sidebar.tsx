import * as React from "react"
import {
  FileText,
  Merge,
  Upload,
  Download,
  History,
  Settings,
  HelpCircle,
  FileIcon,
  FolderIcon,
  LayoutDashboardIcon,
} from "lucide-react"

import { NavDocuments } from "@/components/nav-documents"
import { NavMain } from "@/components/nav-main"
import { NavSecondary } from "@/components/nav-secondary"
import { NavUser } from "@/components/nav-user"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

const data = {
  user: {
    name: "Document Merger",
    email: "user@example.com",
    avatar: "/avatars/user.jpg",
  },
  navMain: [
    {
      title: "Dashboard",
      url: "#",
      icon: LayoutDashboardIcon,
    },
    {
      title: "Upload Files",
      url: "#",
      icon: Upload,
    },
    {
      title: "Merge Documents",
      url: "#",
      icon: Merge,
    },
    {
      title: "Downloads",
      url: "#",
      icon: Download,
    },
    {
      title: "History",
      url: "#",
      icon: History,
    },
  ],
  navSecondary: [
    {
      title: "Settings",
      url: "#",
      icon: Settings,
    },
    {
      title: "Help",
      url: "#",
      icon: HelpCircle,
    },
  ],
  documents: [
    {
      name: "PDF Files",
      url: "#",
      icon: FileText,
    },
    {
      name: "Word Documents",
      url: "#",
      icon: FileIcon,
    },
    {
      name: "Text Files",
      url: "#",
      icon: FolderIcon,
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:!p-1.5"
            >
              <a href="#">
                <Merge className="h-5 w-5" />
                <span className="text-base font-semibold">Document Merger</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavDocuments items={data.documents} />
        <NavSecondary items={data.navSecondary} className="mt-auto" />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
    </Sidebar>
  )
}
