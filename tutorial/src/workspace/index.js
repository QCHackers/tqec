import { useApp } from '@pixi/react'
import { makeGrid } from './grid'
import { Container, Graphics } from 'pixi.js'
import Qubit from './qubit'
import Position from './position'
import { button } from './button'
import Plaquette from './plaquette'
import Circuit from './circuit'

//import addListenersToTabButtons from './addListener'

/////////////////////////////////////////////////////////////

export default function TqecApp() {
	// Initialize the app
	let app = useApp();

    console.log('test log from workspace/index.js (TqecApp)');

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
	// We want the grid to be in the lowest layer
    workspace.addChildAt(grid, 0);

/////////////////////////////////////////////////////////////

	// Add guide for the eyes for the plaquette boundaries.
	// They are located via the position of the top, left corner.
	// The first guide is where the plaquette is built, the other guides are for the library.
	const guideTopLeftCorners = [[13, 3], [21, 3], [21, 7], [21, 11], [21, 15]]
	const libraryColors = ['purple', 'green', 'darksalmon', 'saddlebrown', 'grey']
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
	for (let x = 0; x <= app.screen.width/gridSize; x += 1) {
		for (let y = 0; y <= app.screen.height/gridSize; y += 1) {
			// Skip every other qubit
            if ( (x+y) % 2 === 1 )
                continue;
			// Create a qubit
			const pos = new Position(x*gridSize, y*gridSize, qubitRadius-2);
    		pos.on('click', (_e) => {
				const qubit = new Qubit(x*gridSize, y*gridSize, qubitRadius);
				// Name the qubit according to its position relative to the top-left
				// corner of the plaquette-building area.
				qubit.name = `Q(${String(x-guideTopLeftCorners[0][0]).padStart(2, ' ')},${String(y-guideTopLeftCorners[0][1]).padStart(2, ' ')})`;
				qubit.interactive = true;
				qubit.on('click', qubit.select)
				qubit.select()
				workspace.addChild(qubit);
			});
			workspace.addChild(pos);
		}
	}
	const num_background_children = workspace.children.length;


/////////////////////////////////////////////////////////////

	const infoButton = button('Library of plaquettes', guideTopLeftCorners[1][0]*gridSize, 1*gridSize, 'orange', 'black');
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
				if (child.role !== 'none' && child.globalX < (guideTopLeftCorners[1][0]-2)*gridSize) {
					selectedQubits.push(child);
				}
			}
		});
		if (selectedQubits.length === 0) return;
		// For debugging purposes, annotate on the console's log which qubits were selected
		console.log(selectedQubits);

		// Clear WIP plaquette when not saved
		let numPlaquettes = savedPlaquettes.length;
		if (numPlaquettes !== 0 && savedPlaquettes[numPlaquettes-1].name === 'WIP plaquette') {
			workspace.removeChild(savedPlaquettes[numPlaquettes-1]);
			savedPlaquettes.pop();
			numPlaquettes -= 1;
		};
		// Create and draw the plaquette named 'WIP plaquette'
		const plaquette = new Plaquette(selectedQubits, libraryColors[numPlaquettes])
		plaquette.interactive = true;
		savedPlaquettes.push(plaquette);
		// We want the plaquette to be in the layer just above the grid, guides/outlines, and positions.
		workspace.addChildAt(plaquette, num_background_children);
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
	let circuitArt = null;
    const circuitarea = document.getElementById('editableText');

    printCircuitButton.on('click', (_e) => {
		circuitArt = new Circuit(selectedQubits, gridSize, 5*gridSize, libraryColors[savedPlaquettes.length-1]);
		circuitArt.visible = true;
		workspace.addChild(circuitArt);
		let message = circuitArt.art.text;
		circuitarea.value = message;
	});

	// Listen for user input events
	circuitarea.addEventListener('input', (event) => {
		const inputValue = event.target.value; // Get the input value
		console.log('Textarea input event:', inputValue);
		updateCircuit(inputValue); // Update the text based on the input
	});

	// Function to update the circuit
	function updateCircuit(inputValue) {
		workspace.removeChild(circuitArt);
		circuitArt = new Circuit(selectedQubits, gridSize, 5*gridSize, libraryColors[savedPlaquettes.length-1], inputValue);
		circuitArt.visible = true;
		workspace.addChild(circuitArt);
		// You can also add conditional logic here based on the input
	}

