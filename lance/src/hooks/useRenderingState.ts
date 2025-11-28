import { useState, useCallback } from "react";
import { RenderingStep } from "../types/Layout";

const initialSteps: RenderingStep[] = [
  {
    id: "init",
    name: "Initialize Canvas",
    status: "pending",
    progress: 0,
    description: "Setting up canvas dimensions and context",
  },
  {
    id: "fonts",
    name: "Load Fonts",
    status: "pending",
    progress: 0,
    description: "Loading required fonts for text rendering",
  },
  {
    id: "template",
    name: "Apply Template",
    status: "pending",
    progress: 0,
    description: "Applying selected template design to canvas",
  },
  {
    id: "background",
    name: "Render Background",
    status: "pending",
    progress: 0,
    description: "Applying gradients, colors, and background elements",
  },
  {
    id: "shapes",
    name: "Draw Shapes",
    status: "pending",
    progress: 0,
    description: "Adding geometric elements and decorative shapes",
  },
  {
    id: "text",
    name: "Render Text",
    status: "pending",
    progress: 0,
    description: "Positioning and drawing text blocks with typography",
  },
  {
    id: "images",
    name: "Load Images",
    status: "pending",
    progress: 0,
    description: "Adding logos, icons, and other image elements",
  },
  {
    id: "finalize",
    name: "Finalize",
    status: "pending",
    progress: 0,
    description: "Final composition and image export",
  },
];

export const useRenderingState = (
  onStepUpdate?: (step: RenderingStep) => void
) => {
  const [renderingSteps, setRenderingSteps] =
    useState<RenderingStep[]>(initialSteps);
  const [isRendering, setIsRendering] = useState(false);
  const [renderingProgress, setRenderingProgress] = useState(0);
  const [currentStepName, setCurrentStepName] = useState("");

  const updateStep = useCallback(
    async (
      stepId: string,
      status: RenderingStep["status"],
      progress = 0,
      error?: string
    ) => {
      const now = Date.now();

      setRenderingSteps(prev => {
        const newSteps = prev.map(step => {
          if (step.id === stepId) {
            const updatedStep: RenderingStep = {
              ...step,
              status,
              progress,
              error,
              startTime: status === "active" ? now : step.startTime,
              endTime:
                status === "completed" || status === "error" ? now : undefined,
            };

            onStepUpdate?.(updatedStep);

            if (status === "active") {
              setCurrentStepName(step.name);
            }

            return updatedStep;
          }
          return step;
        });

        const completedSteps = newSteps.filter(
          s => s.status === "completed"
        ).length;
        const totalSteps = newSteps.length;
        setRenderingProgress((completedSteps / totalSteps) * 100);

        return newSteps;
      });
    },
    [onStepUpdate]
  );

  const resetSteps = useCallback(() => {
    setRenderingSteps(initialSteps);
    setRenderingProgress(0);
    setCurrentStepName("");
  }, []);

  return {
    renderingSteps,
    isRendering,
    setIsRendering,
    renderingProgress,
    currentStepName,
    updateStep,
    resetSteps,
  };
};
