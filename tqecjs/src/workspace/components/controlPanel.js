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
