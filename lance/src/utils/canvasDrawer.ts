import { Shape } from "@/types/Canvas";

export const drawShape = (
  ctx: CanvasRenderingContext2D,
  shape: Shape,
  selectedShapeId: string | null
) => {
  ctx.save();

  if (shape.rotation) {
    const centerX = shape.x + (shape.width || 0) / 2;
    const centerY = shape.y + (shape.height || 0) / 2;
    ctx.translate(centerX, centerY);
    ctx.rotate((shape.rotation * Math.PI) / 180);
    ctx.translate(-centerX, -centerY);
  }

  ctx.strokeStyle = shape.color;
  ctx.fillStyle = shape.color;
  ctx.lineWidth = shape.strokeWidth || 2;

  switch (shape.type) {
    case "rectangle":
      if (shape.width && shape.height) {
        ctx.strokeRect(shape.x, shape.y, shape.width, shape.height);
        if (selectedShapeId === shape.id) {
          ctx.strokeStyle = "#FF6B6B";
          ctx.lineWidth = 3;
          ctx.setLineDash([5, 5]);
          ctx.strokeRect(
            shape.x - 2,
            shape.y - 2,
            shape.width + 4,
            shape.height + 4
          );
          ctx.setLineDash([]);
        }
      }
      break;

    case "circle":
      if (shape.radius) {
        ctx.beginPath();
        ctx.arc(shape.x, shape.y, shape.radius, 0, 2 * Math.PI);
        ctx.stroke();
        if (selectedShapeId === shape.id) {
          ctx.strokeStyle = "#FF6B6B";
          ctx.lineWidth = 3;
          ctx.setLineDash([5, 5]);
          ctx.beginPath();
          ctx.arc(shape.x, shape.y, shape.radius + 3, 0, 2 * Math.PI);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }
      break;

    case "cross":
      const crossSize = shape.width || 20;
      const crossThickness = shape.strokeWidth || 3;
      ctx.fillRect(
        shape.x - crossSize / 2,
        shape.y - crossThickness / 2,
        crossSize,
        crossThickness
      );
      ctx.fillRect(
        shape.x - crossThickness / 2,
        shape.y - crossSize / 2,
        crossThickness,
        crossSize
      );
      if (selectedShapeId === shape.id) {
        ctx.strokeStyle = "#FF6B6B";
        ctx.lineWidth = 2;
        ctx.setLineDash([3, 3]);
        ctx.strokeRect(
          shape.x - crossSize / 2 - 3,
          shape.y - crossSize / 2 - 3,
          crossSize + 6,
          crossSize + 6
        );
        ctx.setLineDash([]);
      }
      break;

    case "line":
      if (shape.width && shape.height) {
        ctx.beginPath();
        ctx.moveTo(shape.x, shape.y);
        ctx.lineTo(shape.x + shape.width, shape.y + shape.height);
        ctx.stroke();
        if (selectedShapeId === shape.id) {
          ctx.strokeStyle = "#FF6B6B";
          ctx.lineWidth = (shape.strokeWidth || 2) + 2;
          ctx.setLineDash([5, 5]);
          ctx.beginPath();
          ctx.moveTo(shape.x, shape.y);
          ctx.lineTo(shape.x + shape.width, shape.y + shape.height);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }
      break;

    case "triangle":
      if (shape.points && shape.points.length === 3) {
        ctx.beginPath();
        ctx.moveTo(shape.points[0].x, shape.points[0].y);
        ctx.lineTo(shape.points[1].x, shape.points[1].y);
        ctx.lineTo(shape.points[2].x, shape.points[2].y);
        ctx.closePath();
        ctx.fill();
        if (selectedShapeId === shape.id) {
          ctx.strokeStyle = "#FF6B6B";
          ctx.lineWidth = 3;
          ctx.setLineDash([5, 5]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }
      break;

    case "text":
      if (shape.text) {
        ctx.font = `${shape.fontSize || 16}px Arial`;
        ctx.fillText(shape.text, shape.x, shape.y);
        if (selectedShapeId === shape.id) {
          const textMetrics = ctx.measureText(shape.text);
          ctx.strokeStyle = "#FF6B6B";
          ctx.lineWidth = 2;
          ctx.setLineDash([3, 3]);
          ctx.strokeRect(
            shape.x - 2,
            shape.y - (shape.fontSize || 16) - 2,
            textMetrics.width + 4,
            (shape.fontSize || 16) + 4
          );
          ctx.setLineDash([]);
        }
      }
      break;
  }

  ctx.restore();
};

export const drawCanvas = (
  canvas: HTMLCanvasElement,
  shapes: Shape[],
  selectedShapeId: string | null,
  colorPalette: { background: string },
  width: number,
  height: number
) => {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = colorPalette.background;
  ctx.fillRect(0, 0, width, height);

  shapes.forEach(shape => {
    drawShape(ctx, shape, selectedShapeId);
  });
};
