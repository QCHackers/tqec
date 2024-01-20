import { useApp } from '@pixi/react';
import { Container } from 'pixi.js';
import { AdjustmentFilter } from 'pixi-filters';
import { makeGrid } from './grid';
import Qubit from './QubitClass';
import Tile from './TileClass';
import { button } from './components/button';
import axios from 'axios';

const assert = require('assert');
// TODO: move this to a config file
const prodBackendURL = "https://tqec-app-mvp.uc.r.appspot.com";
const testingBackendURL = { // Default values from Flask
	ip: "127.0.0.1",
	port: "5000",
}

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
		workspace.removeChild(plaquette);
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
	const plaquetteButton = button('Create plaquette', 100, 100);
	plaquetteButton.on('click', (_e) => {
		// Create the plaquettes and tile
		const tile = new Tile(selectedQubits, app);
		tile.createPlaquette();
		tile.container.isTile = true;
		workspace.addChild(tile.container);
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
		if (selectedQubits.length > 2) {
			// Show the button
			plaquetteButton.visible = true;
		}
	};

	workspace.addChild(plaquetteButton);

	// Add download stim button
	const downloadStimButton = button('Download Stim file', 100, 50, 'white', 'black');
	const localTesting = !window.location.href.includes("https://"); // FIXME: this is a hack
	const stimURL = `${localTesting ? `http://${testingBackendURL.ip}:${testingBackendURL.port}` : prodBackendURL}/stim`;

	downloadStimButton.on('click', (_e) => {
		const payload = {plaquettes: []};
		const tiles = workspace.children.filter((child) => child.isTile);
		tiles.forEach((tile) => {
			const _plaquette = {
				color: tile.plaquette.color.toUint8RgbArray(),
				qubits: [],
				layers: []
			}
			const originQubit = tile.plaquette.qubits.toSorted((a, b) => a.globalX - b.globalX)	// leftmost qubits
				.toSorted((a, b) => a.globalY - b.globalY)[0]; // topmost qubit
			tile.plaquette.qubits.forEach((qubit) => {
				assert(qubit.qubitType === "data" || qubit.qubitType === "syndrome",
					"Qubit type must be either 'data' or 'syndrome'")
				_plaquette.qubits.push({
					x: (originQubit.globalX - qubit.globalX) / gridSize,
					y: (originQubit.globalY - qubit.globalY) / gridSize,
					qubitType: qubit.qubitType
				})
			});
			payload.plaquettes.push(_plaquette);
		});
		axios({
			method: 'POST',
			url: stimURL,
			data: JSON.stringify(payload),
			headers: {
				'Content-Type': 'application/json',
				'Data-Type': 'json',
			},
			responseType: 'blob'
		}).then((res) => {
			// create file link in browser's memory
			const href = URL.createObjectURL(res.data);
			// create "a" HTML element with href to file & click
			const link = document.createElement('a');
			link.href = href;
			link.setAttribute('download', 'circuit.json'); //or any other extension
			document.body.appendChild(link);
			link.click();
			// clean up "a" element & remove ObjectURL
			document.body.removeChild(link);
			URL.revokeObjectURL(href);
		}).catch((err) => {
			console.log(err);
		});
	});

	workspace.addChild(downloadStimButton);
	workspace.visible = true;
	app.view.addEventListener('click', selectQubit);
	app.stage.addChild(workspace);

	return;
}
