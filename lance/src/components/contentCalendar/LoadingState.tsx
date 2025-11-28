import { SpaceIcon } from "../icons/SpaceIcon";
import "./LoadingState.css";

export default function LoadingState() {
  return (
    <div className="loading-page">
      <div className="loading-content">
        <div className="loading-header">
          <div className="loading-logo">
            <SpaceIcon fill="#1ec3c8" height={32} />
          </div>
          <span className="loading-title">SPACE AI</span>
        </div>
      </div>
      <div className="loading-pulse-line"></div>
    </div>
  );
}
