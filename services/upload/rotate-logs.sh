#!/bin/bash
# Log rotation script for Stream-Line Upload Server
# This ensures log files don't grow too large

LOG_DIR="/home/ubuntu/file-uploader/services/upload/logs"
MAX_SIZE_MB=100  # Rotate logs when they exceed this size in MB

rotate_log() {
    local log_file="$1"
    local file_path="$LOG_DIR/$log_file"
    
    if [ -f "$file_path" ]; then
        # Get file size in MB
        size_mb=$(du -m "$file_path" | cut -f1)
        
        if [ "$size_mb" -gt "$MAX_SIZE_MB" ]; then
            echo "Rotating $log_file (${size_mb}MB > ${MAX_SIZE_MB}MB)"
            
            # Create backup with timestamp
            timestamp=$(date +%Y%m%d_%H%M%S)
            backup_name="${log_file%.log}_${timestamp}.log"
            
            # Move current log to backup
            mv "$file_path" "$LOG_DIR/$backup_name"
            
            # Compress old log
            gzip "$LOG_DIR/$backup_name"
            
            # Create new empty log file
            touch "$file_path"
            
            # Set proper permissions
            chmod 644 "$file_path"
            chown ubuntu:ubuntu "$file_path"
            
            echo "Created backup: ${backup_name}.gz"
        fi
    fi
}

echo "🔄 Log Rotation Check - $(date)"
echo "================================"

# Rotate each log file if needed
rotate_log "access.log"
rotate_log "activity.log"
rotate_log "server.log"
rotate_log "error.log"

# Clean up old compressed logs (keep last 10 for each type)
echo "🧹 Cleaning up old log archives..."
for log_type in access activity server error; do
    find "$LOG_DIR" -name "${log_type}_*.log.gz" -type f | sort -r | tail -n +11 | xargs rm -f
done

echo "✅ Log rotation complete"
