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
		this.startX = 0;
		this.startY = 0;
		this.plaquette = null;
		this.templateQubits = selectedQubits || [];
		this.rectangle = new Graphics();
		this.workspace = workspace;
		this.templateButton = button('Step 1: Define a Template', 100, 100);
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
	}

	// Render the template control buttons
	renderTemplateControlButtons() {
		this.isDragging = true;
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
			// Clear the template qubits
			this.templateQubits = [];
			// Remove listeners
			this.app.view.removeEventListener(
				'mousedown',
				this.mouseDownCreateTemplateArea
			);
			this.app.view.removeEventListener(
				'mousemove',
				this.mouseDragResizeTemplateArea
			);
			this.app.view.removeEventListener(
				'mouseup',
				this.mouseUpFinishTemplateArea
			);
			this.rectangle.visible = false;
		});

		this.makeTileButton = button('Step 2: Confirm Tile', 100, 150, 'darkgreen');
		this.makeTileButton.on('click', (e) => {
			if (this.templateQubits.length === 0) {
				notification(this.app, 'Template requires +3 qubits');
				return;
			}
			this.makeTileButton.visible = false;
			this.clearButton.visible = false;
			this.isDragging = false;
			// Remove listeners
			this.app.view.removeEventListener(
				'mousedown',
				this.mouseDownCreateTemplateArea
			);
			this.app.view.removeEventListener(
				'mousemove',
				this.mouseDragResizeTemplateArea
			);
			this.app.view.removeEventListener(
				'mouseup',
				this.mouseUpFinishTemplateArea
			);
		});

		// Add the buttons to the container
		this.container.addChild(this.clearButton);
		this.container.addChild(this.makeTileButton);
	}

	mouseDownCreateTemplateArea = (event) => {
		// Get the canvas position
		const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position
		// Calculate the relative click position within the canvas
		const relativeX = event.clientX - canvasRect.left;
		const relativeY = event.clientY - canvasRect.top;

		// Check that the event does not click on th clear button or the make tile button
		console.log(relativeX, relativeY);

		console.log(this.clearButton.getBounds().contains(relativeX, relativeY));
		if (this.makeTileButton.getBounds().contains(relativeX, relativeY)) {
			return;
		}
		this.isDragging = true;

		// Untint the qubits
		this.templateQubits.forEach((qubit) => {
			qubit.changeColor('black');
		});

		// Set the start position
		this.startX = event.clientX;
		this.startY = event.clientY;
		this.rectangle.position.set(relativeX, relativeY);
		this.rectangle.visible = true;
	};

	mouseDragResizeTemplateArea = (event) => {
		if (this.isDragging) {
			// Get the canvas position
			const width = event.clientX - this.startX;
			const height = event.clientY - this.startY;
			this.rectangle.clear();
			this.rectangle.lineStyle(2, 0xff0000);
			this.rectangle.drawRect(0, 0, width, height);
			// Find the qubits within the this.rectangle
			this.workspace.children.filter((child) => {
				const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position
				// Calculate the relative click position within the canvas
				const relativeX = this.startX - canvasRect.left;
				const relativeY = this.startY - canvasRect.top;

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
	};

	mouseUpFinishTemplateArea = (_event) => {
		this.isDragging = false;
		this.rectangle.visible = false;
	};

	defineTemplateArea() {
		this.rectangle.lineStyle(2, 0xff0000);
		this.rectangle.drawRect(0, 0, 0, 0); // Initialize with zero dimensions
		this.rectangle.visible = false;
		this.rectangle.name = 'templateArea';
		this.app.stage.addChild(this.rectangle);

		this.app.renderer.view.addEventListener(
			'mousedown',
			this.mouseDownCreateTemplateArea
		);

		this.app.renderer.view.addEventListener(
			'mousemove',
			this.mouseDragResizeTemplateArea
		);

		this.app.renderer.view.addEventListener(
			'mouseup',
			this.mouseUpFinishTemplateArea
		);
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
