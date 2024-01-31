import { useApp } from '@pixi/react'
import { makeGrid } from './grid'
import { Container } from 'pixi.js'
import Qubit from './qubit'
import { button } from './button'

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
	for (let x = 0; x <= app.renderer.width/gridSize; x += 1) {
		for (let y = 0; y <= app.renderer.height/gridSize; y += 1) {
			// Skip every other qubit
            if ( (x+y) % 2 === 1 )
                continue;
			// Create a qubit
			const qubit = new Qubit(x*gridSize, y*gridSize, 5, 'orange');
			// Name the qubit according to its position
			qubit.name = `${x}_${y}`;
			workspace.addChild(qubit);
		}
	}

    // Select the qubits that are part of a plaquette 
    let selectedQubits = [];
	const plaquetteButton = button('Create plaquette', 2*gridSize, 1*gridSize, 'white', 'black');
	workspace.addChild(plaquetteButton);

    plaquetteButton.on('click', (_e) => {
		// Create the plaquettes and tile
		//template.createPlaquette();
		//workspace.addChild(template.container);
		// Clear the selected qubits
		selectedQubits = [];
	});

    //  Add workspace to the stage
    workspace.visible = true;
	app.stage.addChild(workspace);

    return;
}