/////////////////////////////////////////////////////////////

	// Create a button for printing the plaquette's circuit 
	const confirmCircuitButton = button('Confirm circuit', gridSize, 11*gridSize, 'white', 'black');
	workspace.addChild(confirmCircuitButton);

    confirmCircuitButton.on('click', (_e) => {
		if (savedPlaquettes.length === 0) return; // Failsafe case
		if (circuitArt === null) return; // Failsafe case

		let plaquette = savedPlaquettes[savedPlaquettes.length-1];
		plaquette.addChild(circuitArt);

		plaquette.on('click', (_e) => {
			plaquette.showCircuit()
		});
		
	});

/////////////////////////////////////////////////////////////

	const addPlaquetteButton = button('Add plaquette to library', gridSize, 12*gridSize, 'white', 'black');
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
		savedPlaquettes[numPlaquettes-1].name = `plaquette ${numPlaquettes}`;
		savedPlaquettes[numPlaquettes-1].translatePlaquette(dx*gridSize, dy*gridSize);
		// Make circuit disappear
		savedPlaquettes[numPlaquettes-1].showCircuit()
		// Reset the message in the circuit-edit area
		circuitarea.value = 'Edit the circuit here...';
	});

/////////////////////////////////////////////////////////////

	// Create a button to de-select all qubits 
	const clearPlaquetteButton = button('Clear plaquette', gridSize, 13*gridSize, 'white', 'black');
	workspace.addChild(clearPlaquetteButton);

    clearPlaquetteButton.on('click', (_e) => {
		// Clear the work-in-progress plaquette.
		for (let i = workspace.children.length - 1; i >= 0; i--) {
    		const child = workspace.children[i];
			if (child instanceof Qubit && child.globalX < (guideTopLeftCorners[1][0]-2)*gridSize)
		    	workspace.removeChild(child);
			else if (child instanceof Qubit && child.role === 'none')
		    	workspace.removeChild(child);
			else if (child instanceof Plaquette && child.name === 'WIP plaquette')
				workspace.removeChild(child);
		};
		workspace.removeChild(circuitArt)
		if (savedPlaquettes.length !== 0 && savedPlaquettes[savedPlaquettes.length-1].name === 'WIP plaquette')
			savedPlaquettes.pop();
	});

/////////////////////////////////////////////////////////////

	// Create a button to de-select all qubits 
	const downloadLibraryButton = button('Download plaquette library', gridSize, 15*gridSize, 'white', 'black');
	workspace.addChild(downloadLibraryButton);

	downloadLibraryButton.on('click', (_e) => {
		if (savedPlaquettes.length === 0) return;
	
		let message = '';
		let counter = 0;
		savedPlaquettes.forEach((plaq) => {
			if (plaq.name !== 'WIP plaquette') {
				message += '###############\n'
				message += `# plaquette ${counter} #\n`
				message += '###############\n\n'
				plaq.children.forEach((child) => {
					if (child instanceof Circuit) {
						console.log('circuit to add');
						message += child.art.text;
						message += '\n\n\n';
						console.log(message);
					}
				});
				counter += 1;
			}
		});
		const blob = new Blob([message], { type: 'text/plain' });
		const url = URL.createObjectURL(blob);

		const link = document.createElement('a');
		link.href = url;
		link.download = 'plaquette_library.txt';
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);
	});

/////////////////////////////////////////////////////////////

    //  Add workspace to the stage
    workspace.visible = true;
	app.stage.addChild(workspace);

    return null;
}
