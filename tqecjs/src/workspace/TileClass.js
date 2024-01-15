import { Container } from 'pixi.js';
import { Plaquette, PlaquetteColors } from './plaquettes/PlaquetteClass';
import notification from './components/notifier';

export default class Tile {
	constructor(selectedQubits, app) {
		// UI Properties
		this.container = new Container();
		this.buttonMode = true;
		this.cursor = 'pointer';
		this.mode = 'static';
		this.isDragging = false;
		this.prevMouseX = 0;
		this.prevMouseY = 0;
		this.app = app;

		// Quantum
		this.selectedQubits = selectedQubits || [];
		this.plaquette = null;

		this.isTile = true;
	}

	makeTile() {
		// Get the plaquette
		if (this.plaquette) {
			this.container.addChild(this.plaquette.onDragMove());
		} else {
			notification(this.container, this.app);
		}
	}

	// Create the plaquettes that are assigned to the tile
	createPlaquette = () => {
		const workspace = this.app.stage.getChildByName('workspace');
		// Render the plaquette
		const plaquette = new Plaquette(this.selectedQubits, workspace, 50, PlaquetteColors.purple); // Remove the container
		if (!plaquette.plaquetteMade) return;
		// Add the plaquette to the tile container
		this.container.addChild(plaquette);
		this.container.plaquette = plaquette;
		// For each qubit, remove the text
		this.selectedQubits.forEach((qubit) => {
			qubit.removeChildren();
		});
	};
}
