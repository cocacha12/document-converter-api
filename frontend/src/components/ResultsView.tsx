import React from 'react'
import { Download, FileText, RefreshCw, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { JobStatus } from '../types'

interface ResultsViewProps {
  jobStatus: JobStatus
  onDownload: () => void
  onStartNew: () => void
  isDownloading?: boolean
}

export function ResultsView({ 
  jobStatus, 
  onDownload, 
  onStartNew, 
  isDownloading = false 
}: ResultsViewProps) {
  if (jobStatus.status !== 'completed') {
    return null
  }

  const { result } = jobStatus
  const isLoadingResult = !result

  return (
    <Card className="w-full max-w-2xl mx-auto animate-fadeIn glass shadow-elegant border-white/20 backdrop-blur-xl">
      <CardContent className="flex flex-col items-center space-y-10 p-12">
        {/* Success Icon */}
        <div className="relative flex items-center justify-center">
          <div className="absolute inset-0 bg-gradient-to-r from-green-400/30 to-emerald-500/20 rounded-full blur-2xl animate-pulse" />
          <div className="relative flex items-center justify-center w-24 h-24 bg-gradient-to-br from-green-400 to-emerald-600 rounded-full shadow-2xl animate-bounce">
            <CheckCircle className="w-14 h-14 text-white drop-shadow-lg" />
          </div>
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent rounded-full animate-pulse" />
        </div>

        {/* Success Message */}
        <div className="text-center space-y-6">
          <h3 className="text-3xl font-semibold bg-gradient-to-r from-green-500 to-emerald-600 bg-clip-text text-transparent">
            ¡Fusión completada!
          </h3>
          <p className="text-lg text-muted-foreground font-medium leading-relaxed max-w-sm">
            Tu documento ha sido procesado exitosamente
          </p>
        </div>

        {/* File Info */}
        <Card className="w-full bg-white/5 border border-white/10 backdrop-blur-sm shadow-modern hover:shadow-elegant transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-primary to-primary/80 shadow-modern backdrop-blur-sm">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1 min-w-0 space-y-1">
                {isLoadingResult ? (
                  <>
                    <div className="h-5 bg-muted animate-pulse rounded w-3/4"></div>
                    <div className="h-4 bg-muted animate-pulse rounded w-1/2"></div>
                  </>
                ) : (
                  <>
                    <p className="text-base font-semibold text-foreground truncate">
                      {result.filename}
                    </p>
                    <p className="text-sm text-muted-foreground font-medium">
                      Archivo fusionado listo para descargar
                    </p>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col w-full space-y-6">
          <Button
            onClick={onDownload}
            disabled={isDownloading || isLoadingResult}
            className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            {isLoadingResult ? (
              <>
                <RefreshCw className="w-6 h-6 mr-3 animate-spin" />
                Preparando descarga...
              </>
            ) : isDownloading ? (
              <>
                <RefreshCw className="w-6 h-6 mr-3 animate-spin" />
                Descargando...
              </>
            ) : (
              <>
                <Download className="w-6 h-6 mr-3" />
                Descargar archivo
              </>
            )}
          </Button>

          <Button
            variant="outline"
            onClick={onStartNew}
            className="w-full h-12 text-base font-semibold border border-white/20 bg-white/5 hover:bg-primary/10 hover:border-primary hover:text-primary transition-all duration-300 hover:scale-105 backdrop-blur-sm shadow-modern"
          >
            <RefreshCw className="w-5 h-5 mr-2" />
            Procesar nuevos archivos
          </Button>
        </div>

        {/* Job Details */}
        <div className="w-full pt-8 border-t border-white/10">
          <div className="text-center space-y-6">
            <div className="p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm shadow-modern">
              <div className="text-sm text-muted-foreground/80">
                ID del trabajo: <Badge variant="secondary" className="font-mono text-sm font-semibold ml-2 bg-white/10 border-white/20">{jobStatus.id}</Badge>
              </div>
            </div>
            <Badge className="bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold px-4 py-2 text-sm shadow-modern backdrop-blur-sm">
              ✓ Procesamiento completado al 100%
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}