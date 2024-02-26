/* eslint-disable no-param-reassign */
/* eslint-disable no-restricted-syntax */
/* eslint-disable no-continue */
import { useApp } from '@pixi/react';
import { Container, Point } from 'pixi.js';
import { AdjustmentFilter } from 'pixi-filters';
import notification from './components/notification';
import Grid from './graphics/Grid';
import Template from './plaquettes/Template';
import Qubit from './qubits/Qubit';
import QubitLattice from './qubits/QubitLattice';
import Button from './components/Button';
import DownloadButton from './components/download/DownloadButton';
import store from './store';
import { addQubit } from './actions';

/**
 * Defines how the app behaves (button and feature placement) upon initialization
 * @returns {void}
 */
export default function InitializeControlFlow() {
  const app = useApp();
  app.stage.removeChildren(); // avoid rendering issues
  const gridSize = 50;
  const workspace = new Container();
  workspace.name = 'workspace';
  const grid = new Grid(gridSize, workspace, app);

  workspace.addChild(grid);
  grid.units.forEach((row) => {
    row.forEach((unit) => {
      workspace.addChild(unit);
    });
  });
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

  // TODO: Check the redux store for qubits and add them to the workspace
  // If there are none, instead offer to create a constellation.
  workspace.addChild(createQubitConstellationButton);

  saveQubitConstellationButton.on('click', () => {
    if (lattice.constellation.length === 0) {
      notification(app, 'Constellation must have at least one qubit');
    } else {
      workspace.removeChild(saveQubitConstellationButton);
      const finalizeBoundingQuadButton = new Button(
        'Finalize unit cell',
        x,
        y
      );
      workspace.addChild(finalizeBoundingQuadButton);
      app.view.removeEventListener('click', lattice.selectQubitForConstellation);

      // Make the grid squares selectable
      grid.units.forEach((row) => {
        row.forEach((unit) => {
          app.renderer.view.addEventListener('mousedown', unit.toggleVisibility);
        });
      });

      finalizeBoundingQuadButton.on('click', () => {
        // If the bounding box isn't a rectangle or doesn't contain every qubit, notify and return
        if (!grid.selectedUnitsRectangular()) {
          notification(app, 'Bounding quad must be rectangular');
          return;
        }
        if (!grid.contains(lattice.constellation)) {
          notification(app, 'Bounding quad must contain every qubit');
          return;
        }

        workspace.removeChild(finalizeBoundingQuadButton);
        // Grid units shall no longer be selectable
        grid.units.forEach((row) => {
          row.forEach((unit) => {
            workspace.removeChild(unit);
            app.renderer.view.removeEventListener('click', unit.toggleVisibility);
          });
        });

        // Add qubits to the workspace
        // eslint-disable-next-line max-len
        for (let horiz = 0; horiz < app.renderer.width; horiz += grid.physicalWidth) {
          // eslint-disable-next-line max-len
          for (let vertic = 0; vertic < app.renderer.height; vertic += grid.physicalHeight) {
            for (const qubit of lattice.constellation) {
              const newQubit = new Qubit(
                qubit.bbX + horiz,
                qubit.bbY + vertic,
                workspace.qubitRadius,
                workspace.gridSize
              );
              workspace.addChild(newQubit);
              // Add qubit to redux store
              store.dispatch(addQubit(newQubit.serialized()));
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

        // Create the plaquettes and template
        plaquetteButton.on('click', () => {
          template.createPlaquette();
          workspace.addChild(template.container);
          // Clear the selected qubits
          selectedQubits = [];
          plaquetteButton.visible = false;
        });
        workspace.addChild(plaquetteButton);
        workspace.removeChild(finalizeBoundingQuadButton);

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
