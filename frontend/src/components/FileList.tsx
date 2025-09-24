import React from 'react'
import { X, FileText, Archive, Edit2, Check } from 'lucide-react'
import { cn, formatFileSize } from '@/lib/utils'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import type { FileInfo } from '../types'

interface FileListProps {
  files: FileInfo[]
  onRemoveFile: (fileId: string) => void
  onUpdateTitle: (fileId: string, title: string) => void
  disabled?: boolean
}

export function FileList({ files, onRemoveFile, onUpdateTitle, disabled = false }: FileListProps) {
  const [editingId, setEditingId] = React.useState<string | null>(null)
  const [editTitle, setEditTitle] = React.useState('')

  const handleStartEdit = (file: FileInfo) => {
    setEditingId(file.id)
    setEditTitle(file.title || file.extractedTitle || file.name.replace(/\.[^/.]+$/, ''))
  }

  const handleSaveEdit = (fileId: string) => {
    onUpdateTitle(fileId, editTitle)
    setEditingId(null)
    setEditTitle('')
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditTitle('')
  }

  const getFileIcon = (file: FileInfo) => {
    const iconClass = "w-6 h-6 transition-all duration-300 group-hover:scale-110"
    
    if (file.name.endsWith('.zip')) {
      return <Archive className={cn(iconClass, "text-orange-500 group-hover:text-orange-600")} />
    }
    return <FileText className={cn(iconClass, "text-blue-500 group-hover:text-blue-600")} />
  }

  const getFileTypeColor = (file: FileInfo) => {
    if (file.name.endsWith('.pdf')) return 'from-red-500/20 to-red-600/20 text-red-700 border-red-200'
    if (file.name.endsWith('.docx')) return 'from-blue-500/20 to-blue-600/20 text-blue-700 border-blue-200'
    if (file.name.endsWith('.zip')) return 'from-orange-500/20 to-orange-600/20 text-orange-700 border-orange-200'
    return 'from-gray-500/20 to-gray-600/20 text-gray-700 border-gray-200'
  }

  if (files.length === 0) {
    return null
  }

  return (
    <Card className="glass shadow-elegant border-white/20 backdrop-blur-xl">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-3 text-lg font-semibold">
          <div className="p-2 rounded-lg bg-primary/10 text-primary">
            <FileText className="h-5 w-5" />
          </div>
          Archivos ({files.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 px-6 pb-6">
        {files.map((file, index) => (
          <div
            key={index}
            className="group flex items-center justify-between p-4 border border-white/10 rounded-xl bg-white/5 backdrop-blur-sm hover:bg-white/10 transition-all duration-300 shadow-modern"
          >
            <div className="flex items-center gap-4 flex-1 min-w-0">
              <Badge variant="secondary" className="shrink-0 px-3 py-1 bg-primary/20 text-primary border-primary/30">
                {file.name.split('.').pop()?.toUpperCase()}
              </Badge>
              <div className="flex-1 min-w-0">
                <Input
                  value={file.title || file.extractedTitle || file.name.replace(/\.[^/.]+$/, '')}
                  onChange={(e) => onUpdateTitle(file.id, e.target.value)}
                  className="border-0 bg-transparent p-0 h-auto font-medium focus-visible:ring-0 text-foreground placeholder:text-muted-foreground/70"
                  placeholder="Título del documento"
                />
                <p className="text-sm text-muted-foreground/80 truncate mt-1">
                  {file.name} • {formatFileSize(file.size)}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemoveFile(file.id)}
              className="shrink-0 ml-3 h-8 w-8 p-0 hover:bg-destructive/20 hover:text-destructive transition-colors opacity-70 group-hover:opacity-100"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}