const express = require('express');
const serverless = require('serverless-http');
const app = express();
const child_process = require('child_process');

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.get('/', (req, res) => {
  res.send('Hello, this is Flask on Netlify!');
});

app.use('/.netlify/functions/app', (req, res) => {
  child_process.execSync('docker run -p 5000:5000 my-flask-app');
  res.send('Flask app is running...');
});

module.exports.handler = serverless(app);
