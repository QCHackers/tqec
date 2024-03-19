// Define class Plaquette and its methods

import { Qubit } from '../library/qubit';
import Position from '../library/position';
import Plaquette from '../library/plaquette';
import { GRID_SIZE_CODE_WORKSPACE, GUIDE_MAX_BOTTOM_RIGHT_CORNER_CODE_WORKSPACE, GUIDE_TOP_LEFT_CORNER_CODE_WORKSPACE } from '../constants';

/////////////////////////////////////////////////////////////

/**
 * Plaquette class
 * @extends Graphics
 * @constructor
 * @param {array} qubits - The qubits which are part of the plaquette
 * @param {color} color - Color filling of the plaquette
 * @param {num_background_children} num_background_children - Used to place the latest plaquette on top of the workspace background but below every other elements
 * @param {base_translate_vector} base_translate_vector - Used to confirm that the latest plaquette is snapped to a cell
 */
export default class PlaquetteType extends Plaquette {
    constructor(qubits, color = 'purple', num_background_children = -1, base_translate_vector = {x:0, y:0}) {
        super(qubits, color);
        this.add_at = num_background_children;
        this.base_translate_vector = base_translate_vector;
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
        // If the translator vector does not lead to a cell, log an error and return.
		const plaquetteDx = parseInt(document.getElementById('dxCell').value);
		const plaquetteDy = parseInt(document.getElementById('dyCell').value);
        console.log('this.base_translate_vector = ', this.base_translate_vector[0])
        // Horizontally aligned with a cell.
        let is_valid_translation = (translate_x/GRID_SIZE_CODE_WORKSPACE - this.base_translate_vector.x) % plaquetteDx === 0;
        // Vertically aligned with a cell.
        is_valid_translation = is_valid_translation && (translate_y/GRID_SIZE_CODE_WORKSPACE - this.base_translate_vector.y) % plaquetteDy === 0; 
        // Horizontally within the cells in the guide.
        is_valid_translation = is_valid_translation && (translate_x/GRID_SIZE_CODE_WORKSPACE - this.base_translate_vector.x) + plaquetteDx <= GUIDE_MAX_BOTTOM_RIGHT_CORNER_CODE_WORKSPACE[0] - GUIDE_TOP_LEFT_CORNER_CODE_WORKSPACE[0];
        is_valid_translation = is_valid_translation && (translate_x/GRID_SIZE_CODE_WORKSPACE - this.base_translate_vector.x) >= 0;
        // Vertically within the cells in the guide.
        is_valid_translation = is_valid_translation && (translate_y/GRID_SIZE_CODE_WORKSPACE - this.base_translate_vector.y) + plaquetteDy <= GUIDE_MAX_BOTTOM_RIGHT_CORNER_CODE_WORKSPACE[1] - GUIDE_TOP_LEFT_CORNER_CODE_WORKSPACE[1];
        is_valid_translation = is_valid_translation && (translate_y/GRID_SIZE_CODE_WORKSPACE - this.base_translate_vector.y) >= 0;
        if ( is_valid_translation === false ) {
            console.log('WARNING: Wrong translation for plaquette -> rejected')
            // Reset the position of the original plaquette
            this.x = 0;
            this.y = 0;
            return;
        }
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
        this.x = 0;
        this.y = 0;

        // Update the compact representation of teh QEC code
        const codesummary = document.getElementById('codeSummary');
        let message = codesummary.value.split('\n');
        let lines = message;
        console.log(lines)
		// Recall that plaquette names are like "plaquette 12", starting from "plaquette 1"
		const plaquette_id = parseInt(this.name.match(/\d+/)[0]);
        const col = (translate_x/GRID_SIZE_CODE_WORKSPACE - this.base_translate_vector.x) / plaquetteDx;
        const row = (translate_y/GRID_SIZE_CODE_WORKSPACE - this.base_translate_vector.y) / plaquetteDy;
        // TODO: Here we assume that there is a single space before every plaquette id is left padded with spaces
        console.log(row, col)
        let modifiedLine = lines[row].substring(0, 3*col) + `${String(plaquette_id).padStart(3, ' ')}` + lines[row].substring(3*col+3);
        lines[row] = modifiedLine;
        codesummary.value = lines.join('\n');
    }

}
