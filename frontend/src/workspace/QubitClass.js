import { Graphics, Text } from 'pixi.js';

/**
 * Qubit class
 * @extends Graphics
 * @constructor
 * @param {number} x - The x position of the qubit
 * @param {number} y - The y position of the qubit
 */
export default class Qubit extends Graphics {
	constructor(x, y, radius = 5, gridSize = 50, color = 'black',  qubitType = 'data') {
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
		this.gridSize = gridSize;
		this.qubitType = qubitType;

		// Adjacent (degree 1) qubits
		this.isQubit = true;
		this.visible = true;
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
		// this.hitArea = new Circle(x, y, radius);
		this.endFill();

		// Add hover event
		this.on('pointerover', this._onPointerOver);
		this.on('pointerout', this._onPointerOut);
	}

	changeColor(color) {
		this.clear();
		this._createCircle(this.globalX, this.globalY, 5, color);
	}

	deselect() {
		this.on('click', () => {
			if (this.isSelected === true) {
				this.isSelected = false;
				this.changeColor('black');
				this.removeChildren();
			}
		});
	}
	checkHitArea(eventX, eventY, threshold = 5) {
		// Calculate the distance between event coordinates and qubit's global position
		const distance = Math.sqrt(
			Math.pow(eventX - this.globalX, 2) + Math.pow(eventY - this.globalY, 2)
		);
		// Define a threshold to determine the hit area
		if (distance <= threshold) {
			// If there is already a text element, don't create another one
			if (this.children.length > 0) {
				this.deselect();
				return true;
			}
			this.isSelected = true;
			// Create a text element
			const text = new Text(`Qubit:(${this.globalX},${this.globalY})`, {
				fill: 'white',
				fontSize: 10,
			}); // White text color
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

	/**
	 * Find neighbors of the qubit
	 * There are 4 neighbors, top, bottom, left, right, does not consider diagonal neighbors
	 */
	setNeighbors = () => {
		// Get surrounding qubits, this is specific to the grid we have built, needs to be generalized to find qubits within a maxDistance efficiently
		const topQubitPos = {
			x: this.globalX,
			y: this.globalY - 2 * this.gridSize,
		};
		const bottomQubitPos = {
			x: this.globalX,
			y: this.globalY + 2 * this.gridSize,
		};
		const leftQubitPos = {
			x: this.globalX - 2 * this.gridSize,
			y: this.globalY,
		};
		const rightQubitPos = {
			x: this.globalX + 2 * this.gridSize,
			y: this.globalY,
		};
		// For readability
		const neighborArr = [
			topQubitPos,
			bottomQubitPos,
			leftQubitPos,
			rightQubitPos,
		];
		// console.log(this.parent.children[100]);
		for (const q in neighborArr) {
			// Check if the qubit is within the workspace
			const qubit = this.parent.getChildByName(
				`${neighborArr[q].x}_${neighborArr[q].y}`
			);
			if (qubit) {
				// Set the neighbors
				this.neighbors.push(qubit);
			}
		}
		// console.log(this.neighbors);
		return this.neighbors;
	};

	hideQubitLabels = () => {
		this.children.forEach((child) => {
			if (child instanceof Text) {
				child.visible = false;
			}
		});
	}
}
