import { useQueryClient } from "@tanstack/react-query";
import { contentCalendarKeys } from "@/hooks/useContentCalendar";
import "./ErrorState.css";

interface ErrorStateProps {
  error?: Error;
}

export default function ErrorState({ error }: ErrorStateProps) {
  const queryClient = useQueryClient();

  const handleRetry = () => {
    queryClient.removeQueries({
      queryKey: contentCalendarKeys.all,
    });
    queryClient.invalidateQueries({
      queryKey: contentCalendarKeys.calendars(),
    });
    window.location.reload();
  };

  const handleClearCache = () => {
    queryClient.clear();
    window.location.reload();
  };

  return (
    <div className="content-calendar-container">
      <div className="error-state">
        <div className="error-icon">⚠️</div>
        <h3>Failed to load content calendar</h3>
        {error && (
          <div className="error-details">
            <p className="error-message">{error.message}</p>
            <details className="error-stack">
              <summary>Technical Details</summary>
              <pre>{error.stack}</pre>
            </details>
          </div>
        )}
        <div className="error-actions">
          <button onClick={handleRetry} className="retry-button primary">
            🔄 Try Again
          </button>
          <button onClick={handleClearCache} className="retry-button secondary">
            🗑️ Clear Cache & Retry
          </button>
        </div>
        <div className="error-help">
          <p>If this problem persists:</p>
          <ul>
            <li>Check if the backend server is running</li>
            <li>Verify your network connection</li>
            <li>Try refreshing the page</li>
            <li>Contact support if the issue continues</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
