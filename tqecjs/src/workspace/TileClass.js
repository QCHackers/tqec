import { Graphics } from 'pixi.js';

export default class Tile extends Graphics {
	constructor(plaquette) {
		super();
		this.plaquette = plaquette;
		this.isDragging = false;
		this.prevMouseX = 0;
		this.prevMouseY = 0;
	}
	_onDragStart(event) {
		this.isDragging = true;
	}

	_onDragMove(event) {
		if (this.isDragging) {
			// Determine which position the pointer is moving to
			const currentMouseX = event.data.global.x;
			const currentMouseY = event.data.global.y;
			// Calculate the change in mouse position
			const deltaX = currentMouseX - this.prevMouseX;
			const deltaY = currentMouseY - this.prevMouseY;

			// Update the previous mouse position
			this.prevMouseX = currentMouseX;
			this.prevMouseY = currentMouseY;

			// Create a new plaquette
			// Get the leftmost qubit

			if (
				deltaX > 0 &&
				currentMouseX > this.plaquette.mostRightQubit().globalX
			) {
				console.log('Mouse is moving right');
				// Get the selected qubits
				const newPlaquette = this.plaquette.clone();
				// Set the new plaquette's position
				newPlaquette.position.set(
					this.plaquette.mostRightQubit().globalX + 50,
					this.plaquette.mostRightQubit().globalY
				);
				// Add the new plaquette to the workspace
				this.plaquette.parent.addChild(newPlaquette);
				// Remove the old plaquette
			} else if (deltaX < 0) {
				console.log('Mouse is moving left');
			}

			if (deltaY > 0) {
				console.log('Mouse is moving down');
			} else if (deltaY < 0) {
				console.log('Mouse is moving up');
			}
		}
	}

	makeTile() {
		this.on('pointerdown', this._onDragStart);
		this.on('pointermove', this._onDragMove);
	}
}
