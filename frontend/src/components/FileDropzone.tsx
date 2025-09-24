import React, { useCallback, useState } from 'react'
import { Upload, FileText, Archive } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import type { FileInfo } from '../types'

interface FileDropzoneProps {
  onFilesAdded: (files: FileInfo[]) => void
  acceptedTypes?: string[]
  maxFiles?: number
  disabled?: boolean
}

export function FileDropzone({ 
  onFilesAdded, 
  acceptedTypes = ['.docx', '.pdf', '.zip'], 
  maxFiles = 10,
  disabled = false 
}: FileDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateFile = useCallback((file: File): boolean => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!acceptedTypes.includes(extension)) {
      setError(`Tipo de archivo no soportado: ${extension}`)
      return false
    }
    
    if (file.size > 50 * 1024 * 1024) {
      setError(`El archivo ${file.name} es demasiado grande (máximo 50MB)`)
      return false
    }
    
    return true
  }, [acceptedTypes])

  const processFiles = useCallback((fileList: FileList) => {
    setError(null)
    const files = Array.from(fileList)
    
    if (files.length > maxFiles) {
      setError(`Máximo ${maxFiles} archivos permitidos`)
      return
    }
    
    const validFiles: FileInfo[] = []
    
    for (const file of files) {
      if (validateFile(file)) {
        validFiles.push({
          id: crypto.randomUUID(),
          name: file.name,
          size: file.size,
          type: file.type,
          file,
        })
      } else {
        return
      }
    }
    
    if (validFiles.length > 0) {
      onFilesAdded(validFiles)
    }
  }, [maxFiles, validateFile, onFilesAdded])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) {
      setIsDragOver(true)
    }
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    if (disabled) return
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      processFiles(files)
    }
  }, [disabled, processFiles])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      processFiles(files)
    }
    e.target.value = ''
  }, [processFiles])

  const getIcon = () => {
    const iconClass = cn(
      "w-16 h-16 transition-all duration-300",
      isDragOver ? "text-primary" : "text-muted-foreground group-hover:text-primary"
    )
    
    if (acceptedTypes.includes('.zip')) {
      return <Archive className={iconClass} />
    }
    return <FileText className={iconClass} />
  }

  return (
    <div className="w-full animate-fade-in">
      <div
        className={cn(
          "relative border-2 border-dashed rounded-3xl p-16 text-center transition-all duration-500 group overflow-hidden",
          "glass backdrop-blur-xl border-white/20 dark:border-white/10",
          "hover:border-primary/40 hover:shadow-elegant-hover hover:scale-[1.02] hover:backdrop-blur-2xl",
          isDragOver && "border-primary/60 shadow-elegant scale-[1.02] animate-pulse backdrop-blur-2xl",
          disabled && "opacity-50 cursor-not-allowed",
          !disabled && "cursor-pointer",
          error && "border-destructive/50 bg-destructive/5"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && document.getElementById('file-input')?.click()}
      >
        {/* Animated gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-blue-500/5 opacity-0 group-hover:opacity-100 transition-all duration-700"></div>
        
        {/* Enhanced floating particles */}
        <div className="absolute top-6 left-6 w-3 h-3 bg-gradient-to-r from-primary to-blue-500 rounded-full animate-bounce opacity-60" style={{ animationDelay: '0s' }}></div>
        <div className="absolute top-12 right-12 w-2 h-2 bg-gradient-to-r from-blue-500 to-primary rounded-full animate-bounce opacity-40" style={{ animationDelay: '0.7s' }}></div>
        <div className="absolute bottom-8 left-12 w-2.5 h-2.5 bg-gradient-to-r from-primary/60 to-blue-400/60 rounded-full animate-bounce opacity-50" style={{ animationDelay: '1.4s' }}></div>
        <div className="absolute bottom-16 right-8 w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce opacity-60" style={{ animationDelay: '2.1s' }}></div>
        
        <input
          id="file-input"
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileInput}
          className="hidden"
          disabled={disabled}
        />
        
        <div className="relative z-10 flex flex-col items-center space-y-8">
          <div className="relative">
            <div className={cn(
              "p-6 rounded-full transition-all duration-500 shadow-elegant",
              "bg-gradient-to-br from-white/80 to-white/40 dark:from-slate-800/80 dark:to-slate-700/40",
              "backdrop-blur-sm border border-white/20 dark:border-white/10",
              isDragOver ? "scale-110 shadow-elegant-hover bg-gradient-to-br from-primary/20 to-primary/10" : "group-hover:scale-105 group-hover:shadow-elegant-hover"
            )}>
              {getIcon()}
            </div>
            {isDragOver && (
              <div className="absolute inset-0 rounded-full border-2 border-primary/60 animate-ping"></div>
            )}
            <div className="absolute -inset-2 rounded-full bg-gradient-to-r from-primary/20 to-blue-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl"></div>
          </div>
          
          <div className="space-y-4 text-center">
            <p className={cn(
              "text-2xl font-semibold transition-all duration-500 bg-gradient-to-r bg-clip-text text-transparent",
              isDragOver ? "from-primary to-blue-500 scale-105" : "from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 group-hover:from-primary group-hover:to-blue-500"
            )}>
              {isDragOver ? '✨ Suelta los archivos aquí' : '📁 Arrastra archivos aquí o haz clic para seleccionar'}
            </p>
            <p className="text-base text-muted-foreground leading-relaxed max-w-lg mx-auto">
              Formatos soportados: <span className="font-semibold text-primary">{acceptedTypes.join(', ')}</span>
              <br />
              <span className="text-sm opacity-80">Máximo {maxFiles} archivos • 50MB cada uno</span>
            </p>
          </div>
          
          {!disabled && (
            <Button 
              variant="outline" 
              size="lg"
              className="mt-8 px-10 py-4 text-lg font-semibold transition-all duration-500 hover:scale-105 hover:shadow-elegant-hover glass border-primary/20 hover:border-primary/40 group/btn backdrop-blur-sm"
            >
              <Upload className="w-6 h-6 mr-3 transition-transform duration-500 group-hover/btn:scale-110 group-hover/btn:rotate-12" />
              Seleccionar archivos
            </Button>
          )}
        </div>
      </div>
      
      {error && (
        <Alert variant="destructive" className="mt-6 animate-slide-in border-destructive/50 bg-destructive/5">
          <AlertDescription className="text-destructive font-medium">{error}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}