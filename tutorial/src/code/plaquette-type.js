// Define class Plaquette and its methods

//import { Graphics } from 'pixi.js';
import { Qubit } from '../library/qubit';
import Position from '../library/position';
//import Circuit from './circuit'
import Plaquette from '../library/plaquette';

/////////////////////////////////////////////////////////////

/**
 * Plaquette class
 * @extends Graphics
 * @constructor
 * @param {array} qubits - The qubits which are part of the plaquette
 * @param {color} color - Color filling of the plaquette
 * @param {num_background_children} num_background_children - Used to place the latest plaquette on top of the workspace background but below every other elements
 */
export default class PlaquetteType extends Plaquette {
    constructor(qubits, color = 'purple', num_background_children = -1) {
        super(qubits, color);
        this.add_at = num_background_children;
        this.interactive = true;
        this.buttonMode = true;
        this.on('pointerdown', this.onDragStart)
            .on('pointerup', this.onDragEnd)
            .on('pointerupoutside', this.onDragEnd)
            .on('pointermove', this.onDragMove);

        // Store initial drag position
        this.dragging = false;
        this.dragData = null;
        this.startPosition = { x: 0, y: 0 };
    };

	/**
	 * Implementation of the behavior when the plaquettes are dragged
	 */
    onDragStart(event) {
        // Store initial drag position
        this.dragging = true;
        this.dragData = event.data;
        this.startPosition = this.dragData.getLocalPosition(this.parent);
        console.log(`start position of drag = ${this.startPosition}`);
        console.log(`while the global (x,y) of the first qubit are = (${this.qubits[0].globalX}, ${this.qubits[0].globalY})`);
        this.alpha = 0.5;
    }

    onDragMove() {
        if (this.dragging) {
            const newPosition = this.dragData.getLocalPosition(this.parent);
            this.x = newPosition.x - this.startPosition.x;
            this.y = newPosition.y - this.startPosition.y;
        }
    }

    onDragEnd() {
        this.dragging = false;
        this.alpha = 1;
        console.log(`overall move is (dx,dy) = (${this.x}, ${this.y})`);

        // Find the closest position to the first qubit.
        // Use it to compute the expected translation vector.
        let temp_x = this.qubits[0].globalX + this.x;
        let temp_y = this.qubits[0].globalY + this.y;
        let min_distance = 10000;
        let translate_x = 0;
        let translate_y = 0;
	    this.parent.children.forEach((child) => {
	        if (child instanceof Position) {
                const d = (temp_x-child.globalX)**2 + (temp_y-child.globalY)**2;
                if (d < min_distance) {
                    min_distance = d;
                    translate_x = child.globalX - this.qubits[0].globalX;
                    translate_y = child.globalY - this.qubits[0].globalY;
                }
            }
        });
        // If the translator vector does not lead to cell, log an error and return.

        // Create a copy of the plaquette at the current position.
        let qubits_of_copy = []
		this.qubits.forEach((q) => {
            const qubit = new Qubit(q.globalX + translate_x, q.globalY + translate_y, q.radius);
            qubits_of_copy.push(qubit);
        });
        const copy = new Plaquette(qubits_of_copy, this.color);
	    copy._createConvexHull(0);
        if (this.add_at >= 0) {
            this.parent.addChildAt(copy, this.add_at);
        }

        // Reset the position of the original plaquette
        console.log(`move back to the start position = ${this.startPosition}`);
        this.x = 0;
        this.y = 0;
    }

}
