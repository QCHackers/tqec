import { Graphics } from 'pixi.js';

export default class Plaquette extends Graphics {
	constructor(qubits, gridSize = 50, color = 0x000000) {
		super();
		// UI properties
		this.color = color;
		this.gridSize = gridSize;
		this.cursor = 'pointer';
		this.mode = 'static';
		this.plaquetteMade = false;
		// QC properties
		this.qubits = qubits || []; // We assume that the list is the order of the qubits
		this.quantumCircuit = null; // Might be better to have a quantum circuit class

		// Need to be initialized last
		this.plaquetteDict = {
			3: this._createCircle,
			4: this._createConvexHull,
			5: this._createSquare,
		};
		this._createPlaquette(qubits);
	}

	/**
	 * Create a stim file
	 */
	toStim() {
		// Generate a stim file
		const stim = `H 0`;
		this.stim = stim;
		return stim;
	}

	/**
	 * Create a qasm file
	 */
	toQasm() {
		// Generate a qasm file
		// Code goes here
		const qasm = `OPENQASM 2.0;`;
		this.qasm = qasm;
		return qasm;
	}

	_createConvexHull = (qubits) => {
		// Create a convex hull
		console.log('qubits', qubits);
		for (const qubit of this.qubits) {
			if (qubit === this.qubits.length - 1) {
				// It's a measurement qubit
				qubit.qubitType = 'measurement';
			}
			// Create a convex hull from the qubits
			const { x, y } = qubit;
			// Draw a line to the next qubit
			this.lineStyle(1, this.color);
			this.moveTo(x, y);
			this.lineTo(x + this.gridSize, y);
		}
	};

	_createCircle = ([qubit1, qubit2]) => {
		// Create a half circle
		this.lineStyle(1, this.color);
		this.beginFill(this.color);
		this.arc(
			qubit1.x + qubit2.x / 2,
			qubit1.y + qubit2.y / 2,
			this.gridSize,
			0,
			Math.PI,
			true
		);
		this.position.set((qubit1.globalX + qubit2.globalX) / 2, qubit1.globalY);
		this.endFill();
		this.plaquetteMade = true;
	};

	_createSquare = (qubits) => {
		// Create a square
		// Define the square's properties (position, size, color)
		const squareSize = this.gridSize * 2; // Change the size of the square as needed
		const squareColor = this.color; // Change the color of the square as needed

		// Draw a square with drawRect() method
		this.beginFill(squareColor);
		this.drawRect(qubits[0].globalX, qubits[0].globalY, squareSize, squareSize);
		this.endFill();
		this.plaquetteMade = true;
	};

	_createPlaquette = (qubits) => {
		// The graphic should connect the points from the qubits
		const nQubits = qubits.length;
		console.log('nQubits', nQubits);
		if (nQubits < 3) {
			console.log('Plaquette must have at least 3 qubits');
			this.plaquetteMade = false;
			return null;
		}
		// Create a convex hull
		if (this.plaquetteDict[nQubits]) {
			this.plaquetteDict[nQubits](qubits);
		} else {
			// We assume that the qubits are ordered and omit the final measurement qubit
			for (const qubit of this.qubits) {
				console.log(qubit);
				console.log(this.qubits);
				// if (this.qubits.indexOf(qubit) === this.qubits.length - 1) {
				// 	// It's a measurement qubit
				// 	qubit.qubitType = 'measurement';
				// }
				// // Create a convex hull from the qubits
				// const { x, y } = qubit;
				// // Draw a line to the next qubit
				// this.lineStyle(1, this.color);
				// this.moveTo(x, y);
				// this.lineTo(x + this.gridSize, y);
			}
		}

		this.makeDraggable();
		this.makeRotatable();
	};

	// Check if the selected qubits are adjacent
	_isAdjacent = (qubit1, qubit2) => {
		const { x: x1, y: y1 } = qubit1;
		const { x: x2, y: y2 } = qubit2;
		return (
			Math.abs(x1 - x2) <= this.gridSize && Math.abs(y1 - y2) <= this.gridSize
		);
	};

	makeDraggable = () => {
		// Make the plaquette draggable
		this.interactive = true;
		this.buttonMode = true;

		// Enable interactivity for the half circle
		this.interactive = true;
		this.buttonMode = true;

		// Store initial pointer position and offset
		let pointerStartPos = { x: 0, y: 0 };
		let plaquetteStartPos = { x: 0, y: 0 };

		// Event listeners for dragging
		this.on('pointerdown', (event) => {
			// Store initial positions
			pointerStartPos = event.global.clone();
			plaquetteStartPos = this.position.clone();
			this.alpha = 0.7; // Visual feedback when dragging
		});

		this.on('pointermove', (event) => {
			if (pointerStartPos.x !== 0 && pointerStartPos.y !== 0) {
				// Calculate the new position based on the offset
				const newPosition = event.global.clone();
				const dx = newPosition.x - pointerStartPos.x;
				const dy = newPosition.y - pointerStartPos.y;
				this.x = plaquetteStartPos.x + dx;
				this.y = plaquetteStartPos.y + dy;
			}
		});

		this.on('pointerup', () => {
			pointerStartPos.set(0, 0); // Reset the pointer position
			this.alpha = 1; // Restore alpha when dragging ends
		});
	};
	makeRotatable = () => {
		let lastClickTime = 0;

		this.on('pointerup', (event) => {
			const currentTime = Date.now();
			if (currentTime - lastClickTime < 300) {
				this.rotation += Math.PI / 2; // Rotate 90 degrees
			}
			lastClickTime = currentTime;
		});
	};
}
