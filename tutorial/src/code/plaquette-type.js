// Define class Plaquette and its methods

//import { Graphics } from 'pixi.js';
import { Qubit } from '../library/qubit.js';
//import Circuit from './circuit'
import Plaquette from '../library/plaquette';

/////////////////////////////////////////////////////////////

/**
 * Plaquette class
 * @extends Graphics
 * @constructor
 * @param {array} qubits - The qubits which are part of the plaquette
 * @param {color} color - Color filling of the plaquette
 */
export default class PlaquetteType extends Plaquette {
    constructor(qubits, color = 'purple') {
        super(qubits, color);
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

        // Create a copy of the plaquette at the current position
        let qubits_of_copy = []
		this.qubits.forEach((q) => {
            const qubit = new Qubit(q.globalX + this.x,
                                    q.globalY + this.y,
                                    q.radius);
            qubits_of_copy.push(qubit);
        });
        const copy = new Plaquette(qubits_of_copy, this.color);
	    copy._createConvexHull();
        this.parent.addChild(copy);

        // Reset the position of the original plaquette
        console.log(`move back to the start position = ${this.startPosition}`);
        this.x = 0;
        this.y = 0;
    }

}
