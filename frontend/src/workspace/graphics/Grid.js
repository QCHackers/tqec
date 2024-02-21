/* eslint-disable max-len */
/* eslint-disable guard-for-in */
/* eslint-disable no-restricted-syntax */
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
    this.name = 'Grid';
    this.interactive = true;
    this.gridSize = gridSize;
  }

  visibleUnits = () => this.units.flat().filter((unit) => unit.visible);

  selectedUnitsRectangular = () => {
    const selectedUnits = this.visibleUnits();
    const xSorted = Array.from(new Set(selectedUnits.map((unit) => unit.x))).sort((a, b) => a.x - b.x);
    const ySorted = Array.from(new Set(selectedUnits.map((unit) => unit.y))).sort((a, b) => a.y - b.y);
    // FIXME: delegate these side effects to elsewhere
    this.physicalWidth = xSorted.length * this.gridSize;
    this.physicalHeight = ySorted.length * this.gridSize;
    for (let i = 0; i < xSorted.length - 2; i += 1) {
      if (xSorted[i] + this.gridSize !== xSorted[i + 1]) {
        return false;
      }
    }
    // check ySorted
    for (let i = 0; i < ySorted.length - 2; i += 1) {
      if (ySorted[i] + this.gridSize !== ySorted[i + 1]) {
        return false;
      }
    }
    return true;
  };

  contains = (qubits) => {
    const minX = Math.min(this.visibleUnits().map((unit) => unit.x));
    const minY = Math.min(this.visibleUnits().map((unit) => unit.y));
    const unitXs = new Set(this.visibleUnits().map((unit) => [unit.x, unit.x + this.gridSize]).flat());
    const unitYs = new Set(this.visibleUnits().map((unit) => [unit.y, unit.y + this.gridSize]).flat());
    for (const qubit of qubits) {
      if (!unitXs.has(qubit.globalX) || !unitYs.has(qubit.globalY)) {
        return false;
      }
      qubit.bbX = qubit.globalX - minX;
      qubit.bbY = qubit.globalY - minY;
    }
    return true;
  };

  toString = () => this.name;
}
