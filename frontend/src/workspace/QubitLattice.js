import Qubit from './QubitClass';


const assert = require('assert');

export default class QubitLattice {
    constructor(vector1, vector2, constellation) {
        assert(constellation.length > 0, 'Constellation must have at least one qubit');
        assert(!vector1.parallelTo(vector2), 'Vectors must not be parallel');
    }
}

export class Vector extends Array {
    constructor(x, y) {
        super(x, y);
    }
    parallelTo(vector) {
        return this[0] * vector[1] - this[1] * vector[0] === 0;
    }
}
