/**
 * @fileoverview This file contains the functions for creating the inifinite tiles
 * using the unit cell defined in the grid.
 */
import { Graphics, Text, Circle } from 'pixi.js';
import { ButtonContainer } from '@pixi/ui';

import showNotification from './components/notifier';
import { plaquette } from './plaquette';

const copyVertex = (x, y, app) => {
	const vertexCopy = new Graphics();
	vertexCopy.beginFill(0x000000);
	vertexCopy.drawCircle(0, 0, 5); // Draw a small circle representing the vertex
	vertexCopy.endFill();
	vertexCopy.eventMode = 'static';
	vertexCopy.mode = 'static';
	vertexCopy.cursor = 'pointer';
	vertexCopy.hitArea = new Circle(0, 0, 10);
	vertexCopy.x = x;
	vertexCopy.y = y;
	// Add a click event listener
	plaquette(app, vertexCopy);
	return vertexCopy;
};

const infiniteTile = (app, gridSize, selectedVertices, vertexList) => {
	// Create the tile recursively
	// Stop the recursion if all vertices are selected
	if (selectedVertices.length === vertexList.length) {
		return;
	}
	if (selectedVertices.length === 0) {
		return;
	}
	// Find the neighbors of the selected vertices
	selectedVertices.forEach((vertex) => {
		// Find the neighbors of the vertex
		const neighbor = vertexList.find(
			(v) =>
				(v.x === vertex.x + gridSize &&
					v.y === vertex.y + gridSize &&
					!selectedVertices.includes(v)) ||
				(v.x === vertex.x - gridSize &&
					v.y === vertex.y - gridSize &&
					!selectedVertices.includes(v)) ||
				(v.x === vertex.x - gridSize &&
					v.y === vertex.y + gridSize &&
					!selectedVertices.includes(v)) ||
				(v.x === vertex.x + gridSize &&
					v.y === vertex.y - gridSize &&
					!selectedVertices.includes(v))
		);
		if (!neighbor) {
			return;
		}
		//
		selectedVertices.push(neighbor);
		// Fill the vertex with a color
		const neighborCopy = copyVertex(neighbor.x, neighbor.y, app);
		// Remove the vertex from the vertexList
		vertexList.splice(vertexList.indexOf(neighbor), 1);

		app.stage.removeChild(neighbor);
		app.stage.addChild(neighborCopy);

		// Recursively call the function
		infiniteTile(app, gridSize, selectedVertices, vertexList);
	});
	// For each neighbor, check if it is in the selectedVertices list
	selectedVertices.forEach((neighbor) => {
		if (!selectedVertices.includes(neighbor)) {
			// Add the vertex to the selectedVertices list
			selectedVertices.push(neighbor);
			// Add the vertex to the selectedVertices list
			infiniteTile(app, gridSize, selectedVertices, vertexList);
		}
	});
};

export const createInfQubitArrButton = (
	app,
	selectedVertexList,
	vertexList,
	gridSize,
	displayedText
) => {
	// The button to create the infinite tile

	// Add the button to the PIXI stage
	const button = new ButtonContainer(
		new Graphics().beginFill('black').drawRoundedRect(0, 0, 100, 50, 15)
	);
	button.on('click', () => {
		// Create the tile
		console.log('clicked');
		infiniteTile(app, gridSize, selectedVertexList, vertexList);
		for (const display of displayedText) {
			app.stage.removeChild(display);
			// Replace the vertex with a copy
			// Fill the vertex with a color
			const vertexCopy = copyVertex(
				selectedVertexList[displayedText.indexOf(display)].x,
				selectedVertexList[displayedText.indexOf(display)].y,
				app
			);
			// Remove the vertex from the vertexList
			app.stage.removeChild(selectedVertexList[displayedText.indexOf(display)]);
			// Swap the vertex with the copy
			selectedVertexList.splice(displayedText.indexOf(display), 1, vertexCopy);
			app.stage.addChild(vertexCopy);
		}
		displayedText = [];
		console.log('done');
		// Notify the user that the tile has been created
		showNotification(app, 'Tile created successfully');
		// Remove the button
		setTimeout(() => {
			app.stage.removeChild(button);
		}, 1500);

		return;
	});
	// Add text to the button
	const text = new Text('Create Tile', { fill: 'white', fontSize: 15 });
	text.anchor.set(0.5);
	text.position.set(button.width / 2, button.height / 2);
	button.addChild(text);

	// Add hover effects
	button.on('pointerover', () => {
		button.alpha = 0.8;
	});
	button.on('pointerout', () => {
		button.alpha = 1;
	});
	// Add the button to the PIXI stage
	app.stage.addChild(button);
};
