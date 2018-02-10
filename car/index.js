"use strict";

const http = require('http');
const express = require('express');
const exec = require('child_process').exec;
const execSync = require('child_process').execSync;

// Express app
const app = express();
app.get('/', (req, res) => {

// Get raw temp data
   let linesensorscore = execSync(__dirname + '/line_sensor_scoring.py').toString();
   //let linesensorscore = 1000;
// Response
 res.json({
 status: {
 value: linesensorscore,
 description: 'Current Line Sensor Score'
 }
 });
});

app.listen(8080);