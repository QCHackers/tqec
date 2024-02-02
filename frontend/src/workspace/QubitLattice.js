import Qubit from "./QubitClass";
import Button from "./components/button";
import { Point } from "pixi.js";

const assert = require("assert");

export default class QubitLattice {
  constructor(workspace, app) {
    assert(
      constellation.length > 0,
      "Constellation must have at least one qubit"
    );
    assert(!vector1.parallelTo(vector2), "Vectors must not be parallel");
    this.specifyQubitsButton = new Button("Specify Qubits", 100, 120);
    this.specifyQubitsButton.on("click", () => {
      this.specifyQubits();
    });
    this.workspace = workspace;
    this.app = app;
    this.constellation = [];
    // TODO: remove this event listener when the lattice is done being built
    this.app.view.addEventListener("click", this.selectQubitForConstellation);

    this.app.view.removeEventListener(
      "click",
      this.selectQubitForConstellation
    );
  }

  addQubitsToWorskspace = () => {
    // TODO: duplicate qubits based on the vectors
    // Add the qubits to the workspace
    // for (let x = 0; x <= this.app.renderer.width; x += gridSize) {
    //   for (let y = 0; y <= this.app.renderer.height; y += gridSize) {
    //     // Skip every other qubit
    //     if (x % (gridSize * 2) === 0 && y % (gridSize * 2) === 0) continue;
    //     if (x % (gridSize * 2) === gridSize && y % (gridSize * 2) === gridSize)
    //       continue;
    //     // Create a qubit
    //     const qubit = new Qubit(x, y, 5, gridSize);
    //     // Name the qubit according to its position
    //     qubit.name = `${x}_${y}`;
    //     workspace.addChild(qubit);
    //   }
    // }
    // // Give the qubit its neighbors
    // for (const q in workspace.children) {
    //   if (workspace.children[q].isQubit === true) {
    //     workspace.children[q].setNeighbors();
    //   }
    // }
  };

  relativeXY = (e) => {
    // Check if the click was on a qubit
    const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position
    // Calculate the relative click position within the canvas
    const relativeX = e.clientX - canvasRect.left;
    const relativeY = e.clientY - canvasRect.top;
    return [relativeX, relativeY];
  };

  selectVectorOrigin = (e, vector) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    vector.origin = new Point(relativeX, relativeY);
  };

  selectVectorEndpoint = (e, vector) => {
    const [relativeX, relativeY] = this.relativeXY(e);
  };

  selectQubitForConstellation = (e) => {
    const [relativeX, relativeY] = this.relativeXY(e);
    // Is this qubit already in the constellation? If so, remove it, otherwise add it
    const qubit = this.constellation.find(
      (q) => q.checkHitArea(relativeX, relativeY) === true
    );
    if (qubit) {
      // this qubit is already in the constellation
      this.constellation = this.constellation.filter((q) => q !== qubit);
    } else {
      // this qubit is not in the constellation
      this.constellation.push(new Qubit(relativeX, relativeY, 5, gridSize));
    }
  };
}

/**
 * A two-dimensional vector in the plane.
 * The vector is encoded with an origin Point and end Point.
 * @extends Array
 */
export class PlanarVector {
  dot(vector) {
    return this[0] * vector[0] + this[1] * vector[1];
  }
  cross(vector) {
    return this[0] * vector[1] - this[1] * vector[0];
  }
  parallelTo(vector) {
    return this.cross(vector) === 0;
  }
  perpendicularTo(vector) {
    return this.dot(vector) === 0;
  }
}
