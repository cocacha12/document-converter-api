import axios from 'axios'
import type { ApiResponse, JobStatus, MergeConfigType } from '../types'

const API_BASE_URL = 'http://localhost:8002'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

export class ApiService {
  static async uploadFiles(files: File[], config: MergeConfigType): Promise<ApiResponse<{ jobId: string }>> {
    try {
      const formData = new FormData()
      
      files.forEach((file, index) => {
        formData.append('files', file)
      })
      
      formData.append('output_format', config.outputFormat)
      formData.append('include_toc', config.includeTableOfContents.toString())
      
      if (config.customTitle) {
        formData.append('custom_title', config.customTitle)
      }
      
      formData.append('separate_by_title', config.separateByTitle.toString())
      
      const response = await api.post('/merge-docx', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      return {
        success: true,
        data: { jobId: response.data.job_id },
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Error uploading files',
      }
    }
  }
  
  static async processZipFile(file: File, config: MergeConfigType): Promise<ApiResponse<{ jobId: string }>> {
    try {
      const formData = new FormData()
      formData.append('zip_file', file)
      formData.append('output_format', config.outputFormat)
      formData.append('include_toc', config.includeTableOfContents.toString())
      
      if (config.customTitle) {
        formData.append('custom_title', config.customTitle)
      }
      
      formData.append('separate_by_title', config.separateByTitle.toString())
      
      const response = await api.post('/process-zip', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      return {
        success: true,
        data: { jobId: response.data.job_id },
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Error processing ZIP file',
      }
    }
  }
  
  static async getJobStatus(jobId: string): Promise<ApiResponse<JobStatus>> {
    try {
      const response = await api.get(`/status/${jobId}`)
      return {
        success: true,
        data: response.data,
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Error getting job status',
      }
    }
  }
  
  static async getJobResult(jobId: string): Promise<ApiResponse<any>> {
    try {
      const response = await api.get(`/result/${jobId}`)
      return {
        success: true,
        data: response.data,
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Error getting job result',
      }
    }
  }

  static async downloadResult(jobId: string): Promise<Blob | null> {
    try {
      const response = await api.get(`/download/${jobId}`, {
        responseType: 'blob',
      })
      return response.data
    } catch (error) {
      console.error('Error downloading result:', error)
      return null
    }
  }
  
  static createWebSocket(jobId: string): WebSocket {
    return new WebSocket(`ws://localhost:8002/ws/${jobId}`)
  }
}