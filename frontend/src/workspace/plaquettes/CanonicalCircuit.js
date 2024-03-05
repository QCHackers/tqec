import { Container } from 'pixi.js';

export default class CanonicalCircuit extends Container {
  constructor(ancillaQubit, measureQubit, cxQubits, czQubits) {
    super();
    this.ancillaQubit = ancillaQubit;
    this.measureQubit = measureQubit;
    this.cxQubits = cxQubits;
    this.czQubits = czQubits;
  }
}
