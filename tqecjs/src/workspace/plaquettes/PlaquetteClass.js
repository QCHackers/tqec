import { Graphics, Container } from 'pixi.js';
import { button } from '../components/button';
import notification from '../components/notifier';

export default class Plaquette extends Graphics {
	constructor(qubits, workspace, gridSize = 50, color = 'purple') {
		super();
		// UI properties
		this.workspace = workspace;
		this.color = color;
		this.gridSize = gridSize;
		this.gridOffsetX = this.gridSize;
		this.gridOffsetY = this.gridSize;
		this.isDragging = false;
		this.plaquetteMade = false;
		this.showButton = false;
		this.controlPanel = new Container();
		this.controlPanel.name = 'control_panel';
		this.controlPanel.visible = false;
		this.rotateButton = button('Rotate', 200, 200, 'black');
		this.clearButton = button('Clear', 200, 275, 'red');
		this.colorButton = button('Change color', 200, 350, 'green');
		this.makeRotatable(); // Add the rotate button to screen
		this.clearPlaquette(); // Add the clearbutton to the screen
		this.changeColorButton(); // Add the change color button to the screen
		//this.changeColorButton(); // Addh the color change button
		// QC properties
		this.qubits = qubits || []; // We assume that the list is the order of the qubits
		this.qubitStack = []; // The stack of qubits that form the convex hull
		this.createPlaquette(); // Create the plaquette
		this.quantumCircuit = null; // Might be better to have a quantum circuit class
		this.workspace.addChild(this.controlPanel);
	}

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

