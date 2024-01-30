//import { Sprite} from '@pixi/react'
//import palla from "./Sprite_palla_da_Ping_Pong.png"
import { useApp } from '@pixi/react'
import { makeGrid } from './grid'
import { Container } from 'pixi.js'
import Qubit from './qubit'

// 

export default function TqecApp() {
	// Initialize the app
	let app = useApp();

	// Remove all children from the stage to avoid rendering issues
	app.stage.removeChildren();
	const gridSize = 50;

	// Create the workspace
	const workspace = new Container();
	workspace.name = 'workspace';

	// Create the grid container
	const grid = makeGrid(app, gridSize);
    workspace.addChild(grid);

	// Add the qubits to the workspace
	for (let x = 0; x <= app.renderer.width; x += gridSize) {
		for (let y = 0; y <= app.renderer.height; y += gridSize) {
			// Skip every other qubit
			if (x % (gridSize * 2) === 0 && y % (gridSize * 2) === 0) continue;
			if (x % (gridSize * 2) === gridSize && y % (gridSize * 2) === gridSize)
				continue;
			// Create a qubit
			const qubit = new Qubit(x, y, 5, 'orange', gridSize);
			// Name the qubit according to its position
			qubit.name = `${x}_${y}`;
			workspace.addChild(qubit);
		}
	}

    //  Add workspace to the stage
    workspace.visible = true;
	app.stage.addChild(workspace);

    return;
}
