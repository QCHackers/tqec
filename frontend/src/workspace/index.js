/* eslint-disable no-param-reassign */
/* eslint-disable no-restricted-syntax */
/* eslint-disable no-continue */
import { useApp } from '@pixi/react';
import { Container, Point } from 'pixi.js';
import { AdjustmentFilter } from 'pixi-filters';
import notification from './components/notifier';
import makeGrid from './grid';
import Template from './TemplateClass';
import Qubit from './QubitClass';
import QubitLattice from './QubitLattice';
import Button from './components/button';
import DownloadButton from './components/downloadButton';

export default function TQECApp() {
  // Initialize the app
  const app = useApp();
  // Remove all children from the stage to avoid rendering issues
  app.stage.removeChildren();
  const gridSize = 50;
  // Let's create the workspace
  const workspace = new Container();
  workspace.name = 'workspace';
  // Create the grid container
  const grid = makeGrid(app, gridSize);

  workspace.addChild(grid);
  workspace.selectedPlaquette = null; // Used to update filters
  workspace.gridSize = gridSize;
  workspace.qubitRadius = 5;

  workspace.updateSelectedPlaquette = (newPlaquette) => {
    if (newPlaquette === null) {
      return;
    }
    const currentPlaquette = workspace.selectedPlaquette;
    if (currentPlaquette === newPlaquette) {
      currentPlaquette.filters = null;
      workspace.removeChild(workspace.getChildByName('control_panel'));
      workspace.selectedPlaquette = null;
    } else {
      if (currentPlaquette != null) {
        currentPlaquette.filters = null;
      }
      newPlaquette.filters = [new AdjustmentFilter({ contrast: 0.5 })];
      workspace.removeChild('control_panel');
      workspace.addChild(newPlaquette.controlPanel);
      workspace.selectedPlaquette = newPlaquette;
    }
  };

  workspace.removePlaquette = (plaquette) => {
    if (plaquette === null) {
      return;
    }
    if (workspace.selectedPlaquette === plaquette) {
      workspace.selectedPlaquette = null;
    }
    // Remove control panel if it is visible
    const currentControlPanel = workspace.getChildByName('control_panel');
    if (currentControlPanel === plaquette.controlPanel) {
      workspace.removeChild(currentControlPanel);
    }
    workspace.children
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

  const createQubitConstellationButton = new Button(
    'Create Qubit Constellation',
    x,
    y
  );
  workspace.addChild(createQubitConstellationButton);
  const saveQubitConstellationButton = new Button(
    'Save Qubit Constellation',
    x,
    y
  );
  const lattice = new QubitLattice(workspace, app);
  createQubitConstellationButton.on('click', () => {
    workspace.removeChild(createQubitConstellationButton);
    workspace.addChild(saveQubitConstellationButton);
    app.view.addEventListener('click', lattice.selectQubitForConstellation);
  });
  workspace.addChild(createQubitConstellationButton);
  const finalizeBoundingQuadButton = new Button(
    'Finalize unit cell',
    x,
    y
  );

  saveQubitConstellationButton.on('click', () => {
    if (lattice.constellation.length === 0) {
      notification(app, 'Constellation must have at least one qubit');
    } else {
      workspace.removeChild(saveQubitConstellationButton);
      lattice.createBoundingBox();
      lattice.applyBBCoordinatesToQubits();
      // eslint-disable-next-line prefer-destructuring
      const boundingBox = lattice.boundingBox;
      workspace.addChild(boundingBox);
      workspace.addChild(finalizeBoundingQuadButton);
      app.view.removeEventListener('click', lattice.selectQubitForConstellation);

      finalizeBoundingQuadButton.on('click', () => {
        workspace.removeChild(boundingBox);
        workspace.removeChild(finalizeBoundingQuadButton);

        // eslint-disable-next-line max-len
        for (let horiz = 0; horiz < app.renderer.width; horiz += boundingBox.logicalWidth) {
          // eslint-disable-next-line max-len
          for (let vertic = 0; vertic < app.renderer.height; vertic += boundingBox.logicalHeight) {
            for (const qubit of lattice.constellation) {
              // eslint-disable-next-line max-len
              const newQubit = new Qubit(qubit.bbX + horiz, qubit.bbY + vertic, workspace.qubitRadius, workspace.gridSize);
              workspace.addChild(newQubit);
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
          workspace,
          plaquetteButton,
          app
        );

        plaquetteButton.on('click', () => {
        // Create the plaquettes and template
          template.createPlaquette();
          workspace.addChild(template.container);
          // Clear the selected qubits
          selectedQubits = [];
          plaquetteButton.visible = false;
        });

        workspace.addChild(plaquetteButton);
        workspace.removeChild(finalizeBoundingQuadButton);
        // Add download stim button
        const downloadStimButton = new DownloadButton(
          workspace,
          'Download Stim file',
          x,
          y,
          'white',
          'black'
        );
        workspace.addChild(downloadStimButton);
      });
    }
  });

  // Final workspace setup
  workspace.visible = true;
  app.stage.addChild(workspace);
}
