import { useApp } from '@pixi/react'
import { makeGrid } from './grid'
import { Container } from 'pixi.js'
import Qubit from './qubit'
import { button } from './button'
import Plaquette from './plaquette'
import Circuit from './circuit'

// 

export default function TqecApp() {
	// Initialize the app
	let app = useApp();

	// Remove all children from the stage to avoid rendering issues
	app.stage.removeChildren();
	const gridSize = 50;
	const qubitRadius = 7;

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
			const qubit = new Qubit(x*gridSize, y*gridSize, qubitRadius);
			// Name the qubit according to its position
			qubit.name = `Q(${String(x).padStart(2, ' ')},${String(y).padStart(2, ' ')})`;
			qubit.interactive = true;
			qubit.on('click', qubit.select)
			workspace.addChild(qubit);
		}
	}

    // Select the qubits that are part of a plaquette 
    let selectedQubits = [];
	const createPlaquetteButton = button('Create plaquette', 2*gridSize, 1*gridSize, 'white', 'black');
	workspace.addChild(createPlaquetteButton);
	let plaquette;

    createPlaquetteButton.on('click', (_e) => {
		// Loop on all qubits in the workspace and gather the selected ones
		workspace.children.forEach(child => {
			if (child instanceof Qubit) {
				if (child.role !== 'none') {
					selectedQubits.push(child);
				}
			}
		});
		// For debugging purposes, annotate on the console's log which qubits were selected
		console.log(selectedQubits);

		// Create and draw the plaquette
		plaquette = new Plaquette(selectedQubits)
		plaquette.interactive = true;
		// We want the plaquette to be in the lowest layer
		workspace.addChildAt(plaquette, 0);
	});

	// Create a button to allow for printing the plaquette's qubits 
	const printQubitsButton = button('Print qubit names', 2*gridSize, 2*gridSize, 'white', 'black');
	workspace.addChild(printQubitsButton);
	let qubitsButton;

    printQubitsButton.on('click', (_e) => {
		let message = '';
		selectedQubits.forEach(qubit => {
			message = message + `${qubit.name} `;
		}); 
		qubitsButton = button(message, 2*gridSize, 3*gridSize, 'grey', 'black');
		workspace.addChild(qubitsButton);
	});

	// Create a button for printing the plaquette's circuit 
	const printCircuitButton = button('Print circuit', 2*gridSize, 4*gridSize, 'white', 'black');
	workspace.addChild(printCircuitButton);
	let circuitArt;

    printCircuitButton.on('click', (_e) => {
		circuitArt = new Circuit(selectedQubits, gridSize-25, 5*gridSize-15);
		workspace.addChild(circuitArt);
	});

	// Create a button to de-select all qubits 
	const clearPlaquetteButton = button('Clear plaquette', 2*gridSize, 8*gridSize, 'white', 'black');
	workspace.addChild(clearPlaquetteButton);

    clearPlaquetteButton.on('click', (_e) => {
		// De-select the qubits
		selectedQubits.forEach(qubit => {
		    qubit.role = 'none';
			qubit.changeColor(Qubit.color_none);
			qubit.name = qubit.name.replace(/[szxa]/g, 'q');
			qubit.removeChildren();
		}); 
		selectedQubits = []
		// Remove list of qubits
		//qubitsButton = button('', 2*gridSize, 3*gridSize, 'grey', 'black');
		workspace.removeChild(qubitsButton)
		workspace.removeChild(plaquette)
		workspace.removeChild(circuitArt)
	});

    //  Add workspace to the stage
    workspace.visible = true;
	app.stage.addChild(workspace);

    return;
}
