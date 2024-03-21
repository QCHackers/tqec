import { Container, Graphics, Color } from 'pixi.js';
import Plaquette from './Plaquette';
import notification from '../components/notification';
import Button from '../components/Button';

/**
 * Footprint class to create the footprint for the plaquettes
 * @class footprint
 * @param {Container} workspace - The workspace container
 * @param {PIXI.Application} app - The PIXI application
 * @param {number} x - The x coordinate
 * @param {number} y - The y coordinate
 * @returns {void}
 */
export default class Footprint {
  constructor(workspace, app, x, y) {
    // UI Properties
    this.app = app;
    this.container = new Container();
    this.buttonMode = true;
    this.cursor = 'pointer';
    this.mode = 'static';
    this.isDragging = false;
    this.x = x;
    this.y = y;
    this.startX = 0;
    this.startY = 0;
    this.plaquette = null;
    this.selectQubitsButton = new Button('Select 3+ qubits to make a Footprint', x, y + 50);
    this.unselectQubitsButton = new Button('Unselect Qubits', x, y + 100);
    this.createPlaquetteButton = new Button('Make Plaquette', x, y + 50);
    this.selectedQubits = [];
    this.rectangle = new Graphics();
    this.workspace = workspace;
    this.container.name = 'footprint';
    this.footprintQubits = [];
    this.initializeFootprint();
  }

  /**
   * Initialize the footprint
   * @function initializefootprint
   * @returns {void}
   */
  initializeFootprint = () => {
    // Create the footprint
    this.selectQubitsButton.on('click', () => {
      this.app.view.addEventListener('click', this.selectQubit);
      this.unselectQubitsButton.visible = true;
      this.selectQubitsButton.visible = false;
      this.createPlaquetteButton.visible = false;
    });
    this.unselectQubitsButton.on('click', () => {
      // Unselect the qubits
      this.selectedQubits.forEach((qubit) => {
        qubit.deselect();
        // For each qubit, remove the text
        qubit.removeChildren();
      });
      // Clear the selected qubits
      this.selectedQubits = [];
      this.selectQubitsButton.visible = true;
      this.unselectQubitsButton.visible = false;
      this.createPlaquetteButton.visible = false;
    });

    this.createPlaquetteButton.on('click', () => {
      this.createPlaquette();
    });

    // Initialize the buttons
    this.unselectQubitsButton.visible = false;
    this.selectQubitsButton.visible = true;
    this.createPlaquetteButton.visible = false;
    this.workspace.addChild(this.selectQubitsButton);
    this.workspace.addChild(this.unselectQubitsButton);
    this.workspace.addChild(this.createPlaquetteButton);
  };

  /**
   * Select a qubit from the footprint
   * @function selectQubit
   * @param {Event} e - The click event
   * @returns {void}
   */
  selectQubit = (e) => {
    // Check if the click was on a qubit
    const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position

    // Calculate the relative click position within the canvas
    const relativeX = e.clientX - canvasRect.left;
    const relativeY = e.clientY - canvasRect.top;
    // Get all the qubits
    const qubits = this.workspace.children.filter(
      (child) => child.isQubit === true
    );
    const qubit = qubits.find(
      // Find the qubit that was clicked
      (q) => q.checkHitArea(relativeX, relativeY) === true
    );
    if (!qubit && !(qubit?.isQubit === true)) return; // Check that the qubit exists
    // Check that the qubit is not already selected
    if (this.selectedQubits.includes(qubit)) {
      // Remove the qubit from the selected qubits
      this.selectedQubits = this.selectedQubits.filter((q) => q !== qubit);
      return;
    }
    qubit.changeColor('red');
    this.selectedQubits.push(qubit);
    // Change the color of the qubit
    // Check if the selected qubits are 3 or more
    if (this.selectedQubits.length > 2) {
      // Show the button
      this.selectQubitsButton.visible = false;
      this.createPlaquetteButton.visible = true;
    }
  };

