import { useApp } from '@pixi/react';
import { Container } from 'pixi.js';
import { AdjustmentFilter } from 'pixi-filters';
import { makeGrid } from './grid';
import Qubit from './QubitClass';
import TileClass from './TileClass';
import { Button, DownloadButton } from './components/button';
import { Plaquette } from './plaquettes/PlaquetteClass';

export default function TQECApp() {
	// Initialize the app
	let app = useApp();
	// Remove all children from the stage to avoid rendering issues
	app.stage.removeChildren();
	const gridSize = 50;
	// Let's create the workspace
	const workspace = new Container();
	workspace.name = 'workspace';
	// Create the grid container
	const grid = makeGrid(app, gridSize);

	workspace.addChild(grid);
	workspace.selectedPlaquette = null; // Used to update filters
	workspace.gridSize = gridSize;

	workspace.updateSelectedPlaquette = (newPlaquette) => {
		if (newPlaquette === null) {
			return;
		}
		const currentPlaquette = workspace.selectedPlaquette;
		if (currentPlaquette === newPlaquette) {
			currentPlaquette.filters = null;
			workspace.removeChild(workspace.getChildByName('control_panel'));
			workspace.selectedPlaquette = null;
		} else {
			if (currentPlaquette != null) {
				currentPlaquette.filters = null;
			}
			newPlaquette.filters = [new AdjustmentFilter({contrast: 0.5})]
			workspace.removeChild('control_panel')
			workspace.addChild(newPlaquette.controlPanel);
			workspace.selectedPlaquette = newPlaquette;
		}
	}

	workspace.removePlaquette = (plaquette) => {
		if (plaquette === null) {
			return;
		}
		if (workspace.selectedPlaquette === plaquette) {
			workspace.selectedPlaquette = null;
		}
		// Remove control panel if it is visible
		const currentControlPanel = workspace.getChildByName('control_panel');
		if (currentControlPanel === plaquette.controlPanel) {
			workspace.removeChild(currentControlPanel);
		}
		workspace.children.filter((child) => child instanceof TileClass).forEach((tile) => {
			if (tile.getPlaquettes().includes(plaquette)) {
				tile.removeChild(plaquette);
			}
		});
		plaquette.destroy({ children: true });
	}

	// Add the qubits to the workspace
	for (let x = 0; x <= app.renderer.width; x += gridSize) {
		for (let y = 0; y <= app.renderer.height; y += gridSize) {
			// Skip every other qubit
			if (x % (gridSize * 2) === 0 && y % (gridSize * 2) === 0) continue;
			if (x % (gridSize * 2) === gridSize && y % (gridSize * 2) === gridSize)
				continue;
			// Create a qubit
			const qubit = new Qubit(x, y, 5, gridSize);
			// Name the qubit according to its position
			qubit.name = `${x}_${y}`;
			workspace.addChild(qubit);
		}
	}
	// Give the qubit its neighbors
	for (const q in workspace.children) {
		if (workspace.children[q].isQubit === true) {
			workspace.children[q].setNeighbors();
		}
	}

	let selectedQubits = [];
	// Create the button
	const plaquetteButton = new Button('Create plaquette', 100, 100);
	plaquetteButton.on('click', (_e) => {
		// Create the plaquettes and tile
		const tile = new TileClass([new Plaquette(selectedQubits, workspace)], workspace);
		workspace.addChild(tile);
		// Clear the selected qubits
		selectedQubits = [];
		// Hide the button
		plaquetteButton.visible = false;
	});
	plaquetteButton.visible = false;

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
			plaquetteButton.visible = false;
			return;
		}
		selectedQubits.push(qubit);
		selectedQubits.forEach((qubit) => {
			qubit.visible = true;
		});
		if (selectedQubits.length > 2) {
			// Show the button
			plaquetteButton.visible = true;
		}
	};
	workspace.addChild(plaquetteButton);

	// Add download stim button
	const downloadStimButton = new DownloadButton(workspace, 'Download Stim file', 100, 50, 'white', 'black');
	workspace.addChild(downloadStimButton);

	// Final workspace setup
	workspace.visible = true;
	app.view.addEventListener('click', selectQubit);
	app.stage.addChild(workspace);

	return;
}
