import React, { useState, useEffect, useCallback } from 'react'
import { FileText, Merge } from 'lucide-react'
import { DashboardLayout } from './components/dashboard-layout'
import { FileDropzone } from './components/FileDropzone'
import { FileList } from './components/FileList'
import { MergeConfig } from './components/MergeConfig'
import { ProcessingView } from './components/ProcessingView'
import { ResultsView } from './components/ResultsView'
import { ApiService } from './services/api'
import type { FileInfo, MergeConfigType, JobStatus, WebSocketMessage } from './types'

type AppState = 'upload' | 'processing' | 'completed'

function App() {
  const [state, setState] = useState<AppState>('upload')
  const [files, setFiles] = useState<FileInfo[]>([])
  const [config, setConfig] = useState<MergeConfigType>({
    outputFormat: 'markdown',
    includeTableOfContents: true,
    separateByTitle: true,
  })
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)
  const [websocket, setWebsocket] = useState<WebSocket | null>(null)

  // WebSocket connection management
  const connectWebSocket = useCallback((jobId: string) => {
    const ws = ApiService.createWebSocket(jobId)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
    }
    
    ws.onmessage = (event) => {
      try {
        console.log('🔵 WebSocket raw message received:', event.data)
        const message: WebSocketMessage = JSON.parse(event.data)
        console.log('🔵 WebSocket parsed message:', message)
        
        if (message.type === 'progress') {
          console.log('📊 Processing progress message:', {
            progress: message.progress,
            message: message.message,
            currentJobStatus: jobStatus
          })
          setJobStatus(prev => {
            const updated = prev ? {
              ...prev,
              progress: message.progress || 0,
              message: message.message
            } : null
            console.log('📊 Updated job status:', updated)
            return updated
          })
        } else if (message.type === 'status_update') {
          console.log('🔄 Processing status update message:', {
            status: message.status,
            progress: message.progress,
            message: message.message,
            currentJobStatus: jobStatus
          })
          setJobStatus(prev => {
            const updated = prev ? {
              ...prev,
              status: message.status,
              progress: message.progress || 0,
              message: message.message
            } : null
            console.log('🔄 Updated job status from status_update:', updated)
            return updated
          })
          
          // If status is completed, use the result from WebSocket message
          if (message.status === 'completed') {
            console.log('✅ Job completed, using result from WebSocket:', message.result)
            console.log('🔍 Full message object:', JSON.stringify(message, null, 2))
            if (message.result) {
              console.log('📋 Setting result in jobStatus:', message.result)
              setJobStatus(prev => {
                const updated = prev ? {
                  ...prev,
                  result: message.result
                } : null
                console.log('📋 Updated jobStatus with result:', updated)
                return updated
              })
            } else {
              console.warn('⚠️ No result found in completed message!')
            }
            setState('completed')
          }
        } else if (message.type === 'completed') {
          console.log('✅ Processing completed message:', message)
          setJobStatus(prev => prev ? {
            ...prev,
            status: 'completed',
            progress: 100,
            result: message.result
          } : null)
          setState('completed')
        } else if (message.type === 'error') {
          console.log('❌ Processing error message:', message)
          setJobStatus(prev => prev ? {
            ...prev,
            status: 'failed',
            error: message.error
          } : null)
        } else {
          console.log('❓ Unknown message type:', message.type, message)
        }
      } catch (error) {
        console.error('❌ Error parsing WebSocket message:', error, 'Raw data:', event.data)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }
    
    setWebsocket(ws)
    
    return ws
  }, [])

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (websocket) {
        websocket.close()
      }
    }
  }, [websocket])

  const handleFilesAdded = (newFiles: FileInfo[]) => {
    setFiles(prev => [...prev, ...newFiles])
  }

  const handleRemoveFile = (fileId: string) => {
    setFiles(prev => prev.filter(file => file.id !== fileId))
  }

  const handleUpdateTitle = (fileId: string, title: string) => {
    setFiles(prev => prev.map(file => 
      file.id === fileId ? { ...file, title } : file
    ))
  }

  const handleStartProcessing = async () => {
    if (files.length === 0) return

    console.log('🚀 Starting processing with files:', files.length)
    setState('processing')
    
    try {
      // Check if we have a ZIP file
      const zipFile = files.find(file => file.name.endsWith('.zip'))
      
      let response
      if (zipFile && files.length === 1) {
        console.log('📦 Processing ZIP file:', zipFile.name)
        // Process ZIP file
        response = await ApiService.processZipFile(zipFile.file, config)
      } else {
        console.log('📄 Processing individual files:', files.map(f => f.name))
        // Process individual files
        const fileList = files.map(f => f.file)
        response = await ApiService.uploadFiles(fileList, config)
      }
      
      console.log('📡 API Response:', response)
      
      if (response.success && response.data) {
        const jobId = response.data.jobId
        console.log('🆔 Job ID received:', jobId)
        
        setJobStatus({
          id: jobId,
          status: 'pending',
          progress: 0
        })
        
        console.log('🔌 Connecting WebSocket for job:', jobId)
        // Connect WebSocket for real-time updates
        connectWebSocket(jobId)
      } else {
        throw new Error(response.error || 'Error starting processing')
      }
    } catch (error) {
      console.error('❌ Error starting processing:', error)
      setJobStatus({
        id: 'error',
        status: 'failed',
        progress: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }

  const handleDownload = async () => {
    if (!jobStatus?.result) return
    
    setIsDownloading(true)
    try {
      const blob = await ApiService.downloadResult(jobStatus.id)
      if (blob) {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = jobStatus.result.filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Error downloading file:', error)
    } finally {
      setIsDownloading(false)
    }
  }

  const handleStartNew = () => {
    setState('upload')
    setFiles([])
    setJobStatus(null)
    if (websocket) {
      websocket.close()
      setWebsocket(null)
    }
  }

  const handleCancelProcessing = () => {
    if (websocket) {
      websocket.close()
      setWebsocket(null)
    }
    setState('upload')
    setJobStatus(null)
  }

  const canStartProcessing = files.length > 0

  const getBreadcrumbs = () => {
    const breadcrumbs = [{ label: 'Panel de Control' }]
    
    if (state === 'upload') {
      breadcrumbs.push({ label: 'Subir Archivos' })
    } else if (state === 'processing') {
      breadcrumbs.push({ label: 'Procesando' })
    } else if (state === 'completed') {
      breadcrumbs.push({ label: 'Resultados' })
    }
    
    return breadcrumbs
  }

  const getTitle = () => {
    if (state === 'upload') return 'Subir y Configurar Documentos'
    if (state === 'processing') return 'Procesando Documentos'
    if (state === 'completed') return 'Descargar Resultados'
    return 'Fusionador de Documentos'
  }

  return (
    <DashboardLayout title={getTitle()} breadcrumbs={getBreadcrumbs()}>
      <div className="space-y-8 p-6">
        {state === 'upload' && (
          <div className="space-y-8">
            <div className="mb-8 rounded-lg border bg-card text-card-foreground shadow-sm">
              <FileDropzone onFilesAdded={handleFilesAdded} />
            </div>
            
            {files.length > 0 && (
              <div className="space-y-8">
                <div className="mt-8 rounded-lg border bg-card text-card-foreground shadow-sm">
                  <FileList 
                    files={files}
                    onRemoveFile={handleRemoveFile}
                    onUpdateTitle={handleUpdateTitle}
                  />
                </div>
                
                <div className="mt-8 rounded-lg border bg-card text-card-foreground shadow-sm">
                  <MergeConfig 
                    config={config}
                    onConfigChange={setConfig}
                    onStartProcessing={handleStartProcessing}
                    disabled={files.length === 0}
                  />
                </div>
              </div>
            )}
          </div>
        )}
        
        {state === 'processing' && jobStatus && (
          <div className="mt-8 rounded-lg border bg-card text-card-foreground shadow-sm">
            <ProcessingView 
              jobStatus={jobStatus}
              onCancel={handleCancelProcessing}
            />
          </div>
        )}
        
        {state === 'completed' && jobStatus && (
          <ResultsView 
            jobStatus={jobStatus}
            onStartNew={handleStartNew}
            onDownload={handleDownload}
            isDownloading={isDownloading}
          />
        )}
      </div>
    </DashboardLayout>
  )
}

export default App
