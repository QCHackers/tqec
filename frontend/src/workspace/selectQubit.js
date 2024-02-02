export default selectQubit = (e) => {
  // Check if the click was on a qubit
  const canvasRect = this.app.view.getBoundingClientRect(); // Get canvas position

  // Calculate the relative click position within the canvas
  const relativeX = e.clientX - canvasRect.left;
  const relativeY = e.clientY - canvasRect.top;
  // Get all the qubits
  const qubits = this.templateQubits.filter((child) => child.isQubit === true);
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
