import { Text, Container, Graphics } from 'pixi.js';
import { DropShadowFilter } from '@pixi/filter-drop-shadow';
import Tile from '../TileClass';
import axios from 'axios';
import config from './config.js';

const assert = require('assert');

export class Button extends Container {
	constructor (text, x, y, buttonColor = 'black', fontColor = 'white') {
		super()
		// Create the button text
		const buttonText = new Text(text, {
			fontFamily: 'Arial',
			fontSize: 15,
			// Adjust the font size based on the width and height of the button
			fill: fontColor,
			align: 'center',
		});
		buttonText.anchor.set(0.5);
		buttonText.x = x;
		buttonText.y = y;
		// Create the button background
		const buttonBackground = new Graphics();
		buttonBackground.beginFill(buttonColor);
		buttonBackground.drawRoundedRect(
			buttonText.x - buttonText.getBounds().width / 2 - 15,
			buttonText.y - buttonText.getBounds().height / 2 - 15,
			buttonText.getBounds().width + 30,
			buttonText.getBounds().height + 30
		);
	
		buttonBackground.endFill();
	
		// Add effects
		this.eventMode = 'static';
		// Add hover event
		this.on('pointerover', () => {
			buttonBackground.alpha = 0.5;
		});
		this.on('pointerout', () => {
			buttonBackground.alpha = 1;
		});
	
		// Add shadow
		buttonBackground.filters = [new DropShadowFilter()];
		// Apply cursor
		this.cursor = 'pointer';
		// Add the text to the button container
		this.addChild(buttonBackground);
		this.addChild(buttonText);
	}
}

export class DownloadButton extends Button {

	constructor(workspace, text, x, y, buttonColor = 'black', fontColor = 'white') {
		super(text, x, y, buttonColor, fontColor);
		this.workspace = workspace;
		this.on('click', (_e) => {
			this._onClick(_e);
		});
		const localTesting = !window.location.href.includes("https://"); // FIXME: this is a hack
		this.stimURL = `${localTesting ? `http://${config.devBackendURL.ip}:${config.devBackendURL.port}` : config.prodBackendURL}/stim`;
	}
	
	_onClick = (_e) => {
		const payload = {plaquettes: []};
		this.workspace.children.filter((child) => child instanceof Tile).forEach((tile) => {
			tile.getPlaquettes().forEach((plaquette) => {
				const marshalledPlaquette = {
					color: plaquette.color.toUint8RgbArray(),
					qubits: [],
					layers: []
				}
				// marshall qubits
				const originQubit = plaquette.qubits.toSorted((a, b) => a.globalX - b.globalX)	// leftmost qubits
					.toSorted((a, b) => a.globalY - b.globalY)[0]; // topmost qubit
				plaquette.qubits.forEach((qubit) => {
					assert(qubit.qubitType === "data" || qubit.qubitType === "syndrome",
						"Qubit type must be either 'data' or 'syndrome'")
					marshalledPlaquette.qubits.push({
						x: (originQubit.globalX - qubit.globalX) / this.workspace.gridSize,
						y: (originQubit.globalY - qubit.globalY) / this.workspace.gridSize,
						qubitType: qubit.qubitType
					})
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
			responseType: 'blob'
		}).then((res) => {
			// create file link in browser's memory
			const href = URL.createObjectURL(res.data);
			// create "a" HTML element with href to file & click
			const link = document.createElement('a');
			link.href = href;
			link.setAttribute('download', 'circuit.json'); //or any other extension
			document.body.appendChild(link);
			link.click();
			// clean up "a" element & remove ObjectURL
			document.body.removeChild(link);
			URL.revokeObjectURL(href);
		}).catch((err) => {
			console.log(err);
		});
	};
}
