// Create the grid underlying the qubit array.

import { Graphics } from 'pixi.js';

/////////////////////////////////////////////////////////////

export const makeGrid = (app, gridSize = 50) => {
	// Create a PIXI.Graphics object for the grid
	const grid = new Graphics();
	// Set the line style for the grid lines
	grid.lineStyle(4, 'black');

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
	// NOTE: The grid is not added to the stage yet
	// Name the grid
	grid.name = 'grid';
	return grid;
}