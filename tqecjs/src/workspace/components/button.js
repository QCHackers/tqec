import { Text, Container, Graphics } from 'pixi.js';
import { DropShadowFilter } from '@pixi/filter-drop-shadow';

export const Button = (text, x, y, color = 0x000000) => {
	// Create the button container
	const button = new Container();
	// Create the button text
	const buttonText = new Text(text, {
		fontFamily: 'Arial',
		fontSize: 15,
		// Adjust the font size based on the width and height of the button
		fill: 0xffffff,
		align: 'center',
	});
	buttonText.anchor.set(0.5);
	buttonText.x = x;
	buttonText.y = y;
	// Create the button background
	const buttonBackground = new Graphics();
	buttonBackground.beginFill(color);
	buttonBackground.drawRoundedRect(
		buttonText.x - buttonText.getBounds().width / 2 - 15,
		buttonText.y - buttonText.getBounds().height / 2 - 15,
		buttonText.getBounds().width + 30,
		buttonText.getBounds().height + 30
	);

	buttonBackground.endFill();

	// Add effects
	button.interactive = true;
	button.eventMode = 'static';
	// Add hover event
	button.on('pointerover', () => {
		buttonBackground.alpha = 0.5;
	});
	button.on('pointerout', () => {
		buttonBackground.alpha = 1;
	});

	// Add shadow
	buttonBackground.filters = [new DropShadowFilter()];
	// Apply cursor
	button.cursor = 'pointer';
	// Add the text to the button container
	button.addChild(buttonBackground);
	button.addChild(buttonText);
	// Add the button to the stage
	return button;
};
