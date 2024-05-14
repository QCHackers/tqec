import { Point } from 'pixi.js';
import Qubit from './Qubit';
import QubitLabels from './QubitLabels';
import Button from '../components/Button';
import notification from '../components/notification';

export default class QubitLattice {
  constructor(workspace, app) {
    this.specifyQubitsButton = new Button('Specify Qubits', 100, 120);
    this.specifyQubitsButton.on('click', () => {
      this.specifyQubits();
    });
    this.workspace = workspace;
    this.app = app;
    this.constellation = [];
  }

  relativeXY = (e) => {
    // Check if the click was on a qubit
    const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position
    // Calculate the relative click position within the canvas
    const relativeX = e.clientX - canvasRect.left;
    const relativeY = e.clientY - canvasRect.top;
    return [relativeX, relativeY];
  };

  pointToGridIntersection = (point) => {
    // Given a point, return the nearest grid intersection point
    const x = Math.round(point.x / this.workspace.gridSize) * this.workspace.gridSize;
    const y = Math.round(point.y / this.workspace.gridSize) * this.workspace.gridSize;
    return new Point(x, y);
  };

  selectQubitForConstellation = (e) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    if (relativeX < 250 && relativeY < 150) {
      return; // Do not allow qubits in the top left corner
    }
    // TODO: create a qubit at the grid intersection point nearest to the click
    const qubitPoint = this.pointToGridIntersection(new Point(relativeX, relativeY));
    // Is this qubit already in the constellation? If so, remove it; otherwise, add it
    // FIXME: can we eliminate redundancy by cutting out the constellation instance variable?
    const qubit = this.constellation.find(
      (q) => q.checkHitArea(qubitPoint.x, qubitPoint.y) === true
    );
    if (qubit) {
      // this qubit is already in the constellation
      this.constellation = this.constellation.filter((q) => q !== qubit).flat();
      this.workspace.removeChild(qubit);
    } else {
      // this qubit is not in the constellation
      const newQubit = new Qubit(qubitPoint.x, qubitPoint.y);
      this.constellation.push(newQubit);
      this.workspace.addChild(newQubit);
    }
  };

  selectAncillaQubit = (e) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    const qubitPoint = this.pointToGridIntersection(new Point(relativeX, relativeY));
    const qubit = this.constellation.find(
      (q) => q.checkHitArea(qubitPoint.x, qubitPoint.y) === true
    );
    if (qubit) {
      // Remove the ancilla label, if there is one.
      const ancilla = this.constellation.find((q) => q.getLabel() === QubitLabels.ancilla);
      if (ancilla !== undefined) {
        ancilla.removeLabel();
        if (ancilla === qubit) {
          return;
        }
      }
      if (qubit.getLabel() === QubitLabels.ancilla) {
        qubit.removeLabel();
      } else {
        qubit.setCircuitLabel(QubitLabels.ancilla);
      }
    }
  };

  selectDataQubit = (e) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    const qubitPoint = this.pointToGridIntersection(new Point(relativeX, relativeY));
    const qubit = this.constellation.find(
      (q) => q.checkHitArea(qubitPoint.x, qubitPoint.y) === true
    );
    if (qubit) {
      if (qubit.timestep === QubitLabels.noLabel) {
        // eslint-disable-next-line no-alert
        const input = prompt('Please specify a time step for this qubit.');
        const timeStep = parseInt(input, 10);
        if (Number.isNaN(timeStep) || timeStep < 0 || timeStep > 9) {
          notification(this.app, 'Please specify a time step between 0 and 9.');
          return;
        }
        // eslint-disable-next-line no-restricted-syntax
        for (const q of this.constellation) {
          if (q.timestep === timeStep) {
            notification(this.app, 'A qubit with this time step already exists in the footprint.');
            return;
          }
        }
        qubit.setTimestep(timeStep);
      }
      // Cycle to the next label.
      const labelCycle = [QubitLabels.noLabel, QubitLabels.cx, QubitLabels.cz];
      // eslint-disable-next-line no-plusplus
      for (let k = 0; k < labelCycle.length; k++) {
        if (qubit.getLabel() === labelCycle[k]) {
          qubit.setCircuitLabel(labelCycle[(k + 1) % labelCycle.length]);
          break;
        }
      }
      if (qubit.label === QubitLabels.noLabel) {
        qubit.setTimestep(QubitLabels.noLabel);
      }
      // TODO: Rotate the qubit label
    }
  };

  applyBoundingBoxCoordinatesToQubits = () => {
    // Apply the bounding box coordinates to the qubits
    // eslint-disable-next-line no-restricted-syntax
    for (const qubit of this.constellation) {
      qubit.applyBoundingBoxCoordinates(
        qubit.globalX - this.upperLeftCorner.x,
        qubit.globalY - this.upperLeftCorner.y
      );
    }
  };
}
