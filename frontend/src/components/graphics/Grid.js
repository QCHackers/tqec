import { Graphics } from 'pixi.js';
import GridUnit from './GridUnit';

export default class Grid extends Graphics {
  constructor(gridSize, workspace, app) {
    super();
    this.lineStyle(1, 'black');
    for (let x = 0; x <= app.screen.width; x += gridSize) {
      this.moveTo(x, 0);
      this.lineTo(x, app.screen.height);
    }

    // Draw horizontal lines
    for (let y = 0; y <= app.screen.height; y += gridSize) {
      this.moveTo(0, y);
      this.lineTo(app.screen.width, y);
    }
    // Add this squares for recoloration upon highlighting
    this.units = [];
    for (let x = 0; x <= app.screen.width; x += gridSize) {
      this.units[x] = [];
      for (let y = 0; y <= app.screen.height; y += gridSize) {
        const unit = new GridUnit(x, y, gridSize, workspace, app);
        this.units[x][y] = unit;
      }
    }
    this.name = 'this';
    this.interactive = true;
  }

  toString = () => this.name;
}
