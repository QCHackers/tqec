import { Point } from 'pixi.js';
import Qubit from './QubitClass';
import Button from './components/button';

const assert = require('assert');

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

  createBoundingBox = () => {
    // Create a bounding box parallelogram
    // Determine the vertices of the box. It should contain every qubit,
    // and every vertex should be a grid intersection point.
    // This is a "best effort" to minimize the area, but it's not perfect.
    assert(
      this.constellation.length > 0,
      'Constellation must have at least one qubit'
    );
    // var upperLeftCorner = new Point(-Infinity, -Infinity);
    // var lowerRightCorner = new Point(Infinity, Infinity);
    // this.constellation.forEach((qubit) => {
    //   if (qubit.globalX < lowerRightCorner.x) {
    //     lowerRightCorner.x = qubit.globalX;
    //   }

    // });
  };

  /**
   *
   * @param {*} e
   * @returns
   */
  selectQubitForConstellation = (e) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    if (relativeX < 200 && relativeY < 140) {
      return; // Do not allow qubits in the top left corner
    }
    // Is this qubit already in the constellation? If so, remove it; otherwise, add it
    // FIXME: can we eliminate redundancy by cutting out the constellation instance variable?
    const qubit = this.constellation.find(
      (q) => q.checkHitArea(relativeX, relativeY) === true
    );
    if (qubit) {
      // this qubit is already in the constellation
      this.constellation = this.constellation.filter((q) => q !== qubit);
      this.workspace.removeChild(qubit);
    } else {
      // this qubit is not in the constellation
      const newQubit = new Qubit(relativeX, relativeY);
      this.constellation.push(newQubit);
      this.workspace.addChild(newQubit);
    }
    console.log(this.constellation.toString());
  };
}
