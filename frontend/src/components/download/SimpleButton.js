import axios from 'axios';
import Button from '../Button';
import config from './config';

function postExample(url, data) {
  console.log(url);
  console.log(data);
  axios({
    method: 'POST',
    url,
    data: JSON.stringify(data),
    headers: {
      'Content-Type': 'application/json',
    },
  })
    .then((response) => { console.log(response.status); })
    .catch((err) => { console.log(err); });
}

function getExample(url) {
  axios({
    method: 'GET',
    url,
    headers: {
      'Content-Type': 'application/json',
      'Data-Type': 'json',
    },
    responseType: 'json',
  })
    .then((response) => {
      console.log(response.status);
      console.log(response.data.value);
    })
    .catch((err) => { console.log(err); });
}

export default class SimpleButton extends Button {
  constructor(
    text,
    x,
    y,
    buttonColor = 'black',
    fontColor = 'white',
    url = '/example',
    method = 'POST',
  ) {
    super(text, x, y, buttonColor, fontColor);
    this.method = method;
    this.on('click', () => {
      this.onClick();
    });
    const localTesting = !window.location.href.includes('https://'); // FIXME: this is a hack
    this.backendURL = `${localTesting
      ? `http://${config.devBackendURL.ip}:${config.devBackendURL.port}`
      : config.prodBackendURL
    }`;
    this.backendURL += url;
  }

  onClick = () => {
    if (this.method === 'POST') {
      const payload = { name: 'post_exmaple', value: '3.14' };
      postExample(this.backendURL, payload);
    } else {
      getExample(this.backendURL);
    }
  };
}
