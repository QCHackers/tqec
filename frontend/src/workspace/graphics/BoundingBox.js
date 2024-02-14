import { Graphics } from 'pixi.js';

export default class BoundingBox extends Graphics {
  constructor() {
    super();
    this.on('pointerdown', (e) => {
      this.startDragging(e);
    });
  }

  startDragging = (e) => {
    console.log('Dragging the bounding box');
  };

  onDrag = (e) => {
    console.log('Dragging the bounding box');
  };

  stopDragging = (e) => {
    console.log('Dragging the bounding box');
  };
}
