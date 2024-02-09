import { Graphics, Color } from 'pixi.js';

export default class GridUnit extends Graphics {
  constructor(x, y, gridSize) {
    super();
    this.x = x;
    this.y = y;
    this.width = gridSize;
    this.tint = new Color('purple').toNumber();
    this.visible = false;
    this.name = `GridUnit(${x}, ${y})`;
  }

  makeVisible = () => {
    this.visible = true;
  };

  makeInvisible = () => {
    this.visible = false;
  };
}
