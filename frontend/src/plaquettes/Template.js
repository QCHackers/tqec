import { Container, Graphics } from 'pixi.js';
import Plaquette from './Plaquette';
import notification from '../components/notification';
import Button from '../components/Button';

/**
 * Template class to create the template for the plaquettes
 * @class Template
 * @param {Container} workspace - The workspace container
 * @param {PIXI.Application} app - The PIXI application
 * @param {number} x - The x coordinate
 * @param {number} y - The y coordinate
 * @returns {void}
 */
export default class Template {
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
    this.selectQubitsButton = new Button('Select 3 qubits to make a Plaquette', x, y + 50);
    this.unselectQubitsButton = new Button('Unselect Qubits', x, y + 100);
    this.createPlaquetteButton = new Button('Make Plaquette', x, y + 50);
    this.selectedQubits = [];
    this.rectangle = new Graphics();
    this.workspace = workspace;
    this.container.name = 'template';
    this.initializeTemplate();
  }

  /**
   * Initialize the template
   * @function initializeTemplate
   * @returns {void}
   */
  initializeTemplate = () => {
    // Create the plaquettes and template
    this.selectQubitsButton.on('click', () => {
      this.selectQubits();
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
   * Wrapper function to select qubits
   * @function selectQubits
   */
  selectQubits() {
    this.app.view.addEventListener('click', this.selectQubit);
  }

  /**
   * Select a qubit from the template
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
   * Create the plaquette from the selected qubits and assign it to the template
   * @function createPlaquette
   * @returns {void}
  */
  createPlaquette = () => {
    // Check that the selected qubits are part of the template area
    if (this.selectedQubits.length < 3) {
      notification(this.app, 'Plaquette requires 3+ qubits');
      return;
    }
    // Render the plaquette
    const plaquette = new Plaquette(this.selectedQubits, this.workspace, this.app);
    // Add the plaquette to the tile container
    this.container.addChild(plaquette);
    // Remove seleected qubits from the template qubits, so they can be used again
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
}
