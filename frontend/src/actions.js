export const ADD_QUBIT = 'ADD_QUBIT';
export const REMOVE_QUBIT = 'REMOVE_QUBIT';
export const ADD_PLAQUETTE = 'ADD_PLAQUETTE';
export const REMOVE_PLAQUETTE = 'REMOVE_PLAQUETTE';

export const addQubit = (qubit) => ({
  type: ADD_QUBIT,
  payload: qubit,
});

export const remoteQubit = (qubit) => ({
  type: REMOVE_QUBIT,
  payload: qubit,
});
