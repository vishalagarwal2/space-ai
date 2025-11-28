import "./AddIdeaModal.css";

interface AddIdeaModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit?: (data: {
    date: string;
    contentIdea: string;
    mediaFiles: FileList | null;
  }) => void;
}

export default function AddIdeaModal({
  isOpen,
  onClose,
  onSubmit,
}: AddIdeaModalProps) {
  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const date = formData.get("date") as string;
    const contentIdea = formData.get("contentIdea") as string;
    const mediaFiles = formData.get("mediaFiles") as FileList | null;

    if (onSubmit) {
      onSubmit({ date, contentIdea, mediaFiles });
    }
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h3>Add content idea</h3>
        <form className="add-idea-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Date:</label>
            <input type="date" name="date" className="form-input" required />
          </div>
          <div className="form-group">
            <label>Content idea:</label>
            <textarea
              name="contentIdea"
              className="form-textarea"
              rows={4}
              required
            />
          </div>
        </form>
      </div>
    </div>
  );
}
