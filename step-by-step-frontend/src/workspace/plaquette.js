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
 * @param {number} workspace - The container to which we add the plaquette as child
 * @param {Color} color - Color filling of the plaquette
 */
export default class Plaquette extends Graphics {
    constructor(qubits, workspace, color = PlaquetteColors.purple) {
        super();
        // UI properties
        this.workspace = workspace;
        this.color = color;
        this.gridSize = workspace.gridSize;
        this.gridOffsetX = this.gridSize;
        this.gridOffsetY = this.gridSize;
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
        let xmin = 0
        let xmax = 100000
        let ymin = 0
        let ymax = 100000
        this.qubits.forEach(qubit => {
            let x = qubit.xGlobal;
            if (x < xmin) xmin = x;
            if (x > xmax) xmax = x;
            let y = qubit.yGlobal;
            if (y < ymin) ymin = y;
            if (y > ymax) ymax = y;
        });
		// Create a circle
		this.beginFill(this.color);
		this.drawRect(xmin, ymin, xmax, ymax);
		this.endFill();

		// Add hover event
		this.on('pointerover', this._onPointerOver);
		this.on('pointerout', this._onPointerOut);
	};
}
