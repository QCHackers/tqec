// Define functions to manipulate Plaquette objects

import Plaquette from '../tab_library/plaquette.js';
import { Qubit } from '../tab_library/qubit.js'

/**
 * Plaquette class
 * @param {Plaquette} plaquette - plaquette to copy
 * @param {Dict} translate - absolute translate vector (for the position of qubits and plaquette)
 * @param {float} gridSize - grid size (for the position of the qubits)
 * @param {Tuple} guideTopLeftCorner - absolute position of the top-left corner of the guide/template
 */
export function copyPlaquette(plaquette, translate, gridSize, guideTopLeftCorner) {
    // Create a copy of the plaquette at the current position.
    let qubits_of_copy = []
    plaquette.qubits.forEach((q) => {
        const qubit = new Qubit(q.globalX + translate.x * gridSize, q.globalY + translate.y * gridSize, q.radius);
        qubit.name = `Q(${String(qubit.globalX/gridSize - guideTopLeftCorner[0]).padStart(2, ' ')},${String(qubit.globalY/gridSize - guideTopLeftCorner[1]).padStart(2, ' ')})`;
        qubits_of_copy.push(qubit);
    });
    const copy = new Plaquette(qubits_of_copy, plaquette.color);
    copy.x += translate.x
    copy.y += translate.y
    copy._createConvexHull(0);
    copy.topLeftCorner = {x: translate.x + plaquette.topLeftCorner.x - guideTopLeftCorner[0],
                          y: translate.y + plaquette.topLeftCorner.y - guideTopLeftCorner[1]}
    return copy;
}