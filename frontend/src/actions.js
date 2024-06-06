export const SET_FOOTPRINT = 'SET_FOOTPRINT';
export const SAVE_PLAQUETTE = 'SAVE_PLAQUETTE';

export const setFootprint = (footprint) => ({
  type: SET_FOOTPRINT,
  payload: footprint,
});

export const savePlaquette = (plaquette) => ({
  type: SAVE_PLAQUETTE,
  payload: plaquette,
});
