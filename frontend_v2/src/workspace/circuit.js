import { Text, Container, Graphics } from 'pixi.js';

/**
 * Create the circuit as ASCII art.
 * 
 * Two forms of circuits are possible:
 * 
 * [] "cnot"
 *    - Hadamard on the data qubits
 *    - only CNOT as 2q gates
 *    - every CNOT is controlled by a data qubit and targets the ancilla
 * 
 * [] "univ"
 *    - Hadamard on the ancilla qubit
 *    - both CNOT and CZ as 2q gates
 *    - every CNOT/CZ is controlled by the ancilla and targets a data qubit
 */
export function createCircuitAsciiArt(data_qubits, anc_qubit, with_time=true, form='univ') {
	if (form !== 'cnot') form = 'univ'; // Failsafe case of an unknown form option.
	let lines = [];
	// Add lines for every data qubit.
	let idx = 0;
	data_qubits.forEach(qubit => {
		let line = `${qubit.name}: ----`
		// Local change of basis
		if (form === 'cnot') {
		    if (qubit.role === 'x') line += '-H--';
		    if (qubit.role === 'z') line += '----';
		} else if (form === 'univ') {
		    line += '----';
		}
		// Previous CNOTs
		for (let i = 0; i<idx; i++) {
			line += '-|--';
		}
		// Current CNOT
		if (form === 'cnot') {
			line += '-*--'
		} else if (form === 'univ') {
		    if (qubit.role === 'x') line += '-X--';
		    if (qubit.role === 'z') line += '-*--';
		}
		// Next CNOTs
		for (let i = idx+1; i<data_qubits.length; i++) {
			line += '----';
		}
		// Change of basis
		if (form === 'cnot') {
		    if (qubit.role === 'x') line += '-H--';
		    if (qubit.role === 'z') line += '----';
		} else if (form === 'univ') {
		    line += '----';
		}
		// End
		line += '----';
		lines.push(line);

		// Empty line with only vertical bars.
		//      Q(__,__): ----
		line = '              ';
		line += '    ';
		// Previous CNOTs and current one
		for (let i = 0; i<idx+1; i++) {
			line += ' |  ';
		}
		// Next CNOTs
		for (let i = idx+1; i<data_qubits.length; i++) {
			line += '    ';
		}
		line += '        '
		lines.push(line);
		idx += 1;
	});
	// Add line for the ancilla qubit.
	let line = `${anc_qubit.name}: |0> `
	if (form === 'cnot') {
		line += '----'; // During the change of basis
	} else if (form === 'univ') {
		line += '-H--';
	}
	for (let i = 0; i<data_qubits.length; i++) {
		if (form === 'cnot') {
			line += '-X--';
		} else if (form === 'univ') {
			line += '-*--';
		}
	}
	if (form === 'cnot') {
		line += '---- D~ '
	} else if (form === 'univ') {
		line += '-H-- D~ ';
	}
	lines.push(line);
	// Add time ruler.
	if (with_time) {
		//      Q(__,__): 
		line = '          ';
		let line2 = 'time ruler';
		for (let i = 0; i<data_qubits.length+4; i++) {
			line += '___ ';
			line2 += ' ' + i + '  ';
		}
		lines.push(line);
		lines.push(line2);
	}
	// Create the message
	let art = '';
	lines.slice(0,-1).forEach(line => {
		art = art + line + '\n';
	});
	art += lines[lines.length-1];
	return art;
}



/**
 * Circuit class
 * @extends Container
 * @constructor
 * @param {array} qubits - The qubits involved in the circuit
 * @param {number} x - The x position of the circuit graphics
 * @param {number} y - The y position of the circuit graphics
 * @param {number} color - Color filling of the circuit
 */
export default class Circuit extends Container {
	constructor(qubits, x, y, color = 'purple', message = '') {
		super();
		// Color properties (as static fields).
		// Associated to the role played by the qubit.
		Circuit.color_background = color
		Circuit.color = 'white'
		// UI properties
		this.globalX = x;
		this.globalY = y;
		this.isCompatible = true;
		//this.anc_qubit;
		this.data_qubits = [];
		this._confirmFormat(qubits);
		this.art = this._createCircuit(message);
		this.box = this._createBackground();
		// Add the text object to the stage
		this.addChild(this.box);
		this.addChild(this.art);
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
	_createCircuit(message) {
		if (message === '') {
			const warning = 'Plaquette is not compliant.\n\n'
						  + 'Requirements:\n'
						  + '- there is a unique ancilla qubit\n'
						  + '- all other qubits are associated with either X- or Z-stabilizers\n'
					 	 + '- all data qubits are assumed physically connected to the ancilla qubit';
			message = (this.isCompatible) ? createCircuitAsciiArt(this.data_qubits, this.anc_qubit, true, 'univ') : warning;
		}
		// Create the graphics
		const artText = new Text(message,
			{
				fontFamily: 'monospace',
				fontSize: 16,
				fill: Circuit.color, // White color
				align: 'left',
				wordWrap: true,
				wordWrapWidth: 800, // Set the maximum width for word wrapping
			}
		);
		// Set the position of the text
		artText.position.set(this.globalX, this.globalY);
		return artText;
	}

	/**
	 * Creates a rectangle enclosing the circuit
	 */
	_createBackground() {
		const artBackground = new Graphics();
		// Locate corners
		const dx = this.art.getBounds().width + 30;
		const dy = this.art.getBounds().height + 30;
		// Create a rectangle
		artBackground.beginFill(Circuit.color_background);
		artBackground.drawRoundedRect(this.globalX-15, this.globalY-15, dx, dy);
		artBackground.endFill();

		// Add effects
		this.eventMode = 'static';
		// Add hover event
		/*
		this.on('pointerover', () => {
			artBackground.alpha = 0.5;
		});
		this.on('pointerout', () => {
			artBackground.alpha = 1;
		});
		*/
		return artBackground;
	};
};
