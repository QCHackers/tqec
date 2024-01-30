//import { Sprite} from '@pixi/react'
//import palla from "./Sprite_palla_da_Ping_Pong.png"
import { useApp } from '@pixi/react';
import { makeGrid } from './grid';
import { Container } from 'pixi.js';

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

    workspace.visible = true;
	app.stage.addChild(workspace);

    return;
}
