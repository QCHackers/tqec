import { Point } from 'pixi.js';
import Qubit from './QubitClass';
import Button from './components/button';

export default class QubitLattice {
  constructor(workspace, app) {
    // assert(
    //   constellation.length > 0,
    //   'Constellation must have at least one qubit'
    // );
    // assert(!vector1.parallelTo(vector2), 'Vectors must not be parallel');
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

  selectFirstVectorOrigin = (e) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    this.vector1.origin = new Point(relativeX, relativeY);
  };

  selectSecondVectorOrigin = (e) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    this.vector2.origin = new Point(relativeX, relativeY);
  };

  selectFirstVectorEndpoint = (e) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    this.vector1.end = new Point(relativeX, relativeY);
  };

  selectSecondVectorEndpoint = (e) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    this.vector2.end = new Point(relativeX, relativeY);
  };

  selectQubitForConstellation = (e) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    // Is this qubit already in the constellation? If so, remove it; otherwise, add it
    const qubit = this.constellation.find(
      (q) => q.checkHitArea(relativeX, relativeY) === true
    );
    if (qubit) {
      // this qubit is already in the constellation
      this.constellation = this.constellation.filter((q) => q !== qubit);
    } else {
      // this qubit is not in the constellation
      this.constellation.push(new Qubit(relativeX, relativeY, 5, this.workspace.gridSize));
    }
  };
}
