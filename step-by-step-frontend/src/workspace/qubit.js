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
	constructor(x, y, radius = 5) {
		super();
		// Color properties (as static fields).
		// Associated to the role played by the qubit.
		Qubit.color_none = 'white'
		Qubit.color_selected = 'yellow'
		Qubit.color_x = 'blue'
		Qubit.color_z = 'red'
		Qubit.color_a = 'orange'
		// UI properties
		this.eventMode = 'static';
		this.buttonMode = true;
		this.cursor = 'pointer';
		this.globalX = x;
		this.globalY = y;
		this.radius = radius;
		this._createCircle(x, y, radius, Qubit.color_none);
		this.maxNeighborDist = 2 * this.gridSize;
		this.neighbors = [];
		// Adjacent (degree 1) qubits
		// QC properties
		this.isQubit = true;
		this.role = 'none';
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
		this._createCircle(this.globalX, this.globalY, this.radius, color);
	}

	select() {
		if (this.role === 'none') {
			this.role = 'selected';
			this.changeColor(Qubit.color_selected);
			this.name = this.name.replace(/[qxza]/g, 's');
		} else if (this.role === 'selected') {
		    this.role = 'x';
			this.changeColor(Qubit.color_x);
			this.name = this.name.replace(/[qsza]/g, 'x');
		} else if (this.role === 'x') {
		    this.role = 'z';
			this.changeColor(Qubit.color_z);
			this.name = this.name.replace(/[qsxa]/g, 'z');
		} else if (this.role === 'z') {
		    this.role = 'a';
			this.changeColor(Qubit.color_a);
			this.name = this.name.replace(/[qsxz]/g, 'a');
		} else if (this.role === 'a') {
		    this.role = 'none';
			this.changeColor(Qubit.color_none);
			this.name = this.name.replace(/[szxa]/g, 'q');
		};
		this.updateLabel();
	}

	updateLabel() {
		this.removeChildren();
		if (this.role === 'none')
			return;
		// Create the label as a text element 
		const label = new Text('S', {fill: Qubit.color_none, fontSize: 12,});
		if (this.role === 'x') {
			label.text = 'X';
			//label.tint = Qubit.color_x;
		} else if (this.role === 'z') {
			label.text = 'Z';
			//label.tint = Qubit.color_z;
		} else if (this.role === 'a') {
			label.text = 'A';
			//label.fill = Qubit.color_a;
		} else if (this.role === 'selected') {
			//label.fill = Qubit.color_selected;
		};
		label.anchor.set(0.5);

		label.position.set(this.globalX, Math.max(this.globalY - 15, 13));
		//this._onPointerOver();
		// Add the label to the qubit
		this.addChild(label);
	}
}