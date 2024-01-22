import { Container, Graphics } from 'pixi.js';
import Plaquette from './plaquettes/PlaquetteClass';
import notification from './components/notifier';
import { button } from './components/button';

export default class Template {
	constructor(selectedQubits, workspace, app) {
		// UI Properties
		this.app = app;
		this.container = new Container();
		this.buttonMode = true;
		this.cursor = 'pointer';
		this.mode = 'static';
		this.isDragging = false;
		this.prevMouseX = 0;
		this.prevMouseY = 0;
		this.workspace = workspace;
		this.templateButton = button('Step 1: Define a Template', 50, 100);
		this.templateButton.on('click', (e) => {
			// Create the template
			this.renderTemplateControlButtons();
			this.defineTemplateArea();
			// Clear the selected qubits
			selectedQubits = [];
			// Hide the button
			this.templateButton.visible = false;

			// Show a notification to now select qubits within the template to make a plaquette
		});
		this.container.addChild(this.templateButton);
		// Quantum
		this.selectedQubits = selectedQubits || [];
		this.plaquette = null;
		this.templateQubits = selectedQubits || [];
	}

	// Render the template control buttons
	renderTemplateControlButtons() {
		this.container.name = 'template';
		// Create the buttons
		this.clearButton = button('Clear', 100, 100);
		this.clearButton.on('click', (e) => {
			// Clear the template
			this.clearButton.visible = false;
			this.templateButton.visible = true;
			this.makeTileButton.visible = false;
			this.isDragging = false;
			this.templateQubits.forEach((qubit) => {
				qubit.changeColor('black');
			});
			this.selectedQubits = [];
		});

		this.makeTileButton = button('Step 2: Confirm Tile', 100, 150, 'darkgreen');
		this.makeTileButton.on('click', (e) => {
			this.makeTileButton.visible = false;
			this.clearButton.visible = false;
			this.templateButton.visible = true;
			this.isDragging = false;
			this.makeTileButton.visible = false;
			// Create the plaquettes and tile
			return this.templateQubits;
		});

		// Add the buttons to the container
		this.container.addChild(this.clearButton);
		this.container.addChild(this.makeTileButton);
	}

	defineTemplateArea() {
		const rectangle = new Graphics();
		rectangle.lineStyle(2, 0xff0000);
		rectangle.drawRect(0, 0, 0, 0); // Initialize with zero dimensions
		rectangle.visible = false;
		rectangle.name = 'templateArea';
		this.app.stage.addChild(rectangle);

		let isDragging = false;
		let startX, startY;

		this.app.renderer.view.addEventListener('mousedown', (event) => {
			isDragging = true;

			// Untint the qubits
			this.templateQubits.forEach((qubit) => {
				qubit.changeColor('black');
			});

			// Get the canvas position
			const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position
			// Calculate the relative click position within the canvas
			const relativeX = event.clientX - canvasRect.left;
			const relativeY = event.clientY - canvasRect.top;

			// Set the start position
			startX = event.clientX;
			startY = event.clientY;
			rectangle.position.set(relativeX, relativeY);
			rectangle.visible = true;
		});

		this.app.renderer.view.addEventListener('mousemove', (event) => {
			if (isDragging) {
				// Get the canvas position
				const width = event.clientX - startX;
				const height = event.clientY - startY;
				rectangle.clear();
				rectangle.lineStyle(2, 0xff0000);
				rectangle.drawRect(0, 0, width, height);
				// Find the qubits within the rectangle
				this.workspace.children.filter((child) => {
					const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position
					// Calculate the relative click position within the canvas
					const relativeX = startX - canvasRect.left;
					const relativeY = startY - canvasRect.top;

					if (child.isQubit) {
						const qubitX = child.globalX;
						const qubitY = child.globalY;
						if (
							qubitX <= relativeX + width &&
							qubitX >= relativeX &&
							qubitY >= relativeY &&
							qubitY <= relativeY + height
						) {
							// Change the color of the qubits
							child.changeColor('green');
							this.templateQubits.push(child);
							return child;
						} else if (this.templateQubits.includes(child)) {
							// If the qubit is no longer in the template area, remove it from the template
							this.templateQubits = this.templateQubits.filter(
								(qubit) => qubit !== child
							);
							child.changeColor('black');
						}
					}
				});
			}
		});

		this.app.renderer.view.addEventListener('mouseup', () => {
			isDragging = false;
			rectangle.visible = false;
		});
		return this.templateQubits;
		// Notify the user that the template area has been defined
		// notification(this.workspace, 'Template area defined');
	}

	makeTile() {
		// Get the plaquette
		if (this.plaquette) {
			this.container.addChild(this.plaquette.onDragMove());
		} else {
			notification(this.container, this.app);
		}
	}

	// Create the plaquettes that are assigned to the tile
	createPlaquette = () => {
		const workspace = this.app.stage.getChildByName('workspace');
		// Check that the selected qubits are part of the template area
		for (const qubit in this.selectedQubits) {
			if (!this.templateQubits.includes(qubit)) {
				notification(
					this.workspace,
					'Please select qubits within the template area'
				);
				return;
			}
		}
		// Render the plaquette
		const plaquette = new Plaquette(this.selectedQubits, workspace); // Remove the container
		if (!plaquette.plaquetteMade) return;
		// Add the plaquette to the tile container
		this.container.addChild(plaquette);
		// For each qubit, remove the text
		this.selectedQubits.forEach((qubit) => {
			qubit.removeChildren();
		});
	};
}
