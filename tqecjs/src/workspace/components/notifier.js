/**
 * @fileoverview This file contains the function that shows a notification on the screen.
 * The notification is used to display messages to the user.
 */

import { Graphics, Text, Container } from 'pixi.js';

/**
 *
 * @param {*} text'
 * @description This function shows a notification on the screen.
 */
export default function notification(app, text) {
	// Create a container for the notification
	const notificationContainer = new Container();

	// Create a text object for the notification text
	const notificationText = new Text(text, {
		fontSize: 15,
		fill: 0xffffff,
		fontWeight: 'bold',
	});
	notificationText.anchor.set(0.5);
	notificationText.position.set(150, 50);
	notificationContainer.addChild(notificationText);

	// Create a background for the notification
	const background = new Graphics();
	background.beginFill(0x00ff00, 0.8);
	background.drawRoundedRect(
		0,
		0,
		notificationText.getBounds().width + 30,
		notificationText.getBounds().height + 30
	);
	background.endFill();
	notificationContainer.addChild(background);

	// Position the notification at the top center of the stage
	notificationContainer.position.set(
		app.screen.width / 2 - notificationContainer.width / 2,
		150
	);

	// Add the notification container to the stage
	app.stage.addChild(notificationContainer);

	// Remove the notification after a certain duration
	setTimeout(() => {
		app.stage.removeChild(notificationContainer);
		// Avoid memory leaks
		notificationContainer.destroy();
	}, 900);
}
