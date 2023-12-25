import { useApp } from '@pixi/react';
import { Container, Graphics } from 'pixi.js';
import { makeGrid } from './grid';
import Qubit from './QubitClass';
import Plaquette from './plaquettes/PlaquetteClass';
import Tile from './TileClass';
import { Button } from './components/button';

export default function TQECApp() {
	// Initialize the app
	let app = useApp();
	// Remove all children from the stage to avoid rendering issues
	app.stage.removeChildren();
	const gridSize = 50;
	// Let's create the workspace
	const workspace = new Container();
	// Create the grid container
	const grid = makeGrid(app, gridSize);

	workspace.addChild(grid);
	// Add the qubits to the workspace
	for (let x = 0; x <= app.renderer.width; x += gridSize) {
		for (let y = 0; y <= app.renderer.height; y += gridSize) {
			// Skip every other qubit
			if (x % (gridSize * 2) === 0 && y % (gridSize * 2) === 0) continue;
			if (x % (gridSize * 2) === gridSize && y % (gridSize * 2) === gridSize)
				continue;
			// Create a qubit
			const qubit = new Qubit(x, y, 5);
			workspace.addChild(qubit);
		}
	}
	let selectedQubits = [];
	const tile = new Tile();
	// Create the plaquettes
	const createPlaquette = (e) => {
		// Render the plaquette
		const plaquette = new Plaquette(selectedQubits); // Remove the container
		if (!plaquette.plaquetteMade) return;
		// Add the plaquette to the tile container
		tile.addChild(plaquette);
		tile.plaquette = plaquette;
		// Add the tile container to the workspace
		workspace.addChild(tile);
		// For each qubit, remove the text
		selectedQubits.forEach((qubit) => {
			qubit.removeChildren();
		});
		// Clear the selected qubits
		selectedQubits = [];
		// Hide the button
		button.visible = false;
		// Remove the text
	};

	// Create the button
	const button = Button('Create plaquette', 100, 100);
	button.on('click', createPlaquette);
	button.visible = false;

	// Select qubits
	const selectQubit = (e) => {
		// Check if the click was on a qubit
		const canvasRect = app.view.getBoundingClientRect(); // Get canvas position

		// Calculate the relative click position within the canvas
		const relativeX = e.clientX - canvasRect.left;
		const relativeY = e.clientY - canvasRect.top;
		// Get all the qubits
		const qubits = workspace.children.filter((child) => child.isQubit === true);
		const qubit = qubits.find(
			// Find the qubit that was clicked
			(qubit) => qubit.checkHitArea(relativeX, relativeY) === true
		);
		if (!qubit && !(qubit?.isQubit === true)) return; // Check that the qubit exists
		// Check that the qubit is not already selected
		if (selectedQubits.includes(qubit)) {
			// Remove the qubit from the selected qubits
			selectedQubits = selectedQubits.filter((q) => q !== qubit);
			// Hide the button
			button.visible = false;
			return;
		}
		selectedQubits.push(qubit);
		if (selectedQubits.length > 2) {
			// Show the button
			button.visible = true;
		}
	};

	workspace.addChild(button);
	workspace.visible = true;
	app.view.addEventListener('click', selectQubit);
	app.stage.addChild(workspace);
	return;
}
