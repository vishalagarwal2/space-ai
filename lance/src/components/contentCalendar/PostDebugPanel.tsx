import { useState } from "react";
import "./PostDebugPanel.css";

interface DebugInfo {
  used_fallback: boolean;
  llm_prompt: string;
  raw_llm_response: string;
  user_input: string;
  parsing_errors?: string[];
  processing_steps: string[];
  brand_context: string;
}

interface PostDebugPanelProps {
  debugInfo?: DebugInfo;
  layout: Record<string, unknown>;
}

export default function PostDebugPanel({
  debugInfo,
  layout,
}: PostDebugPanelProps) {
  const [showDebug, setShowDebug] = useState(false);

  return (
    <div className="debug-section">
      <label className="debug-toggle">
        <input
          type="checkbox"
          checked={showDebug}
          onChange={e => setShowDebug(e.target.checked)}
        />
        🔍 Show Tracing Info
      </label>
      {!debugInfo && showDebug && (
        <p className="debug-not-available">
          ⚠️ Debug information not available for this post. This usually means
          the post was generated without debug mode enabled.
        </p>
      )}

      {debugInfo && showDebug && (
        <div className="debug-panel">
          <div className="debug-section-header">
            <h4>🔍 Tracing Information</h4>
            <div className="debug-status">
              {debugInfo.used_fallback ? (
                <span className="debug-status-error">
                  ⚠️ Used Fallback Layout
                </span>
              ) : (
                <span className="debug-status-success">✅ LLM Generated</span>
              )}
            </div>
          </div>

          <div className="debug-tabs">
            <details>
              <summary>📝 Final LLM Prompt (System + User Message)</summary>
              <pre className="debug-content">{debugInfo.llm_prompt}</pre>
            </details>

            <details>
              <summary>🤖 Raw LLM Response (JSON Layout Instructions)</summary>
              <pre className="debug-content">
                {debugInfo.raw_llm_response || "No response received"}
              </pre>
            </details>

            <details>
              <summary>📋 Final Layout JSON (Used for Rendering)</summary>
              <pre className="debug-content">
                {JSON.stringify(layout, null, 2)}
              </pre>
            </details>

            <details>
              <summary>💬 Original User Input</summary>
              <pre className="debug-content">{debugInfo.user_input}</pre>
            </details>

            {debugInfo.parsing_errors &&
              debugInfo.parsing_errors.length > 0 && (
                <details>
                  <summary className="debug-error">❌ Parsing Errors</summary>
                  <pre className="debug-content debug-error-content">
                    {debugInfo.parsing_errors.join("\n\n")}
                  </pre>
                </details>
              )}

            <details>
              <summary>⚙️ Processing Steps</summary>
              <ul className="debug-steps">
                {debugInfo.processing_steps.map(
                  (step: string, index: number) => (
                    <li key={index}>{step}</li>
                  )
                )}
              </ul>
            </details>

            <details>
              <summary>🏢 Brand Context (Business Profile Info)</summary>
              <pre className="debug-content">{debugInfo.brand_context}</pre>
            </details>
          </div>
        </div>
      )}
    </div>
  );
}
