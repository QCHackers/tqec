/* eslint-disable default-param-last */
// reducers/workspaceReducer.js
import { ADD_QUBIT, REMOVE_QUBIT } from './actions';

const initialState = {
  qubits: [],
  plaquettes: [],
};

const workspaceReducer = (state = initialState, action) => {
  switch (action.type) {
  case ADD_QUBIT:
    state.qubits.push(action.payload);
    return state;
  case REMOVE_QUBIT:
    state.qubits.forEach((qubit, index) => {
      if (qubit === action.payload) {
        state.qubits.splice(index, 1);
      }
    });
    return state;
  default:
    return state;
  }
};

const rootReducer = workspaceReducer;

export default rootReducer;
