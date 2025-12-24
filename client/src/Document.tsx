import Editor from "./internal/Editor";
import useWebSocket from "react-use-websocket";
import { debounce } from "lodash";
import { useCallback, useEffect, useState } from "react";

// === Props expected by Document component ===
export interface DocumentProps {
  onContentChange: (content: string) => void;
  content: string;
  onSuggestions: (suggestions: any[]) => void;
  onSelectionChange: (selection: string) => void;
}

// WebSocket endpoint 
const SOCKET_URL = "ws://localhost:8000/ws";

export default function Document({ onContentChange, content, onSuggestions, onSelectionChange }: DocumentProps) {
  const [messageHistory, setMessageHistory] = useState<MessageEvent[]>([]);

  // Initialize WebSocket connection using react-use-websocket
  const { sendMessage, lastMessage } = useWebSocket(SOCKET_URL, {
    onOpen: () => console.log("WebSocket Connected"),
    onClose: () => console.log("WebSocket Disconnected"),
    shouldReconnect: (_closeEvent) => true,
    // Optionally, you can configure WebSocket options here
  });

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage !== null) {

      setMessageHistory((prev) => prev.concat(lastMessage));

      try { 
        const data = JSON.parse(lastMessage.data);

        if (data.error) {
          console.warn("AI Error:", data.error);
          return;
        }

        // Sort issues by severity in the order [high, medium, low]
        if (data.issues) {
          const severityRank: Record<string, number> = {
            high: 3,
            medium: 2,
            low: 1,
          };

          const sortedIssues = data.issues.sort((a: any, b: any) => {
            return (severityRank[b.severity] || 0) - (severityRank[a.severity] || 0);
          });

          // Pass sorted issues back up to App.tsx (to show in "AI Suggestions" box)
          onSuggestions(sortedIssues);
        }
      } catch {
        console.error("Invalid AI message:", lastMessage.data);
      }
    }
  }, [lastMessage, setMessageHistory]);


  // Debounce editor content changes
  // Prevents flooding the server by waiting 500ms after the last change
  const sendEditorContent = useCallback(
    debounce((content: string) => {
      sendMessage(content);
    }, 500), // Adjust debounce time as needed
    [sendMessage]
  );

  // === Handle editor content changes ===
  const handleEditorChange = (content: string) => {
    onContentChange(content);
    sendEditorContent(content);
  };

  // === Render editor wrapped with mouse selection listener ===
  return (
    <div className="w-full h-full overflow-y-auto">
      <Editor handleEditorChange={handleEditorChange} content={content} />
    </div>
  );
}
