/* eslint-disable no-tabs */
/* eslint-disable no-underscore-dangle */
/* eslint-disable no-shadow */
/* eslint-disable no-plusplus */
/* eslint-disable no-mixed-spaces-and-tabs */
/* eslint-disable no-param-reassign */
/* eslint-disable camelcase */

import { CircuitLabels } from '../qubits/Qubit';

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
 */
export default function createCircuitAsciiArt(data_qubits, anc_qubit, with_time = true, form = 'univ') {
  if (form !== 'cnot') form = 'univ'; // Failsafe case of an unknown form option.
  const lines = [];
  // Add lines for every data qubit.
  let idx = 0;
  const { cx, cz } = CircuitLabels;
  data_qubits.forEach((qubit) => {
    let line = `${qubit.name}: ----`;
    // Local change of basis
    if (form === 'cnot') {
      if (qubit.label === cx) line += '-H--';
      if (qubit.label === cz) line += '----';
    } else if (form === 'univ') {
      line += '----';
    }
    // Previous CNOTs
    for (let i = 0; i < idx; i++) {
      line += '-|--';
    }
    // Current CNOT
    if (form === 'cnot') {
      line += '-*--';
    } else if (form === 'univ') {
      if (qubit.label === cx) line += '-X--';
      if (qubit.label === cz) line += '-*--';
    }
    // Next CNOTs
    for (let i = idx + 1; i < data_qubits.length; i++) {
      line += '----';
    }
    // Change of basis
    if (form === 'cnot') {
      if (qubit.label === cx) line += '-H--';
      if (qubit.label === cz) line += '----';
    } else if (form === 'univ') {
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
  let line = `${anc_qubit.name}: |0> `;
  if (form === 'cnot') {
    line += '----'; // During the change of basis
  } else if (form === 'univ') {
    line += '-H--';
  }
  for (let i = 0; i < data_qubits.length; i++) {
    if (form === 'cnot') {
      line += '-X--';
    } else if (form === 'univ') {
      line += '-*--';
    }
  }
  if (form === 'cnot') {
    line += '---- D~ ';
  } else if (form === 'univ') {
    line += '-H-- D~ ';
  }
  lines.push(line);
  // Add time ruler.
  if (with_time) {
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
