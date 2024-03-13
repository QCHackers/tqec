/* eslint-disable import/no-extraneous-dependencies */
/* eslint-disable no-shadow */
/* eslint-disable no-plusplus */
/* eslint-disable camelcase */

import qubitLabels from '../qubits/Qubit';

const { sprintf } = require('sprintf-js');

export const CircuitForm = Object.freeze({
  CNOT: Symbol('CNOT'),
  UNIV: Symbol('UNIV'),
});

const FMT_STR = '%10s';

/**
 * Create the circuit as ASCII art.
 *
 * Two forms of circuits are possible:
 *
 * [] "cnot"
 *    - Hadamard on the data qubits
 *    - only CNOT as 2q gates
 *    - every CNOT is controlled by a data qubit and targets the ancilla
 *
 * [] "univ"
 *    - Hadamard on the ancilla qubit
 *    - both CNOT and CZ as 2q gates
 *    - every CNOT/CZ is controlled by the ancilla and targets a data qubit
 * @function createCircuitAsciiArt
 * @param {Array} data_qubits - The data qubits.
 * @param {Object} anc_qubit - The ancilla qubit.
 * @param {boolean} [withTime=false]
 * @param {CircuitForm} [inputForm=CircuitForm.UNIV]
 */
export function createCircuitAsciiArt(
  data_qubits,
  anc_qubit,
  withTime = false,
  inputForm = CircuitForm.UNIV
) {
  const { CNOT, UNIV } = CircuitForm;
  const { cx, cz } = qubitLabels;
  let form = inputForm;
  if (form !== CNOT) {
    form = UNIV;
  }
  const lines = [];
  // Add lines for every data qubit.
  let idx = 0;
  data_qubits.forEach((qubit) => {
    let line = sprintf('f: ----'.replace('f', FMT_STR), qubit.name.replace('Qubit', 'Q'));
    // Local change of basis
    if (form === CNOT) {
      if (qubit.label === cx) line += '-H--';
      if (qubit.label === cz) line += '----';
    } else if (form === UNIV) {
      line += '----';
    }
    // Previous CNOTs
    for (let i = 0; i < idx; i++) {
      line += '-|--';
    }
    // Current CNOT
    if (form === CNOT) {
      line += '-*--';
    } else if (form === UNIV) {
      if (qubit.label === cx) line += '-X--';
      if (qubit.label === cz) line += '-*--';
    }
    // Next CNOTs
    for (let i = idx + 1; i < data_qubits.length; i++) {
      line += '----';
    }
    // Change of basis
    if (form === CNOT) {
      if (qubit.label === cx) line += '-H--';
      if (qubit.label === cz) line += '----';
    } else if (form === UNIV) {
      line += '----';
    }
    // End
    line += '----';
    lines.push(line);

    // Empty line with only vertical bars.
    //      Q(__,__): ----
    line = '              ';
    line += '    ';
    // Previous CNOTs and current one
    for (let i = 0; i < idx + 1; i++) {
      line += ' |  ';
    }
    // Next CNOTs
    for (let i = idx + 1; i < data_qubits.length; i++) {
      line += '    ';
    }
    line += '        ';
    lines.push(line);
    idx += 1;
  });
  // Add line for the ancilla qubit.
  let line = sprintf('f: |0>'.replace('f', FMT_STR), anc_qubit.name.replace('Qubit', 'Q'));
  if (form === CNOT) {
    line += '----'; // During the change of basis
  } else if (form === UNIV) {
    line += '-H--';
  }
  for (let i = 0; i < data_qubits.length; i++) {
    if (form === CNOT) {
      line += '-X--';
    } else if (form === UNIV) {
      line += '-*--';
    }
  }
  if (form === CNOT) {
    line += '---- D~ ';
  } else if (form === UNIV) {
    line += '-H-- D~ ';
  }
  lines.push(line);
  // Add time ruler.
  if (withTime) {
    //      Q(__,__):
    line = '          ';
    let line2 = 'time ruler';
    for (let i = 0; i < data_qubits.length + 4; i++) {
      line += '___ ';
      line2 += ` ${i}  `;
    }
    lines.push(line);
    lines.push(line2);
  }
  // Create the message
  let art = '';
  lines.slice(0, -1).forEach((line) => {
    art = `${art + line}\n`;
  });
  art += lines[lines.length - 1];
  return art;
}
