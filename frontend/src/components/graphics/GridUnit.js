import { Graphics, Color } from 'pixi.js';

export default class GridUnit extends Graphics {
  constructor(x, y, gridUnitSize, workspace, app) {
    super();
    this.x = x;
    this.y = y;
    this.workspace = workspace;
    this.app = app;
    this.gridUnitSize = gridUnitSize;
    this.tint = new Color('purple').toNumber();
    this.visible = false;
    this.name = `GridUnit(${x}, ${y})`;
  }

  toggleVisibility = (e) => {
    // e.stopPropagation();
    const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position
    // Calculate the relative click position within the canvas
    const relativeX = Math.floor(e.clientX);
    const relativeY = Math.floor(e.clientY - canvasRect.top);
    // Ensure relativeX and relativeY are not behind the main button
    if (relativeX < this.workspace.mainButtonPosition.x
        && relativeY < this.workspace.mainButtonPosition.y) {
      return;
    }
    // console.log('Click at ', relativeX, relativeY, 'on grid unit at ', this.x, this.y);
    // Check whether the click was within the bounds of the grid unit
    if (
      relativeX >= this.x
      && relativeX <= this.x + this.gridUnitSize
      && relativeY >= this.y
      && relativeY <= this.y + this.gridUnitSize
    ) {
      console.log('Toggling visibility', this.name);
      this.visible = !this.visible;
    }
  };

  toString = () => this.name;
}
