#!/usr/bin/env node
const fs = require("fs");

const config = {};

for (const key in process.env) {
    if (key.startsWith("REACT_APP_")) {
        config[key.substring("REACT_APP_".length)] = process.env[key];
    }
}

const src = "window.CONFIG = " + JSON.stringify(config) + ";\n";

fs.writeFile('./config.js', src, (err) => {
    if (err) {
        throw err;
    }
});
