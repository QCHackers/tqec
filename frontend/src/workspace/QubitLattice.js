import { Point, Graphics, Color } from 'pixi.js';
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
    // TODO: create a minimal rectangle containing the constellation.
    const leftmostQubit = this.constellation.reduce((a, b) => (a.globalX < b.globalX ? a : b));
    const rightmostQubit = this.constellation.reduce((a, b) => (a.globalX > b.globalX ? a : b));
    const topmostQubit = this.constellation.reduce((a, b) => (a.globalY < b.globalY ? a : b));
    const bottommostQubit = this.constellation.reduce((a, b) => (a.globalY > b.globalY ? a : b));
    const delta = this.workspace.gridTileWidth;
    const upperLeftCorner = new Point(leftmostQubit.globalX - delta, topmostQubit.globalY - delta);
    // eslint-disable-next-line max-len
    const lowerRightCorner = new Point(rightmostQubit.globalX + delta, bottommostQubit.globalY + delta);
    const width = lowerRightCorner.x - upperLeftCorner.x;
    const height = lowerRightCorner.y - upperLeftCorner.y;
    const boundingBox = new Graphics();
    boundingBox.beginFill(new Color('green').toNumber());
    boundingBox.lineStyle(2, 0x0000ff, 1);
    boundingBox.drawRect(upperLeftCorner.x, upperLeftCorner.y, width, height);
    boundingBox.alpha = 0.5;
    boundingBox.endFill();
    boundingBox.visible = true;
    return boundingBox;
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
