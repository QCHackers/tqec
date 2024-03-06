/* eslint-disable no-param-reassign */
import { Graphics, Text } from 'pixi.js';

export const CircuitLabels = Object.freeze({
  ancilla: 'A',
  measure: 'M',
  cx: 'CX',
  cz: 'CZ'
});

/**
 * Qubit class
 * @extends Graphics
 * @constructor
 * @param {number} x - The x position of the qubit
 * @param {number} y - The y position of the qubit
 */
export default class Qubit extends Graphics {
  constructor(
    x,
    y,
    radius = 5,
    gridSize = 50,
    color = 'black',
  ) {
    super();
    // UI properties
    this.eventMode = 'static';
    this.buttonMode = true;
    this.cursor = 'pointer';
    // assert(x % gridSize === 0, 'x must be a multiple of gridSize');
    // assert(y % gridSize === 0, 'y must be a multiple of gridSize');
    this.globalX = x;
    this.globalY = y;
    this.createCircle(x, y, radius, color);
    this.gridSize = gridSize;
    this.maxNeighborDist = 2 * this.gridSize;
    this.neighbors = [];
    this.gridSize = gridSize;
    this.name = `Qubit(${x}, ${y})`;

    // Adjacent (degree 1) qubits
    this.isQubit = true;
    this.visible = true;
    this.isSelected = false;
  }

  toString = () => this.name;

  onPointerOver = () => {
    this.alpha = 0.5;
  };

  onPointerOut = () => {
    this.alpha = 1;
  };

  /**
   * Creates a circle
   * @param {*} x
   * @param {*} y
   * @param {*} radius
   * @param {*} color
   */
  createCircle(x, y, radius, color) {
    // Create a circle
    this.beginFill(color);
    this.drawCircle(x, y, radius);
    // this.hitArea = new Circle(x, y, radius);
    this.endFill();

    // Add hover event
    this.on('pointerover', this.onPointerOver);
    this.on('pointerout', this.onPointerOut);
  }

  changeColor(color) {
    this.clear();
    this.createCircle(this.globalX, this.globalY, 5, color);
  }

  deselect() {
    this.on('click', () => {
      if (this.isSelected === true) {
        this.isSelected = false;
        this.changeColor('black');
        this.removeChildren();
      }
    });
  }

  checkHitArea(eventX, eventY, threshold = 5) {
    // Calculate the distance between event coordinates and qubit's global position
    const distance = Math.sqrt(
      (eventX - this.globalX) ** 2 + (eventY - this.globalY) ** 2
    );
    // Define a threshold to determine the hit area
    if (distance <= threshold) {
      // If there is already a text element, don't create another one
      if (this.children.length > 0) {
        this.deselect();
        return true;
      }
      this.isSelected = true;
      // Create a text element
      const text = new Text(`Qubit:(${this.globalX},${this.globalY})`, {
        fill: 'white',
        fontSize: 10
      }); // White text color
      text.anchor.set(0.5);
      text.position.set(eventX, eventY + 10);
      this.onPointerOver();
      this.color = 0xffffff;

      // Add the text to the qubit
      this.addChild(text);
      text.visible = true;

      return true;
    }
    return false; // If no hit
  }

  /**
   * Sets the qubit state
   * @param {*} state
   */
  setQuantumState(state) {
    this.quantumState = state;
  }

  /**
   * Find neighbors of the qubit
   * There are 4 neighbors, top, bottom, left, right, does not consider diagonal neighbors
   */
  setNeighbors = () => {
    // Get surrounding qubits, this is specific to the grid we have built
    const topQubitPos = {
      x: this.globalX,
      y: this.globalY - 2 * this.gridSize
    };
    const bottomQubitPos = {
      x: this.globalX,
      y: this.globalY + 2 * this.gridSize
    };
    const leftQubitPos = {
      x: this.globalX - 2 * this.gridSize,
      y: this.globalY
    };
    const rightQubitPos = {
      x: this.globalX + 2 * this.gridSize,
      y: this.globalY
    };
    // For readability
    const neighborArr = [
      topQubitPos,
      bottomQubitPos,
      leftQubitPos,
      rightQubitPos
    ];
    // eslint-disable-next-line no-restricted-syntax, guard-for-in
    for (const q in neighborArr) {
      // Check if the qubit is within the workspace
      const qubit = this.parent.getChildByName(
        `${neighborArr[q].x}_${neighborArr[q].y}`
      );
      if (qubit) {
        // Set the neighbors
        this.neighbors.push(qubit);
      }
    }
    return this.neighbors;
  };

  hideQubitLabels = () => {
    this.children.forEach((child) => {
      if (child instanceof Text) {
        child.visible = false;
      }
    });
  };

  applyBoundingBoxCoordinates = (x, y) => {
    this.bbX = x;
    this.bbY = y;
  };

  setCircuitLabel = (label) => {
    this.label = label;
    const text = new Text(this.label, {
      fill: 'white',
      fontSize: 10
    });
    text.anchor.set(0.5);
    text.position.set(this.globalX, this.globalY - 10);
    text.visible = false;
    text.zIndex = 2;
    this.addChild(text);
    this.text = text;
  };

  showLabelText = () => {
    this.text.visible = true;
  };
}
