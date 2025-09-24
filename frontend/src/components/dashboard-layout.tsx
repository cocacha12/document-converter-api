import React from 'react'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { ThemeToggle } from '@/components/ThemeToggle'

interface DashboardLayoutProps {
  children: React.ReactNode
  title?: string
  breadcrumbs?: Array<{ label: string; href?: string }>
}

export function DashboardLayout({ children, title = 'Fusionador de Documentos', breadcrumbs }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <header className="flex h-16 shrink-0 items-center gap-4 border-b px-6">
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </header>
      <main className="flex-1 p-6 md:p-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
          </div>
          {children}
        </div>
      </main>
    </div>
  )
}