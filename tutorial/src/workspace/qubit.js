// Define class Qubit and its methods

import { Text } from 'pixi.js'
import Position from './position'

/////////////////////////////////////////////////////////////

/**
 * Qubit class
 * @extends Position
 * @constructor
 * @param {number} x - The x position of the qubit
 * @param {number} y - The y position of the qubit
 * @param {number} radius - The radius of the circle representing the qubit
 * @param {number} color - Color filling the circle
 * @param {number} gridSize - Size of the underlying grid
 */
export default class Qubit extends Position {
	constructor(x, y, radius = 5) {
		super();
		// Color properties (as static fields).
		// Associated to the role played by the qubit.
		Qubit.color_none = 'white'
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
		this.factor = 2; // To expand the hitarea.
		this._createCircle(x, y, radius, Qubit.color_none);
		// QC properties
		this.role = 'none';
	}

    changeColor(color) {
		this.clear();
		this._createCircle(this.globalX, this.globalY, this.radius, color);
	}

	select() {
		if (this.role === 'none') {
		    this.role = 'x';
			this.changeColor(Qubit.color_x);
			this.name = this.name.replace(/[QZA]/g, 'X');
		} else if (this.role === 'x') {
		    this.role = 'z';
			this.changeColor(Qubit.color_z);
			this.name = this.name.replace(/[QXA]/g, 'Z');
		} else if (this.role === 'z') {
		    this.role = 'a';
			this.changeColor(Qubit.color_a);
			this.name = this.name.replace(/[QXZ]/g, 'A');
		} else if (this.role === 'a') {
		    this.role = 'none';
			this.changeColor(Qubit.color_none);
			this.name = this.name.replace(/[ZXA]/g, 'Q');
		};
		this.updateLabel();
	}

	updateLabel() {
		this.removeChildren();
		// Create the label as a text element 
		const label = new Text(this.name, {fill: Qubit.color_none, fontSize: 16, fontWeight: 'bold',});
		label.anchor.set(0.5);

		label.position.set(this.globalX, Math.max(this.globalY - 17, 13));
		//this._onPointerOver();
		// Add the label to the qubit
		this.addChild(label);
	}
}