import { Graphics, Text, Container, Circle } from 'pixi.js';

import { createInfQubitArrButton } from './qubitArray';

export const selectQubit = (app, vertexList, displayedText) => {};

export const grid = (app) => {
	const container = new Container();

	app.stage.addChild(container);
	// Create a PIXI.Graphics object for the grid
	const grid = new Graphics();
	// Set the line style for the grid lines
	grid.lineStyle(1, 0x000000);

	// Calcualte grid size
	const gridSize = 100;

	// Draw vertical lines
	for (let x = 0; x <= app.screen.width; x += gridSize) {
		grid.moveTo(x, 0);
		grid.lineTo(x, app.screen.height);
	}

	// Draw horizontal lines
	for (let y = 0; y <= app.screen.height; y += gridSize) {
		console.log(y);
		grid.moveTo(0, y);
		grid.lineTo(app.screen.width, y);
	}

	// Create a Graphic for intersections of grid lines
	const vertexList = [];
	const displayedText = []; // Track displayed text objects
	const selectedVertexList = []; // Track selected vertices

	for (let x = 0; x <= app.screen.width; x += gridSize) {
		for (let y = 0; y <= app.screen.height; y += gridSize) {
			const qubit = new Graphics();
			// Create the vertex 0x1099bb
			qubit.x = x;
			qubit.y = y;
			qubit.eventMode = 'static'; // Set the event mode to static
			qubit.cursor = 'pointer'; // Show pointer cursor on hover
			qubit.hitArea = new Circle(0, 0, 10); // Set the hit area to a circle
			// Add a click event listener
			qubit.on('click', () => {
				console.log(`Clicked on vertex (${x},${y})`);
				// Check if text is already displayed for this vertex
				const index = displayedText.findIndex(
					(text) => text.x - 15 === qubit.x && text.y + 15 === qubit.y
				);
				if (index !== -1) {
					// Remove the fill from the vertex
					qubit.clear();
					// If text exists, remove it and update the displayedText array
					app.stage.removeChild(displayedText[index]);
					displayedText.splice(index, 1);
					// Remove the vertex from the selectedVertexList
					selectedVertexList.splice(index, 1);
				} else {
					// Fill the vertex with a color
					qubit.beginFill(0x000000);
					qubit.drawCircle(0, 0, 5); // Draw a small circle representing the vertex
					qubit.endFill();
					// If no text exists, create and display the integer next to the vertex
					const text = new Text(`Qubit: ${displayedText.length + 1}`, {
						fill: 'black',
						fontSize: 12,
						fontFamily: 'Arial',
					});
					text.x = qubit.x + 15;
					text.y = qubit.y - 15;
					app.stage.addChild(text);
					displayedText.push(text);
					selectedVertexList.push(qubit);

					if (selectedVertexList.length > 0) {
						createInfQubitArrButton(
							app,
							selectedVertexList,
							vertexList,
							gridSize,
							displayedText
						);
					}
				}
			});
			vertexList.push(qubit);
			app.stage.addChild(qubit);
		}
	}

	// Add the grid to the app
	app.stage.addChild(grid);
	// Return the vertex list and the display container
	return {
		vertexList,
		displayedText,
	};
};
