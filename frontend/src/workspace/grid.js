import { Graphics } from 'pixi.js';
import GridUnit from './GridUnit';

export default function makeGrid(app, gridSize = 50) {
  // Create a PIXI.Graphics object for the grid
  const grid = new Graphics();
  // Set the line style for the grid lines
  grid.lineStyle(1, 'black');

  // Draw vertical lines
  for (let x = 0; x <= app.screen.width; x += gridSize) {
    grid.moveTo(x, 0);
    grid.lineTo(x, app.screen.height);
  }

  // Draw horizontal lines
  for (let y = 0; y <= app.screen.height; y += gridSize) {
    grid.moveTo(0, y);
    grid.lineTo(app.screen.width, y);
  }
  // Add grid squares for recoloration upon highlighting
  grid.units = [];
  for (let x = 0; x <= app.screen.width; x += gridSize) {
    grid.units[x] = [];
    for (let y = 0; y <= app.screen.height; y += gridSize) {
      const unit = GridUnit(x, y, gridSize);
      grid.units[x][y] = unit;
    }
  }
  // NOTE: The grid is not added to the stage yet
  // Name the grid
  grid.name = 'grid';
  return grid;
}
