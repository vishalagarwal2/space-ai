import "./ChatBubble.css";

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
  isTyping?: boolean;
}

export default function ChatBubble({
  role,
  content,
  isTyping = false,
}: ChatBubbleProps) {
  return (
    <div className={`chat-bubble ${role}`}>
      <div className="bubble-content">
        <div className="bubble-message">
          {isTyping ? (
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          ) : (
            <p>{content}</p>
          )}
        </div>
      </div>
    </div>
  );
}
