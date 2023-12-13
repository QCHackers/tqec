import { useApp } from '@pixi/react';
import { Container, Graphics } from 'pixi.js';
import { makeGrid } from './grid';
import Qubit from './QubitClass';
import Plaquette from './plaquettes/PlaquetteClass';

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
	const plaquetteContainer = new Container();
	// Create the plaquettes
	const createPlaquette = (e) => {
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
		if (selectedQubits.includes(qubit)) return;
		selectedQubits.push(qubit);
		// Render the plaquette
		const plaquette = new Plaquette(selectedQubits); // Remove the container
		if (!plaquette.plaquetteMade) return;
		// Add the plaquette to the plaquette container
		plaquetteContainer.addChild(plaquette);
		// // Add the plaquette container to the workspace
		workspace.addChild(plaquetteContainer);
	};

	app.renderer.view.addEventListener('click', createPlaquette);

	app.stage.addChild(workspace);
	return;
}
