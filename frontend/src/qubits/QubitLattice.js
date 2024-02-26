import { Point } from 'pixi.js';
import Qubit from './Qubit';
import Button from '../components/Button';

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
      this.constellation = this.constellation.filter((q) => q !== qubit);
      this.workspace.removeChild(qubit);
    } else {
      // this qubit is not in the constellation
      const newQubit = new Qubit(qubitPoint.x, qubitPoint.y);
      this.constellation.push(newQubit);
      this.workspace.addChild(newQubit);
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