  /**
   * Create the plaquette from the selected qubits and assign it to the footprint
   * @function createPlaquette
   * @returns {void}
  */
  createPlaquette = () => {
    // Check that the selected qubits are part of the footprint area
    if (this.selectedQubits.length < 3) {
      notification(this.app, 'Plaquette requires 3+ qubits');
      return;
    }
    // Render the plaquette
    const plaquette = new Plaquette(this.selectedQubits, this.workspace, this.app);
    // Add the plaquette to the tile container
    this.container.addChild(plaquette);
    // Remove seleected qubits from the footprint qubits, so they can be used again
    // For each qubit, remove the text
    this.selectedQubits.forEach((qubit) => {
      qubit.removeChildren();
    });
    // Clear the selected qubits
    this.selectedQubits = [];
    // Notify the user that the plaquette has been created
    notification(this.app, 'Plaquette created');
    this.selectQubitsButton.visible = true;
    this.createPlaquetteButton.visible = false;
    this.unselectQubitsButton.visible = false;
  };

  /**
   * Update the visibility and event listeners
   * @function updateVisiblityAndEventListeners
   * @returns {void}
   */
  updateVisiblityAndEventListeners() {
    this.isDragging = true;
    this.container.name = 'footprint';
    // Create the buttons
    const { x, y } = this.workspace.mainButtonPosition;
    this.clearButton = new Button('Clear', x, y + 50);
    this.clearButton.on('click', () => {
      // Clear the footprint
      this.clearButton.visible = false;
      this.footprintButton.visible = true;
      this.makeTileButton.visible = false;
      this.isDragging = false;
      this.footprintQubits.forEach((qubit) => {
        qubit.changeColor('black');
      });
      // Clear the footprint qubits
      this.footprintQubits = [];
      // Remove listeners
      this.app.view.removeEventListener(
        'mousedown',
        this.mouseDownCreateFootprintArea
      );
      this.app.view.removeEventListener(
        'mousemove',
        this.mouseDragResizeFootprintArea
      );
      this.app.view.removeEventListener(
        'mouseup',
        this.mouseUpFinishFootprintArea
      );
      this.rectangle.visible = false;
      notification(this.app, 'Step 1: Drag to define a footprint area');
    });
  }

  /**
   * Create the footprint area
   * @param {*} event
   * @returns {void}
   */
  mouseDownCreateFootprintArea = (event) => {
    // Get the canvas position
    const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position
    // Calculate the relative click position within the canvas
    const relativeX = event.clientX - canvasRect.left;
    const relativeY = event.clientY - canvasRect.top;

    // Check that the event does not click on the clear button or the make tile button
    if (this.makeTileButton.getBounds().contains(relativeX, relativeY)) {
      return;
    }
    this.isDragging = true;

    // Untint the qubits
    this.footprintQubits.forEach((qubit) => {
      qubit.changeColor('black');
    });

    // Set the start position
    this.startX = event.clientX;
    this.startY = event.clientY;
    this.rectangle.position.set(relativeX, relativeY);
    this.rectangle.visible = true;
  };

  /**
   * mouseDragResizeFootprintArea
   * @param {*} event
   * @returns {void}
   */
  mouseDragResizeFootprintArea = (event) => {
    if (this.isDragging) {
      // Get the canvas position
      const width = event.clientX - this.startX;
      const height = event.clientY - this.startY;
      this.rectangle.clear();
      this.rectangle.lineStyle(2, new Color('red').toNumber());
      this.rectangle.drawRect(0, 0, width, height);
      // Find the qubits within the this.rectangle
      // eslint-disable-next-line consistent-return
      this.workspace.children.forEach((child) => {
        const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position
        // Calculate the relative click position within the canvas
        const relativeX = this.startX - canvasRect.left;
        const relativeY = this.startY - canvasRect.top;

        if (child.isQubit) {
          const qubitX = child.globalX;
          const qubitY = child.globalY;
          if (
            qubitX <= relativeX + width
            && qubitX >= relativeX
            && qubitY >= relativeY
            && qubitY <= relativeY + height
          ) {
            // Change the color of the qubits
            child.changeColor('red');
            this.footprintQubits.push(child);
            return child;
          } if (this.footprintQubits.includes(child)) {
            // If the qubit is no longer in the footprint area,
            // remove it from the footprint
            this.footprintQubits = this.footprintQubits.filter(
              (qubit) => qubit !== child
            );
            child.changeColor('black');
          }
        }
      });
    }
  };

  /**
   * mouseUpFinishFootprintArea
   * @returns {void}
   */
  mouseUpFinishFootprintArea = () => {
    this.isDragging = false;
    this.rectangle.visible = false;
  };
}
