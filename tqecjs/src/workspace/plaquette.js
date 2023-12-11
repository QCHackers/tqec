import { Text, Container, Graphics } from 'pixi.js';
import { DropShadowFilter } from 'pixi-filters';

const plaquetteContainer = () => {
	// Create a container
	const roundedContainer = new Container();

	// Create a rounded rectangle graphics for the background
	const background = new Graphics();
	const containerWidth = 300; // Adjust the width of the container
	const containerHeight = 600; // Adjust the height of the container
	const cornerRadius = 15; // Adjust the corner radius for rounded edges

	background.beginFill(0xcccccc); // Change the color of the background
	background.drawRoundedRect(
		0,
		0,
		containerWidth,
		containerHeight,
		cornerRadius
	);
	background.endFill();

	// Add the background to the container
	roundedContainer.addChild(background);

	// Position the container
	roundedContainer.x = 50; // Adjust X position as needed
	roundedContainer.y = 50; // Adjust Y position as needed

	// Apply shadow effect to the container
	roundedContainer.filters = [
		new DropShadowFilter({
			distance: 10, // Adjust the distance of the shadow
			blur: 5, // Adjust the blur strength
			alpha: 0.3, // Adjust the alpha of the shadow
			quality: 5, // Adjust the quality of the shadow
		}),
	];

	// Add a text to the container
	const text = new Text('Plaquette', {
		fill: 'black',
		fontSize: 20,
		fontFamily: 'Arial',
	});
	text.x = 15; // Adjust the X position of the text
	text.y = 15; // Adjust the Y position of the text
	roundedContainer.addChild(text);
	return roundedContainer;
};

const makeDraggable = (plaquette) => {
	// Make the plaquette draggable
	plaquette.interactive = true;
	plaquette.buttonMode = true;

	// Enable interactivity for the half circle
	plaquette.interactive = true;
	plaquette.buttonMode = true;

	// Store initial pointer position and offset
	let pointerStartPos = { x: 0, y: 0 };
	let plaquetteStartPos = { x: 0, y: 0 };

	// Event listeners for dragging
	plaquette.on('pointerdown', (event) => {
		// Store initial positions
		pointerStartPos = event.data.global.clone();
		plaquetteStartPos = plaquette.position.clone();
		plaquette.alpha = 0.7; // Visual feedback when dragging
	});

	plaquette.on('pointermove', (event) => {
		if (pointerStartPos.x !== 0 && pointerStartPos.y !== 0) {
			// Calculate the new position based on the offset
			const newPosition = event.data.global.clone();
			const dx = newPosition.x - pointerStartPos.x;
			const dy = newPosition.y - pointerStartPos.y;
			plaquette.x = plaquetteStartPos.x + dx;
			plaquette.y = plaquetteStartPos.y + dy;
		}
	});

	plaquette.on('pointerup', () => {
		pointerStartPos.set(0, 0); // Reset the pointer position
		plaquette.alpha = 1; // Restore alpha when dragging ends
	});
};

const createPlaquette = (plaquetteQubits) => {
	const container = plaquetteContainer();
	console.log(plaquetteQubits);
	if (plaquetteQubits.length > 3) {
		// Create a square
		const square = new Graphics();
		// Define the square's properties (position, size, color)
		const squareSize = 100; // Change the size of the square as needed
		const squareColor = 0xff0000; // Change the color of the square as needed

		// Draw a square with drawRect() method
		square.beginFill(squareColor);
		square.drawRect(50, 50, squareSize, squareSize);
		square.endFill();

		// Position the square
		square.x = 0; // Centering the square horizontally
		square.y = 200; // Centering the square vertically
		makeDraggable(square);
		container.addChild(square);
	}
	if (plaquetteQubits.length > 2) {
		// Create a triangle
		console.log(plaquetteQubits, 'hello');
		const triangle = new Graphics();
		// Define the triangle's properties (position, size, color)
		const triangleSize = 100; // Change the size of the triangle as needed
		const triangleColor = 0x00ff00; // Change the color of the triangle as needed

		// Draw a triangle with drawPolygon() method
		triangle.beginFill(triangleColor);

		// Define the points of the triangle (x, y coordinates)
		const points = [
			0,
			-triangleSize / Math.sqrt(3), // Top point
			-triangleSize / 2,
			triangleSize / (2 * Math.sqrt(3)), // Bottom left point
			triangleSize / 2,
			triangleSize / (2 * Math.sqrt(3)), // Bottom right point
		];
		triangle.drawPolygon(points);
		triangle.endFill();

		// Position the triangle
		triangle.x = container.getGlobalPosition().x + 50; // Centering the triangle horizontally
		triangle.y = 180; // Centering the triangle vertically

		// Add the tr
		makeDraggable(triangle);
		container.addChild(triangle);
	}

	if (plaquetteQubits.length > 1) {
		// Create polygons that represent the plaquette

		// Create a half circle
		const halfCircle = new Graphics();
		halfCircle.lineStyle(1, 0x000000);
		halfCircle.beginFill(0x000000);
		halfCircle.arc(
			container.getGlobalPosition().x + 50,
			container.getGlobalPosition().y + 50,
			50,
			0,
			Math.PI,
			true
		);

		halfCircle.endFill();
		makeDraggable(halfCircle);

		container.addChild(halfCircle);
	}
	// Add the container to the stage
	return container;
};

export const plaquette = (app, vertex) => {
	// Return an ordered list of vertices
	const plaquetteQubits = [];

	// Add an onClick event listener to the vertex
	vertex.on('click', () => {
		// If no text exists, create and display the integer next to the vertex
		const text = new Text(`Qubit: ${plaquetteQubits.length + 1}`, {
			fill: 'black',
			fontSize: 12,
			fontFamily: 'Arial',
		});
		text.x = vertex.x + 15;
		text.y = vertex.y - 15;
		vertex.addChild(text);
		plaquetteQubits.push(vertex);
		const plaquetteDashboard = createPlaquette(plaquetteQubits);
		app.stage.addChild(plaquetteDashboard);
	});
};
