import { Graphics, Circle, Text } from 'pixi.js';

/**
 * Qubit class
 * @extends Graphics
 * @constructor
 * @param {number} x - The x position of the qubit
 * @param {number} y - The y position of the qubit
 */
export default class Qubit extends Graphics {
	constructor(x, y, radius = 5, color = 0x000000) {
		super();
		// UI properties
		this.eventMode = 'static';
		this.buttonMode = true;
		this.cursor = 'pointer';
		this.globalX = x;
		this.globalY = y;
		this._createCircle(x, y, radius, color);
		// QC properties
		this.quantumState = '0'; // NOTE: In javascript, becareful updating values such as "this", "state", etc.
		this.qubitType = 'data'; // data or measurement
		this.neighbors = [];
		this.isQubit = true;
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
		// this.hitArea = new Circle(x, y, radius);
		this.endFill();

		// Add hover event
		this.on('pointerover', this._onPointerOver);
		this.on('pointerout', this._onPointerOut);
	}

	checkHitArea(eventX, eventY, threshold = 5) {
		// Calculate the distance between event coordinates and qubit's global position
		const distance = Math.sqrt(
			Math.pow(eventX - this.globalX, 2) + Math.pow(eventY - this.globalY, 2)
		);

		// Define a threshold to determine the hit area
		if (distance <= threshold) {
			console.log('distance', distance);
			// Create a text element
			if (this.children.length > 0) return true; // If there is already a text element, don't create another one
			const text = new Text('Sample Text', { fill: 'white', fontSize: 10 }); // White text color
			text.anchor.set(0.5);
			text.position.set(eventX, eventY + 10);
			this._onPointerOver();
			this.color = 0xffffff;

			// Add the text to the qubit
			this.addChild(text);

			return true;
		}
		return false; // If no hit
	}

	/**
	 * Sets the qubit state
	 * @param {*} state
	 */
	setQuantumState(state) {
		this.quantumState = state;
	}
}
