import React from 'react'
import { Loader2, CheckCircle, XCircle, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import type { JobStatus } from '../types'

interface ProcessingViewProps {
  jobStatus: JobStatus
  onCancel?: () => void
}

export function ProcessingView({ jobStatus, onCancel }: ProcessingViewProps) {
  const getStatusIcon = () => {
    const iconClass = "w-12 h-12 transition-all duration-500"
    
    switch (jobStatus.status) {
      case 'pending':
        return <Clock className={cn(iconClass, "text-yellow-500 animate-pulse")} />
      case 'processing':
        return <Loader2 className={cn(iconClass, "text-primary animate-spin")} />
      case 'completed':
        return <CheckCircle className={cn(iconClass, "text-green-500 animate-bounce")} />
      case 'failed':
        return <XCircle className={cn(iconClass, "text-destructive animate-pulse")} />
      default:
        return <Clock className={cn(iconClass, "text-muted-foreground")} />
    }
  }

  const getStatusText = () => {
    switch (jobStatus.status) {
      case 'pending':
        return 'Preparando procesamiento...'
      case 'processing':
        return 'Procesando documentos...'
      case 'completed':
        return '¡Procesamiento completado!'
      case 'failed':
        return 'Error en el procesamiento'
      default:
        return 'Estado desconocido'
    }
  }

  const getStatusColor = () => {
    switch (jobStatus.status) {
      case 'pending':
        return 'text-yellow-600'
      case 'processing':
        return 'text-primary'
      case 'completed':
        return 'text-green-600'
      case 'failed':
        return 'text-destructive'
      default:
        return 'text-muted-foreground'
    }
  }

  const getProgressBarColor = () => {
    switch (jobStatus.status) {
      case 'pending':
        return 'from-yellow-400 to-yellow-600'
      case 'processing':
        return 'from-primary to-primary/80'
      case 'completed':
        return 'from-green-400 to-green-600'
      case 'failed':
        return 'from-destructive to-destructive/80'
      default:
        return 'from-muted-foreground to-muted-foreground/80'
    }
  }

  return (
    <Card className="w-full max-w-2xl mx-auto animate-fadeIn glass shadow-elegant border-white/20 backdrop-blur-xl">
      <CardContent className="flex flex-col items-center space-y-10 p-12">
        {/* Status Icon */}
        <div className="relative flex items-center justify-center">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-primary/10 rounded-full blur-xl animate-pulse" />
          <div className="relative p-8 rounded-2xl glass shadow-elegant border-white/20 backdrop-blur-xl">
            {getStatusIcon()}
          </div>
        </div>

        {/* Status Text */}
        <div className="text-center space-y-4">
          <h3 className={cn("text-2xl font-semibold bg-gradient-to-r bg-clip-text text-transparent", 
            jobStatus.status === 'pending' ? 'from-yellow-500 to-yellow-600' :
            jobStatus.status === 'processing' ? 'from-primary to-primary/70' :
            jobStatus.status === 'completed' ? 'from-green-500 to-green-600' :
            jobStatus.status === 'failed' ? 'from-destructive to-destructive/70' :
            'from-muted-foreground to-muted-foreground/70'
          )}>
            {getStatusText()}
          </h3>
          {jobStatus.message && (
            <p className="text-base text-muted-foreground font-medium leading-relaxed max-w-sm">
              {jobStatus.message}
            </p>
          )}
        </div>

        {/* Progress Bar */}
        <div className="w-full space-y-6">
          <div className="flex justify-between items-center">
            <span className="text-base font-semibold text-foreground">Progreso</span>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-lg font-semibold text-primary">{Math.round(jobStatus.progress)}%</span>
            </div>
          </div>
          <div className="relative">
            <div className="h-3 bg-muted rounded-full overflow-hidden shadow-inner">
              <div 
                className={cn(
                  "h-full bg-gradient-to-r transition-all duration-500 ease-out relative overflow-hidden",
                  getProgressBarColor()
                )}
                style={{ width: `${Math.min(100, Math.max(0, jobStatus.progress))}%` }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
              </div>
            </div>
          </div>
        </div>

        {/* Job ID */}
        <div className="text-center p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm shadow-modern">
          <p className="text-sm text-muted-foreground/80">
            ID del trabajo: <span className="font-mono text-primary font-semibold">{jobStatus.id}</span>
          </p>
        </div>

        {/* Error Message */}
        {jobStatus.status === 'failed' && jobStatus.error && (
          <Alert variant="destructive" className="w-full animate-slideIn border border-destructive/30 bg-destructive/5 backdrop-blur-sm rounded-xl shadow-modern">
            <XCircle className="h-5 w-5" />
            <AlertDescription className="text-base font-medium">
              <strong>Error:</strong> {jobStatus.error}
            </AlertDescription>
          </Alert>
        )}

        {/* Cancel Button */}
        {(jobStatus.status === 'pending' || jobStatus.status === 'processing') && onCancel && (
          <Button
            variant="outline"
            onClick={onCancel}
            className="px-10 py-4 text-base font-semibold border border-white/20 bg-white/5 hover:bg-destructive/10 hover:border-destructive hover:text-destructive transition-all duration-300 hover:scale-105 mt-4 backdrop-blur-sm shadow-modern"
          >
            Cancelar
          </Button>
        )}
      </CardContent>
    </Card>
  )
}