import { Container, Graphics, Color } from 'pixi.js';
import Plaquette from './plaquettes/PlaquetteClass';
import notification from './components/notifier';
import Button from './components/button';

export default class Template {
  constructor(selectedQubits, workspace, plaquetteButton, app) {
    // UI Properties
    this.app = app;
    this.container = new Container();
    this.buttonMode = true;
    this.cursor = 'pointer';
    this.mode = 'static';
    this.isDragging = false;
    this.startX = 0;
    this.startY = 0;
    this.plaquette = null;
    this.plaquetteButton = plaquetteButton;
    this.templateQubits = selectedQubits || [];
    this.selectedQubits = [];
    this.rectangle = new Graphics();
    this.workspace = workspace;
    const { x, y } = workspace.mainButtonPosition;
    this.templateButton = new Button('Step 1: Define a Template', x, y + 50);
    this.templateButton.on('click', () => {
      // Create the template
      this.renderTemplateControlButtons();
      this.defineTemplateArea();
      // Clear the selected qubits
      this.selectedQubits = [];
      // Hide the button
      this.templateButton.visible = false;

      // Show a notification to now select qubits within the template to make a plaquette
    });
    this.container.addChild(this.templateButton);
    this.container.addChild(this.plaquetteButton);
    this.container.name = 'template';
    // this.workspace.addChild(this.container);
  }

  // Render the template control buttons
  renderTemplateControlButtons() {
    this.isDragging = true;
    this.container.name = 'template';
    // Create the buttons
    const { x, y } = this.workspace.mainButtonPosition;
    this.clearButton = new Button('Clear', x, y + 50);
    this.clearButton.on('click', () => {
      // Clear the template
      this.clearButton.visible = false;
      this.templateButton.visible = true;
      this.makeTileButton.visible = false;
      this.isDragging = false;
      this.templateQubits.forEach((qubit) => {
        qubit.changeColor('black');
      });
      // Clear the template qubits
      this.templateQubits = [];
      // Remove listeners
      this.app.view.removeEventListener(
        'mousedown',
        this.mouseDownCreateTemplateArea
      );
      this.app.view.removeEventListener(
        'mousemove',
        this.mouseDragResizeTemplateArea
      );
      this.app.view.removeEventListener(
        'mouseup',
        this.mouseUpFinishTemplateArea
      );
      this.rectangle.visible = false;
      notification(this.app, 'Step 1: Drag to define a template area');
    });

    this.makeTileButton = new Button(
      'Step 2: Confirm Template',
      100,
      170,
      'darkgreen'
    );
    this.makeTileButton.on('click', () => {
      if (this.templateQubits.length === 0) {
        notification(this.app, 'Template requires +3 qubits');
        return;
      }
      this.makeTileButton.visible = false;
      this.clearButton.visible = false;
      this.isDragging = false;
      // Remove listeners
      this.app.view.removeEventListener(
        'mousedown',
        this.mouseDownCreateTemplateArea
      );
      this.app.view.removeEventListener(
        'mousemove',
        this.mouseDragResizeTemplateArea
      );
      this.app.view.removeEventListener(
        'mouseup',
        this.mouseUpFinishTemplateArea
      );
      notification(this.app, 'Step 3: Click on 3+ qubits to make a plaquette');
      this.app.view.addEventListener('click', this.selectQubit);
      this.plaquetteButton.visible = true;
      this.plaquetteButton.on('click', () => {
        // Create the plaquettes and tile
        this.createPlaquette();
        this.workspace.addChild(this.container);
        // Clear the selected qubits
        this.selectedQubits = [];
        notification(this.app, 'Step 4: Define the circuit');
      });
    });

    // Add the buttons to the container
    this.container.addChild(this.clearButton);
    this.container.addChild(this.makeTileButton);
  }

  mouseDownCreateTemplateArea = (event) => {
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
    this.templateQubits.forEach((qubit) => {
      qubit.changeColor('black');
    });

    // Set the start position
    this.startX = event.clientX;
    this.startY = event.clientY;
    this.rectangle.position.set(relativeX, relativeY);
    this.rectangle.visible = true;
  };

  mouseDragResizeTemplateArea = (event) => {
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
            child.changeColor('green');
            this.templateQubits.push(child);
            return child;
          } if (this.templateQubits.includes(child)) {
            // If the qubit is no longer in the template area,
            // remove it from the template
            this.templateQubits = this.templateQubits.filter(
              (qubit) => qubit !== child
            );
            child.changeColor('black');
          }
        }
      });
    }
  };

  mouseUpFinishTemplateArea = () => {
    this.isDragging = false;
    this.rectangle.visible = false;
  };

  defineTemplateArea() {
    this.rectangle.lineStyle(2, 0xff0000);
    this.rectangle.drawRect(0, 0, 0, 0); // Initialize with zero dimensions
    this.rectangle.visible = false;
    this.rectangle.name = 'templateArea';
    this.app.stage.addChild(this.rectangle);

    this.app.renderer.view.addEventListener(
      'mousedown',
      this.mouseDownCreateTemplateArea
    );

    this.app.renderer.view.addEventListener(
      'mousemove',
      this.mouseDragResizeTemplateArea
    );

    this.app.renderer.view.addEventListener(
      'mouseup',
      this.mouseUpFinishTemplateArea
    );
    return this.templateQubits;
  }

  makeTile() {
    // Get the plaquette
    if (this.plaquette) {
      this.container.addChild(this.plaquette.onDragMove());
    } else {
      notification(this.container, this.app);
    }
  }

  // Select qubits
  selectQubit = (e) => {
    // Check if the click was on a qubit
    const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position

    // Calculate the relative click position within the canvas
    const relativeX = e.clientX - canvasRect.left;
    const relativeY = e.clientY - canvasRect.top;
    // Get all the qubits
    const qubits = this.templateQubits.filter(
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
    this.selectedQubits.push(qubit);
    if (this.selectedQubits.length > 2) {
      // Show the button
      this.plaquetteButton.visible = true;
    }
  };

  // Create the plaquette from the selected qubits and assign it to the template
  createPlaquette = () => {
    // Check that the selected qubits are part of the template area
    if (this.selectedQubits.length < 3) {
      notification(this.app, 'Plaquette requires 3+ qubits');
      return;
    }
    // Render the plaquette
    const plaquette = new Plaquette(this.selectedQubits, this.workspace);
    if (!plaquette.plaquetteMade);
    // Add the plaquette to the tile container
    this.container.addChild(plaquette);
    // For each qubit, remove the text
    this.selectedQubits.forEach((qubit) => {
      qubit.removeChildren();
    });
    // Clear the selected qubits
    this.selectedQubits = [];
    // Notify the user that the plaquette has been created
    notification(this.app, 'Plaquette created');
    this.plaquetteButton.visible = true;
  };
}
