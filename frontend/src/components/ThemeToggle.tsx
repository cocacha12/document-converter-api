import React from 'react'
import { Moon, Sun, Monitor } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { Button } from './ui/button'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const cycleTheme = () => {
    const themes = ['light', 'dark', 'system'] as const
    const currentIndex = themes.indexOf(theme)
    const nextIndex = (currentIndex + 1) % themes.length
    setTheme(themes[nextIndex])
  }

  const getIcon = () => {
    switch (theme) {
      case 'light':
        return <Sun className="h-4 w-4" />
      case 'dark':
        return <Moon className="h-4 w-4" />
      case 'system':
        return <Monitor className="h-4 w-4" />
    }
  }

  const getLabel = () => {
    switch (theme) {
      case 'light':
        return 'Modo claro'
      case 'dark':
        return 'Modo oscuro'
      case 'system':
        return 'Sistema'
    }
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={cycleTheme}
      className="relative overflow-hidden transition-all duration-300 hover:scale-105 hover:shadow-lg"
      title={`Cambiar tema (actual: ${getLabel()})`}
    >
      <div className="flex items-center space-x-2">
        <div className="transition-transform duration-300 hover:rotate-12">
          {getIcon()}
        </div>
        <span className="hidden sm:inline text-xs font-medium">
          {getLabel()}
        </span>
      </div>
    </Button>
  )
}