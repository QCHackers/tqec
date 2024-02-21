export default class Workspace {
  constructor() {
    this.workspace = {};
  }

  static fromJSON(json) {
    const workspace = new Workspace();
    workspace.qubits = json.qubits;
    workspace.plaquettes = json.plaquettes;
    return workspace;
  }
}
