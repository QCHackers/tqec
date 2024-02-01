// Define class Plaquette and its methods

import { Graphics, Color } from 'pixi.js';
import { convexHull } from './utils'

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
        //this._createRectangle();
	    this._createConvexHull();
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
        });
		// Create a rectangle
		this.beginFill(this.color);
		this.drawRect(xmin, ymin, xmax-xmin, ymax-ymin);
		this.endFill();

		// Add hover event
		this.on('pointerover', this._onPointerOver);
		this.on('pointerout', this._onPointerOut);
	};

	/**
	 * Create the convex hull using the naive algorithm
     * 
     * Start from a verical line left to the qubits.
     * Then 
	 */
	_createConvexHull() {
        // Convert the qubits in coordinate points
        let points = []
        this.qubits.forEach(qubit => {
            points.push({x: qubit.globalX, y: qubit.globalY});
        });
        const hull = convexHull(points)

        // Draw convex hull
		this.beginFill(this.color);
        this.lineStyle(1, this.color);
        this.moveTo(hull[0].x, hull[0].y);
        for (let i = 1; i < hull.length; i++) {
            this.lineTo(hull[i].x, hull[i].y);
        }
        this.lineTo(hull[0].x, hull[0].y);
		this.endFill();
	};
}
