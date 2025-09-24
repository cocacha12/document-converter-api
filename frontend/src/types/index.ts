export interface FileInfo {
  id: string
  name: string
  size: number
  type: string
  file: File
  title?: string
  extractedTitle?: string
}

export interface MergeConfigType {
  outputFormat: 'markdown' | 'docx' | 'pdf'
  includeTableOfContents: boolean
  customTitle?: string
  separateByTitle: boolean
}

export interface JobStatus {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message?: string
  result?: {
    downloadUrl: string
    filename: string
  }
  error?: string
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface WebSocketMessage {
  type: 'progress' | 'completed' | 'error' | 'status_update'
  jobId?: string
  job_id?: string
  status?: 'pending' | 'processing' | 'completed' | 'failed'
  progress?: number
  message?: string
  result?: {
    downloadUrl: string
    filename: string
  }
  error?: string
}