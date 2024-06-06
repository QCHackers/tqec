/* eslint-disable default-param-last */
import { SET_FOOTPRINT } from './actions';

export const initialState = {
  untiCell: {
    qubits: [],
    gridSquares: [],
  },
};

const rootReducer = (state = initialState, action) => {
  switch (action.type) {
  case SET_FOOTPRINT:
    return {
      unitCell: {
        qubits: action.payload.qubits,
        gridSquares: action.payload.gridSquares,
      }
    };
  default:
    return state;
  }
};

export default rootReducer;
