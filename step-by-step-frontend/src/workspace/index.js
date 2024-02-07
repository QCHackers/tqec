import { useApp } from '@pixi/react'
import { makeGrid } from './grid'
import { Container, Graphics } from 'pixi.js'
import Qubit from './qubit'
import Position from './position'
import { button } from './button'
import Plaquette from './plaquette'
import Circuit from './circuit'

/////////////////////////////////////////////////////////////

export default function TqecApp() {
	// Initialize the app
	let app = useApp();

	// Remove all children from the stage to avoid rendering issues
	app.stage.removeChildren();
	const gridSize = 50;
	const qubitRadius = 7;
	const plaquetteDx = 2;
	const plaquetteDy = 2;

	// Create the workspace
	const workspace = new Container();
	workspace.name = 'workspace';

	// Create the grid container
	const grid = makeGrid(app, gridSize);
    workspace.addChild(grid);

/////////////////////////////////////////////////////////////

	// Add guide for the eyes for the plaquette boundaries.
	// They are located via the position of the top, left corner.
	// The first guide is where the plaquette is built, the other guides are for the library.
	const guideTopLeftCorners = [[11, 3], [19, 3], [19, 7], [19, 11], [19, 15]]
	const outline = new Graphics();
	outline.lineStyle(2, 'red');
	for (const [x0, y0] of guideTopLeftCorners) {
		const x1 = x0 + plaquetteDx;
		const y1 = y0 + plaquetteDy;
		outline.moveTo(x0*gridSize, y0*gridSize);
		outline.lineTo(x1*gridSize, y0*gridSize);
		outline.lineTo(x1*gridSize, y1*gridSize);
		outline.lineTo(x0*gridSize, y1*gridSize);
		outline.lineTo(x0*gridSize, y0*gridSize);
	}
    workspace.addChild(outline);

/////////////////////////////////////////////////////////////

	// Add qubit positions to the workspace
	for (let x = 0; x <= app.renderer.width/gridSize; x += 1) {
		for (let y = 0; y <= app.renderer.height/gridSize; y += 1) {
			// Skip every other qubit
            if ( (x+y) % 2 === 1 )
                continue;
			// Create a qubit
			const pos = new Position(x*gridSize, y*gridSize, qubitRadius);
    		pos.on('click', (_e) => {
				const qubit = new Qubit(x*gridSize, y*gridSize, qubitRadius);
				// Name the qubit according to its position
				qubit.name = `Q(${String(x).padStart(2, ' ')},${String(y).padStart(2, ' ')})`;
				qubit.interactive = true;
				qubit.on('click', qubit.select)
				qubit.select()
				workspace.addChild(qubit);
			});
			workspace.addChild(pos);
		}
	}

/////////////////////////////////////////////////////////////

	const infoButton = button('Library of plaquettes', 19*gridSize, 1*gridSize, 'orange', 'black');
	workspace.addChild(infoButton);


    // Select the qubits that are part of a plaquette 
	const createPlaquetteButton = button('Create plaquette', gridSize, 1*gridSize, 'white', 'black');
	workspace.addChild(createPlaquetteButton);
	let savedPlaquettes = [];
    let selectedQubits = [];

    createPlaquetteButton.on('click', (_e) => {
		// Loop on all qubits in the workspace and gather the selected ones
		selectedQubits = [];
		workspace.children.forEach(child => {
			if (child instanceof Qubit) {
				if (child.role !== 'none' && child.globalX < guideTopLeftCorners[1][0]*gridSize) {
					selectedQubits.push(child);
				}
			}
		});
		// For debugging purposes, annotate on the console's log which qubits were selected
		console.log(selectedQubits);

		// Create and draw the plaquette
		const plaquette = new Plaquette(selectedQubits)
		plaquette.interactive = true;
		savedPlaquettes.push(plaquette)
		// We want the plaquette to be in the lowest layer
		workspace.addChildAt(plaquette, 0);
	});

/////////////////////////////////////////////////////////////

	// Create a button to allow for printing the plaquette's qubits 
	const printQubitsButton = button('Print qubit names', gridSize, 2*gridSize, 'white', 'black');
	workspace.addChild(printQubitsButton);
	let qubitsButton;

    printQubitsButton.on('click', (_e) => {
		// Remove the prior info box
		workspace.removeChild(qubitsButton);
		let message = '';
		selectedQubits.forEach(qubit => {
			message = message + `${qubit.name} `;
		}); 
		qubitsButton = button(message, gridSize, 3*gridSize, 'grey', 'black');
		workspace.addChild(qubitsButton);
	});

/////////////////////////////////////////////////////////////

	// Create a button for printing the plaquette's circuit 
	const printCircuitButton = button('Print circuit', gridSize, 4*gridSize, 'white', 'black');
	workspace.addChild(printCircuitButton);
	let circuitArt;

    printCircuitButton.on('click', (_e) => {
		circuitArt = new Circuit(selectedQubits, gridSize, 5*gridSize);
		//let message = createCircuitAsciiArt(selectedQubits, selectedQubits[0]) // FIXME:
		//circuitArt = button(message, gridSize, 7*gridSize, 'grey', 'black'); // FIXME:
		workspace.addChild(circuitArt);
	});

/////////////////////////////////////////////////////////////

	const addPlaquetteButton = button('Add plaquette to library', gridSize, 10*gridSize, 'white', 'black');
	workspace.addChild(addPlaquetteButton);

    addPlaquetteButton.on('click', (_e) => {
		// De-select the qubits
		selectedQubits = [];
		// Remove list of qubits
		workspace.removeChild(qubitsButton);
		workspace.removeChild(circuitArt)
		const numPlaquettes = savedPlaquettes.length
		const dx = guideTopLeftCorners[numPlaquettes][0]-guideTopLeftCorners[0][0];
		const dy = guideTopLeftCorners[numPlaquettes][1]-guideTopLeftCorners[0][1];
		savedPlaquettes[numPlaquettes-1].movePlaquette(dx*gridSize, dy*gridSize);
	});

/////////////////////////////////////////////////////////////

	// Create a button to de-select all qubits 
	const clearPlaquetteButton = button('Clear plaquette', gridSize, 11*gridSize, 'white', 'black');
	workspace.addChild(clearPlaquetteButton);

    clearPlaquetteButton.on('click', (_e) => {
		// Clear the work-in-progress plaquette.
		for (let i = workspace.children.length - 1; i >= 0; i--) {
    		const child = workspace.children[i];
			if (child instanceof Qubit && child.globalX < guideTopLeftCorners[1][0]*gridSize)
		    	workspace.removeChild(child);
		};
	});

/////////////////////////////////////////////////////////////

    //  Add workspace to the stage
    workspace.visible = true;
	app.stage.addChild(workspace);

    return;
}
