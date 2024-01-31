// Create the grid underlying the qubit array.

import { Graphics } from 'pixi.js';

/////////////////////////////////////////////////////////////

export const makeGrid = (app, gridSize = 50, isRotated = true) => {
	/**
	 * Two grids are possible:
	 * - a square grid with horizontal and vertical lines running at a distance equal to the gridSize
	 * - a square grid with 45°/-45° lines, intersecting where the qubits are located 
	 */
	// Create a PIXI.Graphics object for the grid
	const grid = new Graphics();
	// Set the line style for the grid lines
	grid.lineStyle(4, 'black');

	if (isRotated === false) {
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
	} else {
		for (let x = 0; x <= app.screen.width; x += 2*gridSize) {
			// Draw lines at 45°, like '\' due to the reference system
			grid.moveTo(x, 0);
			const d1 = Math.min(app.screen.height, app.screen.width-x);
			grid.lineTo(x+d1, d1);
			// Draw lines at -45°, like '/' due to the reference system
			grid.moveTo(x, 0);
			const d2 = Math.min(app.screen.height, x);
			grid.lineTo(x-d2, d2);
		}
		for (let y = 0; y <= app.screen.height; y += 2*gridSize) {
			// Draw lines at 45°, like '\' due to the reference system
			grid.moveTo(0, y);
			const d1 = Math.min(app.screen.height-y, app.screen.width);
			grid.lineTo(0+d1, y+d1);
			// Draw lines at -45°, like '/' due to the reference system
			grid.moveTo(app.screen.width, y);
			const d2 = Math.min(app.screen.height-y, app.screen.width);
			grid.lineTo(app.screen.width-d2, y+d2);
		}
	}

	grid.name = 'grid';
	return grid;
	// NOTE: The grid is not added to the stage yet
}