/* eslint-disable import/no-extraneous-dependencies */
/* eslint-disable no-shadow */
/* eslint-disable no-plusplus */
/* eslint-disable camelcase */

import qubitLabels from '../qubits/Qubit';

/**
 * Create the circuit as stim code snippet.
 *
 * For simplicity, a single form of circuits is available:
 *
 * [] "univ"
 *    - Hadamard on the ancilla qubit
 *    - both CNOT and CZ as 2q gates
 *    - every CNOT/CZ is controlled by the ancilla and targets a data qubit
 *
 * @function createCircuitStimCode
 * @param {Array} data_qubits - The data qubits.
 * @param {Object} anc_qubit - The ancilla qubit.
 * @param {boolean} [addTickMarks=false] - Add TICK marks as part of the stim code
 */
export default function createCircuitStimCode(data_qubits, anc_qubit, addTickMarks = false) {
  const { cx, cz } = qubitLabels;
  let lines = [];
  // Qubit coordinates.
  let q = 1;
  let line = '';
  data_qubits.forEach((qubit) => {
    line = 'QUBIT_COORDS' + qubit.name.slice(1) + ` ${q}`;
    q += 1;
    lines.push(line);
  });
  const id_ancilla = `${data_qubits.length + 1}`;
  line = 'QUBIT_COORDS' + anc_qubit.name.slice(1) + ' ' + id_ancilla;
  lines.push(line);
  // In the first time step, reset the ancilla qubit.
  line = 'R ' + id_ancilla;
  lines.push(line);
  if (addTickMarks) lines.push('TICK');
  // In the second time step, apply the Hadamard to the ancilla qubit.
  line = 'H ' + id_ancilla;
  lines.push(line);
  if (addTickMarks) lines.push('TICK');
  // Then apply one CNOt or CZ at a time, everyone controlled by the ancilla
  // and acting on a different data qubit.
  q = 1;
  data_qubits.forEach((qubit) => {
    if (qubit.role === cx) line = 'CX ';
    if (qubit.role === cz) line = 'CZ ';
    line += id_ancilla + ` ${q}`;
    q += 1;
    lines.push(line);
    if (addTickMarks) lines.push('TICK');
  });
  // Finally, apply the Hadamard to the ancilla qubit and measure it.
  line = 'H ' + id_ancilla;
  lines.push(line);
  if (addTickMarks) lines.push('TICK');
  line = 'MR ' + id_ancilla;
  lines.push(line);
  if (addTickMarks) lines.push('TICK');
  // We do not add detectors at this stage.
  // Create the message
  let stim = '';
  lines.slice(0, -1).forEach((line) => {
    stim = stim + line + '\n';
  });
  stim += lines[lines.length - 1];
  return stim;
}
