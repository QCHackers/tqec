// Define class Qubit and its methods

import { Graphics, Text } from 'pixi.js'

/////////////////////////////////////////////////////////////

/**
 * Qubit class
 * @extends Graphics
 * @constructor
 * @param {number} x - The x position of the qubit
 * @param {number} y - The y position of the qubit
 * @param {number} radius - The radius of the circle representing the qubit
 * @param {number} color - Color filling the circle
 * @param {number} gridSize - Size of the underlying grid
 */
export default class Qubit extends Graphics {
	constructor(x, y, radius = 5, color = 'orange') {
		super();
		// UI properties
		this.eventMode = 'static';
		this.buttonMode = true;
		this.cursor = 'pointer';
		this.globalX = x;
		this.globalY = y;
		this._createCircle(x, y, radius, color);
		this.maxNeighborDist = 2 * this.gridSize;
		this.neighbors = [];
		// Adjacent (degree 1) qubits
		// QC properties
		this.isQubit = true;
		this.isSelected = false;
	}

	_onPointerOver = () => {
		this.alpha = 0.5;
	};

	_onPointerOut = () => {
		this.alpha = 1;
	};

    	/**
	 * Creates a circle
	 * @param {*} x
	 * @param {*} y
	 * @param {*} radius
	 * @param {*} color
	 */
	_createCircle(x, y, radius, color) {
		// Create a circle
		this.beginFill(color);
		this.drawCircle(x, y, radius);
		this.endFill();

		// Add hover event
		this.on('pointerover', this._onPointerOver);
		this.on('pointerout', this._onPointerOut);
	}

    changeColor(color) {
		this.clear();
		this._createCircle(this.globalX, this.globalY, 5, color);
	}

	select() {
		this.on('click', () => {
			if (this.isSelected === true) {
				this.isSelected = false;
				this.changeColor('red');
				this.removeChildren();
			}
            else {
                this.isSelected = true;
				this.changeColor(this.color);
            }
		});
	}
}