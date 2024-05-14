/* eslint-disable no-param-reassign */
import { Graphics, Text } from 'pixi.js';
import QubitLabels from './QubitLabels';

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

    this.globalX = x;
    this.globalY = y;
    this.createCircle(x, y, radius, color);
    this.gridSize = gridSize;
    this.maxNeighborDist = 2 * this.gridSize;
    this.neighbors = [];
    this.gridSize = gridSize;
    this.name = `Qubit(${x}, ${y})`;

    // Adjacent (degree 1) qubits
    this.visible = true;
    this.isSelected = false;

    this.timestep = QubitLabels.noLabel;
    this.label = QubitLabels.noLabel;
  }

  toString = () => this.name;

  serialized = () => ({
    x: this.globalX,
    y: this.globalY,
    radius: this.radius,
    gridSize: this.gridSize,
    color: this.color,
    qubitType: this.qubitType
  });

  onPointerOver = () => {
    this.alpha = 0.5;
  };

  onPointerOut = () => {
    this.alpha = 1;
  };

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
      this.onPointerOver();
      this.color = 0xffffff;
      return true;
    }
    return false; // If no hit
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

  updateLabel = () => {
    const label = new Text(`${this.label}${this.timestep}`, {
      fontSize: 10,
      fill: 'white'
    });
    label.anchor.set(0.5);
    label.position.set(this.globalX, this.globalY - 10);
    label.visible = true;
    label.zIndex = 0.5;
    // Remove all children
    this.children.forEach((child) => {
      this.removeChild(child);
    });
    this.addChild(label);
  };

  setCircuitLabel = (label) => {
    this.label = label;
    this.updateLabel();
  };

  getLabel = () => this.label;

  hideLabel = () => {
    this.children.forEach((child) => {
      if (child instanceof Text) {
        child.visible = false;
      }
    });
  };

  setTimestep = (timestep) => {
    this.timestep = timestep;
    this.updateLabel();
  };

  removeLabel = () => {
    this.setCircuitLabel(QubitLabels.noLabel);
  };
}
