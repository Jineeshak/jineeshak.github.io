---
layout: post
title: Filtering WebSocket Noise in BurpSuite Using Bambda
date: 2025-05-14 22:00 +0530
categories: [burp, websocket]
tags: [websocket, burpsuite, bamda, pentest, message-filtering, burp-extensions, montoya, bugbounty]
---


## Introduction

One of the issues a tester faces when testing a WebSocket-heavy application is that there aren't many filtering options available for WebSocket traffic — unlike HTTP messages in Burp Suite. 

With HTTP traffic, you can easily scope URLs, hide irrelevant hosts, or apply fine-grained filters. But with WebSockets, **the entire flow becomes noisy**: constant `ping`/`pong` messages, huge volumes of client-server chatter, and **no easy way to hide out-of-scope traffic**.

That's where **Bambda**, a not-so-new feature in Burp Suite, comes in. It allows you to filter WebSocket messages based on content, direction, and even size — helping you **tidy up the signal from the noise**.

## The Problem

When dealing with WebSocket traffic, you often face:

- A stream of `ping`/`pong` messages
- Messages from out-of-scope domains you don't care about
- Large payloads mixed with short heartbeats
- Limited UI-level filtering options

![Burp Suite WebSocket Filtering Options](https://github.com/Jineeshak/jineeshak.github.io/blob/main/assets/img/Burp_websocket.png?raw=true)
* Burp Suite WebSocket filtering options for managing WebSocket traffic*


As a result, **analyzing meaningful WebSocket messages gets painful**, especially in large apps or single-page applications with real-time data sync.

## Filtering with Bambda

Bambda is Burp Suite’s custom filtering language — think of it like Java snippets used to process and filter WebSocket messages.

You can write expressions in the **WebSocket history filter bar** using `message ->` syntax. Here are some real-world examples we’ve tested:

### 1. Remove `ping`/`pong` messages

```java
return !message.payload().toString().contains("ping") && 
       !message.payload().toString().contains("pong");
```
This removes most of the heartbeat traffic that clutters your view.

### 2. Show only client-to-server messages longer than 60 bytes and likely to contain URLs (e.g., for SSRF hunting)

```java
return message.payload().length() > 60 &&
       message.direction() == Direction.CLIENT_TO_SERVER &&
       message.payload().toString().matches(".*https?://.*");
```

### 3. Exclude out-of-scope domains manually  
Since there's no `isInScope()` for WebSocket messages, you can manually exclude domains:

```java
return !message.payload().toString().contains("outofscope.com");
```

Add more exclusions as needed.

### 4. Filter for JSON-looking content

```java
return message.payload().toString().trim().startsWith("{");
```

This helps you focus on structured data — especially useful for GraphQL or REST over WebSocket.

### 5. Show only server responses

```java
return message.direction() == Direction.SERVER_TO_CLIENT;
```

Useful when you just want to track what the server is pushing.

## Limitations
- Bambda filtering is powerful but comes with a *performance cost* — complex filters can lag the UI.
- Some familiarity with coding is required to write and customize Bambda filters effectively.

## Conclusion
If you're dealing with modern web apps that rely heavily on WebSockets, cleaning up the traffic becomes a necessity. Burp Suite doesn't offer the same level of filtering for WebSocket traffic as it does for HTTP, but Bambda gives you a way to take control.

By using Bambda filters, you can:

- Cut out the noise (like ping/pong)
- Focus on request/response directions
- Detect payloads with specific characteristics (like URLs or JSON)
- Create a manageable WebSocket testing workflow

This doesn’t solve everything — but it gets you closer to clarity in a stream of chaos.

For more information on Montoya API and examples, check out [here](https://github.com/PortSwigger/burp-extensions-montoya-api-examples) and the official [Montoya API documentation](https://portswigger.github.io/burp-extensions-montoya-api/javadoc/burp/api/montoya/MontoyaApi.html).
