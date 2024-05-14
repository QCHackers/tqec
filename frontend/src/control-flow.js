/* eslint-disable no-param-reassign */
/* eslint-disable no-restricted-syntax */
import { useApp } from '@pixi/react';
import { Container, Point } from 'pixi.js';
import { AdjustmentFilter } from 'pixi-filters';
import Qubit from './qubits/Qubit';
import notification from './components/notification';
import Grid from './graphics/Grid';
import Footprint from './plaquettes/Footprint';
import QubitLattice from './qubits/QubitLattice';
import Button from './components/Button';
import store from './store';
import QubitLabels from './qubits/QubitLabels';

const fullPopMode = false; // Set to true to populate the workspace with qubits

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
  // Add qubits from redux store
  // const storedUnitCell = store.getState().unitCell;
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
      .filter((child) => child instanceof Footprint)
      .forEach((template) => {
        if (template.getPlaquettes().includes(plaquette)) {
          template.removeChild(plaquette);
        }
      });
    plaquette.destroy({ children: true });
  };

  workspace.mainButtonPosition = new Point(125, 50);
  const { x, y } = workspace.mainButtonPosition;

  const saveFootprintButton = new Button(
    'Save footprint',
    x,
    y
  );
  workspace.addChild(saveFootprintButton);
  notification(app, 'Specify a rectangular footprint.');
  // Make the grid squares selectable
  grid.units.forEach((row) => {
    row.forEach((unit) => {
      app.renderer.view.addEventListener('mousedown', unit.toggleVisibility);
    });
  });

  saveFootprintButton.on('click', () => {
    if (grid.visibleUnits().length === 0) {
      notification(app, 'No units selected');
      return;
    }
    if (!grid.selectedUnitsRectangular()) {
      notification(app, 'Footprint must be rectangular');
      return;
    }
    workspace.removeChild(saveFootprintButton);
    // Grid units shall no longer be selectable
    grid.units.forEach((row) => {
      row.forEach((unit) => {
        app.renderer.view.removeEventListener('mousedown', unit.toggleVisibility);
      });
    });
    notification(app, 'Specify qubits within the footprint.');
    const saveQubitConstellationButton = new Button(
      'Save Qubit Constellation',
      x,
      y
    );
    const lattice = new QubitLattice(workspace, app);
    workspace.addChild(saveQubitConstellationButton);

    app.renderer.view.addEventListener('click', lattice.selectQubitForConstellation);

    // TODO: Check the redux store for qubits and add them to the workspace
    // If there are none, instead offer to create a constellation.

    saveQubitConstellationButton.on('click', () => {
      if (lattice.constellation.length === 0) {
        notification(app, 'Constellation must have at least one qubit');
        return;
      }
      if (!grid.contains(lattice.constellation)) {
        notification(app, 'Footprint must contain each specified qubit');
        return;
      }
      if (!grid.boundaryQubitsValid(lattice.constellation)) {
        notification(app, 'Footprint must contain no overlapping qubits');
        return;
      }
      workspace.removeChild(saveQubitConstellationButton);

      // Commit footprint to redux store
      store.dispatch({
        type: 'SET_FOOTPRINT',
        payload: {
          qubits: lattice.constellation.map((q) => q.serialized()),
          gridSquares: grid.visibleUnits().map((u) => u.serialized())
        },
      });

      if (fullPopMode) {
        // Remove lattice qubits from workspace
        lattice.constellation.forEach((qubit) => {
          workspace.removeChild(qubit);
        });

        // Add qubits to the workspace
        for (let horiz = 0; horiz < app.renderer.width; horiz += grid.footprintWidth()) {
          for (let vertic = 0; vertic < app.renderer.height; vertic += grid.footprintHeight()) {
            for (const qubit of lattice.constellation) {
              const newQubit = new Qubit(
                qubit.bbX + horiz,
                qubit.bbY + vertic,
                workspace.qubitRadius,
                workspace.gridSize
              );
              workspace.addChild(newQubit);
            }
          }
        }
      }

      app.renderer.view.removeEventListener('click', lattice.selectQubitForConstellation);
      workspace.removeChild(saveFootprintButton);

      // Add "Create canonical plaquette" button
      const createPlaquetteButton = new Button(
        'Create canonical plaquette',
        x,
        y
      );
      workspace.addChild(createPlaquetteButton);
      createPlaquetteButton.on('click', () => {
        notification(app, 'Choose ancilla qubit.');
        workspace.removeChild(createPlaquetteButton);
        // Add ancilla qubit selection
        app.renderer.view.addEventListener('click', lattice.selectAncillaQubit);
        const finalizeAncillaButton = new Button('Finalize ancilla', x, y);
        workspace.addChild(finalizeAncillaButton);
        finalizeAncillaButton.on('click', () => {
          // Make sure an ancilla is selected before proceeding
          const ancilla = lattice.constellation.find((q) => q.getLabel() === QubitLabels.ancilla);
          if (ancilla === undefined) {
            notification(app, 'Please select an ancilla qubit before proceeding.');
            return;
          }
          // Remove ancilla selection
          app.renderer.view.removeEventListener('click', lattice.selectAncillaQubit);
          // Remove ancilla selection button
          workspace.removeChild(finalizeAncillaButton);
          // Now select X and Z qubits
        });
      });
    });
  });

  // Final workspace setup
  workspace.visible = true;
  app.stage.addChild(workspace);
}
