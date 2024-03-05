import axios from 'axios';
import Button from '../Button';
import Template from '../../plaquettes/Template';
import config from './config';
import notification from '../notification';

// const assert = require('assert');

export default class DownloadButton extends Button {
  constructor(
    workspace,
    text,
    x,
    y,
    buttonColor = 'black',
    fontColor = 'white',
  ) {
    super(text, x, y, buttonColor, fontColor);
    this.workspace = workspace;
    this.on('click', () => {
      this.onClick();
    });
    const localTesting = !window.location.href.includes('https://'); // FIXME: this is a hack
    this.stimURL = `${
      localTesting
        ? `http://${config.devBackendURL.ip}:${config.devBackendURL.port}`
        : config.prodBackendURL
    }/stim`;
  }

  onClick = () => {
    const payload = { plaquettes: [] };
    this.workspace.children
      .filter((child) => child instanceof Template)
      .forEach((tile) => {
        tile.getPlaquettes().forEach((plaquette) => {
          const marshalledPlaquette = {
            color: plaquette.color.toUint8RgbArray(),
            qubits: [],
            layers: [],
          };
          // marshall qubits
          const originQubit = plaquette.qubits
            .toSorted((a, b) => a.globalX - b.globalX) // leftmost qubits
            .toSorted((a, b) => a.globalY - b.globalY)[0]; // topmost qubit
          plaquette.qubits.forEach((qubit) => {
            // assert(
            //   qubit.qubitType === 'data' || qubit.qubitType === 'syndrome',
            //   "Qubit type must be either 'data' or 'syndrome'",
            // );
            marshalledPlaquette.qubits.push({
              x:
                (originQubit.globalX - qubit.globalX) / this.workspace.gridSize,
              y:
                (originQubit.globalY - qubit.globalY) / this.workspace.gridSize,
              qubitType: qubit.label,
            });
          });
          payload.plaquettes.push(marshalledPlaquette);
        });
      });
    // send request to backend
    axios({
      method: 'POST',
      url: this.stimURL,
      data: JSON.stringify(payload),
      headers: {
        'Content-Type': 'application/json',
        'Data-Type': 'json',
      },
      responseType: 'blob',
    })
      .then((res) => {
        // create file link in browser's memory
        const href = URL.createObjectURL(res.data);
        // create "a" HTML element with href to file & click
        const link = document.createElement('a');
        link.href = href;
        link.setAttribute('download', 'circuit.stim');
        document.body.appendChild(link);
        link.click();
        // clean up "a" element & remove ObjectURL
        document.body.removeChild(link);
        URL.revokeObjectURL(href);
      })
      .catch((err) => {
        notification(this.app, `Error: ${err}`);
      });
  };
}