	calculatePlaquetteCenter = () => {
		// Get the geometric center of the plaquette
		if (this.qubitStack.length === 0) {
			return { x: 0, y: 0 }; // Return the center of an empty polygon as (0, 0).
		}

		// Calculate the average x and y coordinates
		let sumX = 0;
		let sumY = 0;
		for (const vertex of this.qubitStack) {
			sumX += vertex.globalX;
			sumY += vertex.globalY;
		}

		const centerX = sumX / this.qubitStack.length;
		const centerY = sumY / this.qubitStack.length;

		return { x: centerX, y: centerY };
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
				)
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
		if (val === 0) return true; // Collinear
		return val > 0 ? false : true;
	};

	createPlaquette = () => {
		// The graphic should connect the points from the qubits
		const nQubits = this.qubits.length;
		if (nQubits < 3) {
			console.log('Plaquette must have at least 3 qubits');
			// Show a notification to the user that the plaquette must have at least 3 qubits
			notification(this.workspace, 'Plaquette must have at least 3 qubits');
			this.plaquetteMade = false;
			return null;
		}

		// Create a convex hull
		this._createConvexHull();
		const { x, y } = this.calculatePlaquetteCenter();
		// Set the position and pivot of the plaquette
		this.pivot.set(x, y);
		this.position.set(x, y);
		// Allow for the object to be interactive
		this.plaquetteMade = true;
		this.cursor = 'pointer';
		this.makeExtensible();
		this.toggleCtrlButtons();
	};

	makeExtensible = () => {
		// Make the plaquette extensible
		this.buttonMode = true;
		this.on('pointerdown', this.onDragStart);
		this.on('pointermove', this.onDragMove);
		this.on('pointerup', this.onDragEnd);
	};
	onDragStart(event) {
		this.isDragging = true;
		this.initialPosition = event.data.getLocalPosition(this.parent);
		console.log(this.initialPosition);
	}

	onDragMove = (event) => {
		let newQubits = [];
		let diff = 0;
		// Get current position
		const newPosition = event.data.getLocalPosition(this.parent);
		// Calculate the distance moved
		const deltaX = newPosition.x - this.initialPosition?.x;
		const deltaY = newPosition.y - this.initialPosition?.y;
		console.log(deltaY, deltaY);
		let shiftQ = null;
		if (
			this.isDragging &&
			(deltaX >= this.gridSize * 0.4 || deltaY >= this.gridSize * 0.4)
		) {
			// Check which direction the plaquette is being dragged
			if (Math.abs(deltaX) > Math.abs(deltaY)) {
				// Dragging horizontally
				if (deltaX > 0) {
					// Moving to the right
					shiftQ = this.mostRightQubit();
					// Find the neighboring qubit that is closest to the right
					const newrq = shiftQ.neighbors.find(
						(qubit) =>
							qubit.globalX > shiftQ.globalX && qubit.globalY === shiftQ.globalY
					);

					diff = newrq.globalX - shiftQ.globalX;
				} else {
					// Generate the qubits that are closest to the left
					shiftQ = this.mostLeftQubit();
					// Find the neighboring qubit that is closest to the left
					const newlq = shiftQ.neighbors.find(
						(qubit) =>
							qubit.globalX < shiftQ.globalX && qubit.globalY === shiftQ.globalY
					);
					diff = newlq.globalX - shiftQ.globalX;
				}
				// Shift the qubits by the difference
				for (const qubit of this.qubits) {
					const q = qubit.neighbors.find(
						// eslint-disable-next-line no-loop-func
						(q) =>
							q.globalX === qubit.globalX + diff && q.globalY === qubit.globalY
					);
					newQubits.push(q);
				}
			} else {
				if (deltaY > 0) {
					// Generate the qubits that are closest to the top
					shiftQ = this.mostTopQubit();
					console.log(shiftQ, 'shiftQ tq');
					console.log(shiftQ.neighbors);
					// Find the neighboring qubit that is closest to the top
					const newtq = shiftQ.neighbors.find(
						(qubit) =>
							qubit.globalX === shiftQ.globalX && qubit.globalY > shiftQ.globalY
					);

					diff = newtq.globalY - shiftQ.globalY;
				} else {
					// Generate the qubits that are closest to the bottom
					shiftQ = this.mostBottomQubit();
					// Find the neighboring qubit that is closest to the bottom
					const newbq = shiftQ.neighbors.find(
						(qubit) =>
							qubit.globalX === shiftQ.globalX && qubit.globalY < shiftQ.globalY
					);
					diff = newbq.globalY - shiftQ.globalY;
				}
				// Shift the qubits by the difference
				for (const qubit of this.qubits) {
					const q = qubit.neighbors.find(
						(q) =>
							q.globalX === qubit.globalX && q.globalY === qubit.globalY + diff
					);
					newQubits.push(q);
				}
			}

			// Create a new plaquette
			let color = 'yellow';
			if (this.color !== 'purple') {
				color = 'purple';
			}
			console.log(color);
			const newPlaquette = new Plaquette(
				newQubits,
				this.workspace,
				this.gridSize,
				color
			);
			// Change the color of the plaquette

			// Add the plaquette to the tile
			this.addChild(newPlaquette);
		}
	};

	changePlaquetteColor(newColor) {
		this.color = newColor;
		// Update the color of the convex hull shape.
		this.clear();
		this.createPlaquette();
	}

	onDragEnd() {
		this.isDragging = false;
		this.initialPosition = null;
	}

	toggleCtrlButtons = () => {
		let lastClickTime = 0;
		this.on('click', (e) => {
			const currentTime = Date.now();
			if (currentTime - lastClickTime < 300) {
				// Set the alpha of the plaquette to 0.8 to indicate
				// Check if the plaquette is clicked, not the button
				this.showButton = !this.showButton;
				// this.showButton ? (this.alpha = 0.8) : (this.alpha = 1);
				// Show or hide the buttons
				this.controlPanel.visible = this.showButton;
			}
			lastClickTime = currentTime;
		});
	};

	makeRotatable = () => {
		// Rotate the plaquette by 90 degrees. Still needs to make sure it maps to qubits on grid
		this.rotateButton.on('click', (_event) => {
			// Rotate the plaquette
			this.rotation += Math.PI / 2; // Rotate 90 degrees
			console.log(this.rotateButton.position);
		});
		this.rotateButton.name = 'rotate_button';
		// Add the button to the control panel container
		this.controlPanel.addChild(this.rotateButton);
	};

	changeColorButton = () => {
		this.colorButton.on('click', (_event) => {
			if (this.color === 'purple') this.changePlaquetteColor('yellow');
			else {
				this.changePlaquetteColor('purple');
			} // Change the color of the plaquette})
		});
		this.colorButton.name = 'color_button';
		this.controlPanel.addChild(this.colorButton);
	};

	clearPlaquette = () => {
		this.clearButton.on('click', (_event) => {
			const cp = this.workspace.getChildByName('control_panel');
			cp.destroy();
			this.destroy();
		});
		this.clearButton.name = 'clear_button';
		this.controlPanel.addChild(this.clearButton);
	};
}
