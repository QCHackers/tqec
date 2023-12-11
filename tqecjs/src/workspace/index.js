import { useApp } from '@pixi/react';
import { grid } from './grid';

export default function PixiApp() {
	let app = useApp();
	app.stage.removeChildren();
	// Create the grid.
	grid(app);

	return;
}
