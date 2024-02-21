/* eslint-disable max-len */
/* eslint-disable no-param-reassign */
/* eslint-disable no-restricted-syntax */
/* eslint-disable no-continue */
import { useApp } from '@pixi/react';
import { Container, Point } from 'pixi.js';
import { AdjustmentFilter } from 'pixi-filters';
// import { useDispatch } from 'react-redux';
import notification from './components/components/notification';
import Grid from './components/graphics/Grid';
import Template from './components/plaquettes/Template';
import Qubit from './components/qubits/Qubit';
import QubitLattice from './components/qubits/QubitLattice';
import Button from './components/components/Button';
import DownloadButton from './components/components/download/DownloadButton';
import Workspace from './components/workspace';
// import { addQubit } from './actions';

export default function InitiateControlFlow() {
  const app = useApp();
  app.stage.removeChildren(); // avoid rendering issues
  const gridSize = 50;
  const workspaceContainer = new Container();
  // const workspace = Workspace.fromJSON(JSON.parse(store.getState()?.workspace));
  const workspace = new Workspace();
  workspace.qubits = [];
  workspaceContainer.workspace = workspace; // yes this is horrible please forgive me
  workspace.name = 'workspace';
  // const dispatch = useDispatch();
  const grid = new Grid(gridSize, workspaceContainer, app);

  workspaceContainer.addChild(grid);
  grid.units.forEach((row) => {
    row.forEach((unit) => {
      workspaceContainer.addChild(unit);
    });
  });

  workspace.selectedPlaquette = null; // Used to update filters
  workspace.gridSize = gridSize;
  workspace.qubitRadius = 5;

  workspaceContainer.updateSelectedPlaquette = (newPlaquette) => {
    if (newPlaquette === null) {
      return;
    }
    const currentPlaquette = workspaceContainer.selectedPlaquette;
    if (currentPlaquette === newPlaquette) {
      currentPlaquette.filters = null;
      workspaceContainer.removeChild(workspaceContainer.getChildByName('control_panel'));
      workspaceContainer.selectedPlaquette = null;
    } else {
      if (currentPlaquette != null) {
        currentPlaquette.filters = null;
      }
      newPlaquette.filters = [new AdjustmentFilter({ contrast: 0.5 })];
      workspaceContainer.removeChild('control_panel');
      workspaceContainer.addChild(newPlaquette.controlPanel);
      workspaceContainer.selectedPlaquette = newPlaquette;
    }
  };

  workspaceContainer.removePlaquette = (plaquette) => {
    if (plaquette === null) {
      return;
    }
    if (workspaceContainer.selectedPlaquette === plaquette) {
      workspaceContainer.selectedPlaquette = null;
    }
    // Remove control panel if it is visible
    const currentControlPanel = workspaceContainer.getChildByName('control_panel');
    if (currentControlPanel === plaquette.controlPanel) {
      workspaceContainer.removeChild(currentControlPanel);
    }
    workspaceContainer.children
      .filter((child) => child instanceof Template)
      .forEach((template) => {
        if (template.getPlaquettes().includes(plaquette)) {
          template.removeChild(plaquette);
        }
      });
    plaquette.destroy({ children: true });
  };

  workspace.mainButtonPosition = new Point(125, 50);
  const { x, y } = workspace.mainButtonPosition;

  if (workspace.qubits.length > 0) {
    workspace.qubits.forEach((qubit) => {
      workspaceContainer.addChild(qubit);
    });
  } else { // Let's add some qubits.
    const createQubitConstellationButton = new Button(
      'Create Qubit Constellation',
      x,
      y
    );
    workspaceContainer.addChild(createQubitConstellationButton);
    const saveQubitConstellationButton = new Button(
      'Save Qubit Constellation',
      x,
      y
    );
    const lattice = new QubitLattice(workspaceContainer, app);
    createQubitConstellationButton.on('click', () => {
      workspaceContainer.removeChild(createQubitConstellationButton);
      workspaceContainer.addChild(saveQubitConstellationButton);
      app.view.addEventListener('click', lattice.selectQubitForConstellation);
    });
    workspaceContainer.addChild(createQubitConstellationButton);

    saveQubitConstellationButton.on('click', () => {
      if (lattice.constellation.length === 0) {
        notification(app, 'Constellation must have at least one qubit');
      } else {
        workspaceContainer.removeChild(saveQubitConstellationButton);
        lattice.createBoundingBox();
        lattice.applyBoundingBoxCoordinatesToQubits();
        const { boundingBox } = lattice;
        workspaceContainer.addChild(boundingBox);
        const finalizeBoundingQuadButton = new Button(
          'Finalize unit cell',
          x,
          y
        );
        workspaceContainer.addChild(finalizeBoundingQuadButton);
        app.view.removeEventListener('click', lattice.selectQubitForConstellation);

        // Add recolorable grid squares
        grid.units.forEach((row) => {
          row.forEach((unit) => {
            workspaceContainer.addChild(unit);
            app.renderer.view.addEventListener('mousedown', unit.toggleVisibility);
          });
        });

        finalizeBoundingQuadButton.on('click', () => {
          workspaceContainer.removeChild(boundingBox);
          workspaceContainer.removeChild(finalizeBoundingQuadButton);
          grid.units.forEach((row) => {
            row.forEach((unit) => {
              workspaceContainer.removeChild(unit);
              app.renderer.view.removeEventListener('click', unit.toggleVisibility);
            });
          });

          // Add qubits to the workspace
          for (let horiz = 0; horiz < app.renderer.width; horiz += boundingBox.logicalWidth) {
            for (let vertic = 0; vertic < app.renderer.height; vertic += boundingBox.logicalHeight) {
              for (const qubit of lattice.constellation) {
                const newQubit = new Qubit(
                  qubit.bbX + horiz,
                  qubit.bbY + vertic,
                  workspace.qubitRadius,
                  workspace.gridSize
                );
                workspaceContainer.addChild(newQubit);
                // workspaceContainer.workspace.qubits.push(newQubit);
                // TODO: use Redux to update the workspace state
                // dispatch(addQubit(newQubit));
              }
            }
          }

          // Make the original qubits invisible to remove redundancy
          lattice.constellation.forEach((qubit) => {
            qubit.visible = false;
          });

          // Initialize button to make plaquettes
          let selectedQubits = [];
          const plaquetteButton = new Button('Create plaquette', x, y + 50);
          const template = new Template(
            selectedQubits,
            workspaceContainer,
            plaquetteButton,
            app
          );

          // Create the plaquettes and template
          plaquetteButton.on('click', () => {
            template.createPlaquette();
            workspaceContainer.addChild(template.container);
            // Clear the selected qubits
            selectedQubits = [];
            plaquetteButton.visible = false;
          });
          workspaceContainer.addChild(plaquetteButton);
          workspaceContainer.removeChild(finalizeBoundingQuadButton);

          const downloadStimButton = new DownloadButton(
            workspaceContainer,
            'Download Stim file',
            x,
            y,
            'white',
            'black'
          );
          workspaceContainer.addChild(downloadStimButton);
        });
      }
    });
  }

  // Final workspace setup
  workspaceContainer.visible = true;
  app.stage.addChild(workspaceContainer);
}
