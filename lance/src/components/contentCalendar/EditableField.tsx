import "./EditableField.css";

interface EditableFieldProps {
  label: string;
  value: string;
  isEditing: boolean;
  editValue: string;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSaveEdit: () => void;
  onChange: (value: string) => void;
  isSaving?: boolean;
  multiline?: boolean;
}

export default function EditableField({
  label,
  value,
  isEditing,
  editValue,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onChange,
  isSaving = false,
  multiline = false,
}: EditableFieldProps) {
  const fieldName = label.toLowerCase().replace(":", "");

  return (
    <div
      className={`preview-${fieldName} preview-field-editable ${isEditing ? "editing" : ""}`}
    >
      <span className="preview-label">
        {label}
        {!isEditing && (
          <span
            className="edit-icon"
            onClick={onStartEdit}
            title={`Edit ${fieldName}`}
          >
            ✏️
          </span>
        )}
      </span>
      {isEditing ? (
        <>
          {multiline ? (
            <textarea
              value={editValue}
              onChange={e => onChange(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Escape") {
                  onCancelEdit();
                }
              }}
              autoFocus
            />
          ) : (
            <input
              type="text"
              value={editValue}
              onChange={e => onChange(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  onSaveEdit();
                } else if (e.key === "Escape") {
                  onCancelEdit();
                }
              }}
              autoFocus
            />
          )}
          <div className="edit-actions">
            <button
              className="edit-save-button"
              onClick={onSaveEdit}
              disabled={isSaving}
            >
              Save
            </button>
            <button
              className="edit-cancel-button"
              onClick={onCancelEdit}
              disabled={isSaving}
            >
              Cancel
            </button>
          </div>
        </>
      ) : (
        <p className="preview-text">{value}</p>
      )}
    </div>
  );
}
