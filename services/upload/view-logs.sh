#!/bin/bash
# Stream-Line Upload Server Log Viewer
# Easy access to different log types

LOG_DIR="/home/ubuntu/file-uploader/services/upload/logs"

echo "🔍 Stream-Line Upload Server Log Viewer"
echo "========================================"
echo ""

# Check if logs directory exists
if [ ! -d "$LOG_DIR" ]; then
    echo "❌ Logs directory not found: $LOG_DIR"
    exit 1
fi

# Function to show log file with formatting
show_log() {
    local log_file="$1"
    local log_name="$2"
    local lines="${3:-20}"
    
    echo "📋 $log_name (Last $lines lines):"
    echo "----------------------------------------"
    
    if [ -f "$LOG_DIR/$log_file" ] && [ -s "$LOG_DIR/$log_file" ]; then
        tail -n "$lines" "$LOG_DIR/$log_file" | while IFS= read -r line; do
            # Pretty print JSON logs if they contain activity/access data
            if [[ "$line" == *"{"* ]] && [[ "$line" == *"}"* ]]; then
                echo "$line" | python3 -m json.tool 2>/dev/null || echo "$line"
            else
                echo "$line"
            fi
        done
    else
        echo "(No entries yet)"
    fi
    echo ""
}

# Function to monitor logs in real-time
monitor_logs() {
    echo "🔄 Monitoring all logs in real-time (Ctrl+C to stop)..."
    echo "========================================================="
    tail -f "$LOG_DIR"/*.log
}

# Menu system
if [ "$1" = "monitor" ] || [ "$1" = "follow" ] || [ "$1" = "tail" ]; then
    monitor_logs
    exit 0
fi

if [ "$1" = "access" ]; then
    show_log "access.log" "ACCESS LOGS" "${2:-50}"
    exit 0
fi

if [ "$1" = "activity" ]; then
    show_log "activity.log" "ACTIVITY LOGS" "${2:-50}"
    exit 0
fi

if [ "$1" = "server" ]; then
    show_log "server.log" "SERVER LOGS" "${2:-50}"
    exit 0
fi

if [ "$1" = "error" ]; then
    show_log "error.log" "ERROR LOGS" "${2:-50}"
    exit 0
fi

# Default: show summary of all logs
echo "📊 LOG SUMMARY:"
echo "---------------"
echo "🌐 Access Log:   $(wc -l < "$LOG_DIR/access.log" 2>/dev/null || echo "0") entries"
echo "📁 Activity Log: $(wc -l < "$LOG_DIR/activity.log" 2>/dev/null || echo "0") entries"
echo "🖥️  Server Log:   $(wc -l < "$LOG_DIR/server.log" 2>/dev/null || echo "0") entries"
echo "❌ Error Log:    $(wc -l < "$LOG_DIR/error.log" 2>/dev/null || echo "0") entries"
echo ""

# Show recent entries from each log
show_log "server.log" "SERVER LOGS" 5
show_log "access.log" "ACCESS LOGS" 3
show_log "activity.log" "ACTIVITY LOGS" 3
show_log "error.log" "ERROR LOGS" 3

echo "💡 Usage:"
echo "  $0                    # Show this summary"
echo "  $0 access [lines]     # Show access logs"
echo "  $0 activity [lines]   # Show activity logs"
echo "  $0 server [lines]     # Show server logs"
echo "  $0 error [lines]      # Show error logs"
echo "  $0 monitor            # Follow all logs in real-time"
