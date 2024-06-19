import axios from 'axios';
import config from './config';

export function postExample(url, data) {
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

export function getExample(url) {
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

