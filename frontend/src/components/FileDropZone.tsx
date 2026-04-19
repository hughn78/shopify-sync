import { useCallback, useState, type DragEvent } from 'react';
import { Upload, Loader2, FileCheck2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileDropZoneProps {
  accept: string;
  onFiles: (files: File[]) => void;
  label: string;
  hint?: string;
  isLoading?: boolean;
  disabled?: boolean;
  selectedFiles?: File[];
  multiple?: boolean;
}

export function FileDropZone({
  accept,
  onFiles,
  label,
  hint,
  isLoading = false,
  disabled = false,
  selectedFiles = [],
  multiple = false,
}: FileDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLLabelElement>) => {
      e.preventDefault();
      setIsDragOver(false);
      if (disabled || isLoading) return;
      const files = Array.from(e.dataTransfer.files || []);
      if (files.length) onFiles(files);
    },
    [disabled, isLoading, onFiles],
  );

  return (
    <label
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled && !isLoading) setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      className={cn(
        'flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-6 text-center transition-colors cursor-pointer',
        isDragOver ? 'border-primary bg-primary/5' : 'border-border bg-card hover:border-primary/40',
        (disabled || isLoading) && 'cursor-not-allowed opacity-60',
      )}
    >
      <input
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        disabled={disabled || isLoading}
        onChange={(e) => {
          const files = Array.from(e.target.files || []);
          if (files.length) onFiles(files);
          e.target.value = '';
        }}
      />
      {isLoading ? (
        <Loader2 className="h-8 w-8 text-primary animate-spin" />
      ) : selectedFiles.length ? (
        <FileCheck2 className="h-8 w-8 text-green-600" />
      ) : (
        <Upload className="h-8 w-8 text-muted-foreground" />
      )}
      <div className="text-sm font-medium text-foreground">{label}</div>
      {selectedFiles.length ? (
        <div className="text-xs text-muted-foreground max-w-full">
          {selectedFiles.length === 1 ? selectedFiles[0].name : `${selectedFiles.length} files selected`}
        </div>
      ) : hint ? (
        <div className="text-xs text-muted-foreground">{hint}</div>
      ) : null}
      <div className="text-xs text-muted-foreground/70 mt-1">Drop file or click to browse</div>
    </label>
  );
}
