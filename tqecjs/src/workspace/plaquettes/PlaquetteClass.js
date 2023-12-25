import { Graphics } from 'pixi.js';

export default class Plaquette extends Graphics {
	constructor(qubits, gridSize = 50, color = 0x000000) {
		super();
		// UI properties
		this.color = color;
		this.gridSize = gridSize;
		this.gridOffsetX = 50;
		this.gridOffsetY = 50;
		this.cursor = 'pointer';
		this.mode = 'static';
		this.isDragging = false;
		this.plaquetteMade = false;
		// QC properties
		this.qubits = qubits || []; // We assume that the list is the order of the qubits
		this.createPlaquette();
		this.qubitStack = [];
		this.colorToCircuit = {
			0x000000: 'X',
			0xff0000: 'Z',
		};
		this.quantumCircuit = null; // Might be better to have a quantum circuit class
	}

	clone = (qubits) => {
		// Clone the plaquette
		const newPlaquette = new Plaquette(this.qubits);
		return newPlaquette;
	};

	mostLeftQubit = () =>
		// Get the leftmost qubit
		this.qubitStack.toSorted((a, b) => a.globalX - b.globalX)[0];

	mostRightQubit = () =>
		// Get the rightmost qubit
		this.qubitStack.toSorted((a, b) => b.globalX - a.globalX)[0];

	mostTopQubit = () =>
		// Get the qubit that is closest to the top, visually
		this.qubitStack.toSorted((a, b) => a.globalY - b.globalY)[0];

	mostBottomQubit = () =>
		// Get the qubit that is closest to the bottom
		this.qubitStack.toSorted((a, b) => b.globalY - a.globalY)[0];

	width = () => {
		// Get the width of the plaquette
		const leftQubit = this.mostLeftQubit();
		const rightQubit = this.mostRightQubit();
		return rightQubit.globalX - leftQubit.globalX;
	};

	height = () => {
		// Get the height of the plaquette
		const topQubit = this.mostTopQubit();
		const bottomQubit = this.mostBottomQubit();
		return bottomQubit.globalY - topQubit.globalY;
	};
	// Function to snap coordinates to the grid
	_snapToGrid(x, y) {
		const snappedX =
			Math.round((x - this.gridOffsetX) / this.gridSize) * this.gridSize +
			this.gridOffsetX;
		const snappedY =
			Math.round((y - this.gridOffsetY) / this.gridSize) * this.gridSize +
			this.gridOffsetY;
		return { x: snappedX, y: snappedY };
	}

