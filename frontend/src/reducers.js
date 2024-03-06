/* eslint-disable default-param-last */
import { SET_UNIT_CELL } from './actions';

export const initialState = {
  untiCell: {
    qubits: [],
    gridSquares: [],
  },
};

const rootReducer = (state = initialState, action) => {
  switch (action.type) {
  case SET_UNIT_CELL:
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
