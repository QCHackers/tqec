import { Container } from 'pixi.js';
import { Plaquette, PlaquetteColors } from './plaquettes/PlaquetteClass';

export default class Tile extends Container {
	constructor(plaquettes, workspace) {
		super();
		// UI Properties
		this.buttonMode = true;
		this.cursor = 'pointer';
		this.mode = 'static';
		this.isDragging = false;
		this.prevMouseX = 0;
		this.prevMouseY = 0;
		this.workspace = workspace;
		// Add the plaquette to the tile
		plaquettes.forEach((plaquette) => {
			this.addChild(plaquette);
		});
	}

	createPlaquetteFromControlPanel = () => {
		// Create the plaquette
		const plaquette = new Plaquette(this.selectedQubits, this.workspace, PlaquetteColors.purple);
		if (!plaquette.plaquetteMade) return;
		// Add the plaquette to the tile container
		this.addChild(plaquette);
	};

	getPlaquettes = () => {
		return this.children.filter((child) => child instanceof Plaquette);
	}

}
