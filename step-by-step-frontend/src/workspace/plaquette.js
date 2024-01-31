// Define class Plaquette and its methods

import { Graphics, Color } from 'pixi.js';

/////////////////////////////////////////////////////////////

export const PlaquetteColors = {
  purple: new Color('purple'),
  yellow: new Color('yellow'),
};

/////////////////////////////////////////////////////////////

/**
 * Plaquette class
 * @extends Graphics
 * @constructor
 * @param {array} qubits - The qubits which are part of the plaquette
 * @param {Color} color - Color filling of the plaquette
 */
export default class Plaquette extends Graphics {
    constructor(qubits, color = PlaquetteColors.purple) {
        super();
        // UI properties
        this.color = color;
        this.qubits = qubits
        //this.isDragging = false;
        //this.plaquetteMade = false;
        this.name = 'plaquette';
        // Draw the plaquette
        // TODO: Only rectangular plaquettes, at the moment
        this._createRectangle();
    };

	_onPointerOver = () => {
		this.alpha = 0.5;
	};

	_onPointerOut = () => {
		this.alpha = 1;
	};

	/**
	 * Creates a rectangle enclosing the qubits
	 */
	_createRectangle() {
        // Locate corners
        let xmin = 10000
        let xmax = 0
        let ymin = 10000
        let ymax = 0
        this.qubits.forEach(qubit => {
            let x = qubit.globalX;
            if (x < xmin) xmin = x;
            if (x > xmax) xmax = x;
            let y = qubit.globalY;
            if (y < ymin) ymin = y;
            if (y > ymax) ymax = y;
            console.log(x,y)
        });
        console.log(xmin, ymin, xmax, ymax)
		// Create a rectangle
		this.beginFill(this.color);
		this.drawRect(xmin, ymin, xmax-xmin, ymax-ymin);
		this.endFill();

		// Add hover event
		this.on('pointerover', this._onPointerOver);
		this.on('pointerout', this._onPointerOut);
	};
}