	_createConvexHull = () => {
		// Create a convex hull using grahams scan credit: https://en.wikipedia.org/wiki/Graham_scan
		const qubitStack = [];
		// Sort the qubits by the leftmost qubit
		const sortedQubits = this.qubits.toSorted((a, b) => a.globalX - b.globalX);
		// Using the sorted Qubit find the lowest y value qubit

		let lowestYQubit = sortedQubits[0]; // This is the first qubit in the sorted list
		// Run a for loop to find the next qubit
		for (const q in sortedQubits) {
			if (sortedQubits[q].globalY > lowestYQubit.globalY) {
				lowestYQubit = sortedQubits[q];
			}
		}
		// Sort points by polar angle with respect to lowestYQubit
		let sortedPoints = sortedQubits.toSorted((a, b) => {
			// Calculate the polar angle
			const polarAngleA = Math.atan2(
				a.globalY - lowestYQubit.globalY,
				a.globalX - lowestYQubit.globalX
			);
			const polarAngleB = Math.atan2(
				b.globalY - lowestYQubit.globalY,
				b.globalX - lowestYQubit.globalX
			);
			a.pAngle = polarAngleA;
			b.pAngle = polarAngleB;

			// Get the distance from the lowestYQubit
			const distA = Math.sqrt(
				Math.pow(a.globalX - lowestYQubit.globalX, 2) +
					Math.pow(a.globalY - lowestYQubit.globalY, 2)
			);
			const distB = Math.sqrt(
				Math.pow(b.globalX - lowestYQubit.globalX, 2) +
					Math.pow(b.globalY - lowestYQubit.globalY, 2)
			);
			a.dist = distA;
			b.dist = distB;
			return polarAngleB - polarAngleA;
		});

		sortedPoints = sortedPoints.filter((qubit) => {
			// If the qubit is the lowestYQubit, then keep it
			if (qubit === lowestYQubit) return qubit;
			// Get the qubits that have the same polar angle
			const samepQubits = sortedPoints.filter((q) => q.pAngle === qubit.pAngle);
			// Get the maximum distance qubit
			const maxDistQubit = samepQubits.sort((a, b) => {
				return b.dist - a.dist;
			})[0];
			// Return the qubit with the maximum distance
			return qubit === maxDistQubit;
		});
		// Create the stack of qubits which contains the convex hull
		for (const qubit of sortedPoints) {
			// Remove qubits from the stack if the angle formed by points next-to-top, top, and qubit is not counterclockwise
			while (
				qubitStack.length > 1 &&
				this._ccw(
					qubitStack.at(-2), // second from top
					qubitStack.at(-1), // top of stack
					qubit
				) <= 0
			) {
				qubitStack.pop();
			}
			// push the qubit onto the stack
			qubitStack.push(qubit);
		}
		// Map the qubit stack to the global coordinates
		const qubitPos = qubitStack.map((qubit) => ({
			x: qubit.globalX,
			y: qubit.globalY,
		}));

		this.beginFill(this.color);
		// Fill the convex hull
		this.drawPolygon(qubitPos);
		this.cursor = 'pointer';
		this.endFill();
		// Assign the qubit stack to the plaquette
		this.qubitStack = qubitStack;
	};

	_ccw = (p, q, r) => {
		// Check if the points are counterclockwise
		const v1 = { x: q.globalX - p.globalX, y: q.globalY - p.globalY };
		const v2 = { x: r.globalX - q.globalX, y: r.globalY - q.globalY };
		// Take the cross product
		const val = -(v1.x * v2.y - v1.y * v2.x); // If val > 0, then counterclockwise, else clockwise
		if (val === 0) return 0; // Collinear
		return val; // Clockwise  < 0 or counterclockwise >0
	};

	createPlaquette = () => {
		// The graphic should connect the points from the qubits
		const nQubits = this.qubits.length;
		if (nQubits < 3) {
			console.log('Plaquette must have at least 3 qubits');
			this.plaquetteMade = false;
			return null;
		}

		// Create a convex hull
		this._createConvexHull();
		this.plaquetteMade = true;
		// this.makeDraggable();
		// this.makeExtensible();
	};

	makeExtensible = () => {
		// Make the plaquette extensible
		this.interactive = true;
		this.buttonMode = true;
		this.on('pointerdown', this.onDragStart);
		this.on('pointermove', this.onDragMove);
	};
	onDragStart(event) {
		this.isDragging = true;
		this.initialPosition = event.data.getLocalPosition(this.parent);
	}

	onDragMove(event) {
		if (this.isDragging) {
			const newPosition = event.data.getLocalPosition(this.parent);
			console.log(newPosition);
			// Calculate the distance moved
			const deltaX = newPosition.x - this.initialPosition.x;
			const deltaY = newPosition.y - this.initialPosition.y;

			// Snap the new position to the grid
			const snappedPosition = this._snapToGrid(
				this.x + deltaX,
				this.y + deltaY
			);

			// Update the graphics position
			this.position.set(snappedPosition.x, snappedPosition.y);
		}
	}

	changePlaquetteColor(newColor) {
		this.color = newColor;
		// Update the color of the convex hull shape.
		this.clear(); // Clear the previous shape.
		this.beginFill(this.color);
		this.drawPolygon(this.qubitStack); // Replace "qubitPos" with your calculated points.
		this.endFill();
	}

	onDragEnd() {
		this.isDragging = false;
		this.initialPosition = null;
	}

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
