import { Graphics, Color } from 'pixi.js';

export default class GridUnit extends Graphics {
  constructor(x, y, gridUnitSize, workspace, app) {
    super();
    this.view = app.view;
    this.screen = app.screen;
    this.stage = app.stage;
    // Calculate the relative click position within the canvas
    this.x = x;
    this.y = y;
    this.eventMode = 'static';
    this.buttonMode = true;
    this.cursor = 'pointer';
    this.interactive = true;
    this.workspace = workspace;
    this.gridUnitSize = gridUnitSize;
    this.color = new Color('green').toNumber();
    this.beginFill(this.color, 0.5);
    // eslint-disable-next-line max-len
    this.drawRect(this.x / 250, this.y / 250, this.gridUnitSize, this.gridUnitSize);
    this.endFill();
    this.visible = false;
    this.name = `GridUnit(${this.x}, ${this.y})`;
    this.workspace.addChild(this);
  }

  // eslint-disable-next-line class-methods-use-this
  viewportX = (x) => Math.floor(x / this.gridUnitSize) * this.gridUnitSize;

  // eslint-disable-next-line max-len
  viewportY = (y) => Math.floor((y - this.view.getBoundingClientRect().top) / this.gridUnitSize) * this.gridUnitSize;

  toggleVisibility = (e) => {
    e.stopPropagation();
    // Calculate the relative click position within the canvas
    const relativeX = this.viewportX(e.clientX);
    const relativeY = this.viewportY(e.clientY);
    // Ensure relativeX and relativeY are not behind the main button
    if (relativeX <= this.workspace.mainButtonPosition.x
        && relativeY <= this.workspace.mainButtonPosition.y) {
      return;
    }
    // Check whether the click was within the bounds of the grid unit
    if (relativeX === this.x && relativeY === this.y) {
      this.visible = !this.visible;
    }
  };

  toString = () => this.name;
}
