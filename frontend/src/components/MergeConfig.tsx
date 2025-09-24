import React from 'react'
import { FileText, File, BookOpen, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { MergeConfigType } from '../types'

interface MergeConfigProps {
  config: MergeConfigType
  onConfigChange: (config: MergeConfigType) => void
  onStartProcessing: () => void
  disabled?: boolean
}

export function MergeConfig({ config, onConfigChange, onStartProcessing, disabled = false }: MergeConfigProps) {
  const handleOutputFormatChange = (format: MergeConfigType['outputFormat']) => {
    onConfigChange({ ...config, outputFormat: format })
  }

  const handleToggleTOC = () => {
    onConfigChange({ ...config, includeTableOfContents: !config.includeTableOfContents })
  }

  const handleToggleSeparateByTitle = () => {
    onConfigChange({ ...config, separateByTitle: !config.separateByTitle })
  }

  const handleCustomTitleChange = (title: string) => {
    onConfigChange({ ...config, customTitle: title })
  }

  const formatOptions = [
    {
      value: 'markdown' as const,
      label: 'Markdown',
      icon: <FileText className="w-4 h-4" />,
      description: 'Formato de texto plano con marcado'
    },
    {
      value: 'docx' as const,
      label: 'Word (DOCX)',
      icon: <File className="w-4 h-4" />,
      description: 'Documento de Microsoft Word'
    },
    {
      value: 'pdf' as const,
      label: 'PDF',
      icon: <BookOpen className="w-4 h-4" />,
      description: 'Documento PDF'
    }
  ]

  return (
    <div className="w-full space-y-6 glass shadow-elegant border-white/20 backdrop-blur-xl">
      <h3 className="text-lg font-medium text-foreground mb-4 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-primary/10 text-primary">
          <Settings className="h-5 w-5" />
        </div>
        Configuración de fusión
      </h3>

      <div className="space-y-8 px-6 pb-6">
        {/* Output Format */}
        <div className="space-y-4">
          <Label className="text-base font-semibold text-foreground">
            Formato de salida
          </Label>
          <div className="grid grid-cols-3 gap-4 mt-3">
            {formatOptions.map((option) => (
              <div key={option.value} className="flex items-center space-x-3 p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition-all duration-300">
                <Button
                  type="button"
                  variant={config.outputFormat === option.value ? "default" : "outline"}
                  onClick={() => handleOutputFormatChange(option.value)}
                  disabled={disabled}
                  className="flex items-center gap-2 h-10 font-medium"
                >
                  <span className="text-primary">{option.icon}</span>
                  <span className="text-sm">{option.label}</span>
                </Button>
              </div>
            ))}
          </div>
        </div>

        {/* Custom Title */}
        <div className="space-y-3">
          <Label htmlFor="custom-title" className="text-base font-semibold text-foreground">
            Título personalizado <span className="text-muted-foreground">(opcional)</span>
          </Label>
          <Input
            id="custom-title"
            type="text"
            value={config.customTitle || ''}
            onChange={(e) => handleCustomTitleChange(e.target.value)}
            placeholder="Ingresa un título para el documento fusionado"
            disabled={disabled}
            className="h-12 px-4 bg-white/5 border-white/10 rounded-xl backdrop-blur-sm focus:bg-white/10 transition-all duration-300"
          />
        </div>

        {/* Options */}
        <div className="space-y-4">
          <Label className="text-base font-semibold text-foreground">
            Opciones adicionales
          </Label>
          
          <div className="space-y-4 mt-3">
            <div className="flex items-start space-x-3 p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition-all duration-300">
              <input
                type="checkbox"
                checked={config.includeTableOfContents}
                onChange={handleToggleTOC}
                disabled={disabled}
                className="h-4 w-4 mt-0.5"
              />
              <Label className="cursor-pointer leading-relaxed font-medium">
                <span className="text-sm font-medium text-foreground">
                  Incluir tabla de contenidos
                </span>
                <p className="text-xs text-muted-foreground">
                  Genera automáticamente una tabla de contenidos al inicio del documento
                </p>
              </Label>
            </div>

            <div className="flex items-start space-x-3 p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition-all duration-300">
              <input
                type="checkbox"
                checked={config.separateByTitle}
                onChange={handleToggleSeparateByTitle}
                disabled={disabled}
                className="h-4 w-4 mt-0.5"
              />
              <Label className="cursor-pointer leading-relaxed font-medium">
                <span className="text-sm font-medium text-foreground">
                  Separar por títulos extraídos
                </span>
                <p className="text-xs text-muted-foreground">
                  Usa los títulos extraídos de los documentos como separadores
                </p>
              </Label>
            </div>
          </div>
        </div>

        {/* Convert Button */}
        <div className="pt-4 border-t border-white/10">
          <Button
            onClick={onStartProcessing}
            disabled={disabled}
            className="w-full h-12 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-[1.02]"
          >
            <FileText className="w-5 h-5 mr-2" />
            Convertir y fusionar documentos
          </Button>
        </div>
      </div>
    </div>
  )
}