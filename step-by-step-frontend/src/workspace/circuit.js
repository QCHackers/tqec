import { Text, Container, Graphics } from 'pixi.js';

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
export default class Circuit extends Container {
	constructor(qubits, x, y) {
		super();
		// Color properties (as static fields).
		// Associated to the role played by the qubit.
		Circuit.color_background = 'white'
		Circuit.color = 'black'
		// UI properties
		this.globalX = x;
		this.globalY = y;
		this.isCompatible = true;
		//this.anc_qubit;
		this.data_qubits = [];
		this._confirmFormat(qubits);
		if (this.isCompatible === true) {
			this._createBackground();
			this._createCircuit();
		}
	}

	/**
	 * Confirm format of the plaquette, constraining the type of circuit
	 * - there is a unique ancilla qubit
	 * - all other qubits are associated with either X- or Z-stabilizers
	 * - all data qubits are assumed connected to the ancilla qubit
	 *   (i.e. they can be involved in 2q gates)
	 */
	_confirmFormat(qubits) {
		this.isCompatible = true;
		let numAncillas = 0;
        qubits.forEach(qubit => {
            if (qubit.role === 'a') {
				numAncillas += 1;
				this.anc_qubit = qubit;
			} else if (qubit.role !== 'z' && qubit.role !== 'x') {
				this.isCompatible = false;
			} else {
				this.data_qubits.push(qubit);
			}
        });
		if (numAncillas !== 1) {
			this.isCompatible = false;
		}
	}

	/**
	 * Create the circuit as ASCII art
	 */
	_createCircuit() {
		let lines = [''];
		// Add lines for every data qubit.
		let idx = 0;
        this.data_qubits.forEach(qubit => {
			let line = `|${qubit.name}> --`
			// Local change of basis
			if (qubit.role === 'x') line = line + 'H--';
			if (qubit.role === 'z') line = line + '---';
			// Previous CNOTs
			for (let i = 0; i<idx; i++) {
				line = line + '|--';
			}
			// Current CNOT
			line = line + '*--'
			// Next CNOTs
			for (let i = idx+1; i<this.data_qubits.length; i++) {
				line = line + '---';
			}
			// Change of basis
			if (qubit.role === 'x') line = line + 'H--';
			if (qubit.role === 'z') line = line + '---';
			// End
			line = line + '---'
			lines.push(line);
			idx += 1;
		});
		// Add line for the ancilla qubit.
		let line = `|${this.anc_qubit.name}> --`
		line = line + '---'; // Change of basis
		for (let i = 0; i<this.data_qubits.length; i++) {
			line = line + 'x--';
		}
		line = line + '--- D~'
		lines.push(line);
		// Create the message
		let message = '';
        lines.forEach(line => {
			message = message + line + '\n';
		});
		// Create the graphics
		const artText = new Text(message,
			{
				fontFamily: 'monospace',
				fontSize: 15,
				fill: Circuit.color, // White color
				align: 'left',
				wordWrap: true,
				wordWrapWidth: 300, // Set the maximum width for word wrapping
			}
		);
		// Set the position of the text
		artText.position.set(this.globalX, this.globalY);
		// Add the text object to the stage
		this.addChild(artText);
	}

	/**
	 * Creates a rectangle enclosing the circuit
	 */
	_createBackground() {
		const artBackground = new Graphics();
        // Locate corners
        const dx = 400
        const dy = 130; //4 + this.data_qubits.length * 24
		// Create a rectangle
		artBackground.beginFill(Circuit.color_background);
		artBackground.drawRoundedRect(this.globalX-15, this.globalY, dx, dy);
		artBackground.endFill();
		this.addChild(artBackground);
	};
};
