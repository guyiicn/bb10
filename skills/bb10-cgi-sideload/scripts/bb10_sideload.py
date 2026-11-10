#!/usr/bin/env python3
"""Install a BB10 BAR through the same HTTPS CGI protocol used by Sachesi."""
import argparse
import getpass
import hashlib
import http.cookiejar
import os
import ssl
import struct
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


def hash_password(password, salt, iterations, challenge):
    if not 1 <= iterations <= 100000:
        raise ValueError("unexpected iteration count")
    data = password.encode("utf-8")
    for phase in range(2):
        if phase == 1:
            data = challenge.encode("utf-8") + data
        for counter in range(iterations):
            data = hashlib.sha512(struct.pack("<I", counter) + salt + data).digest()
    return data.hex().upper()


def first_child(data):
    return ET.fromstring(data).find("*")


def text(element, name, default=""):
    node = element.find(name)
    return node.text if node is not None and node.text else default


def main():
    parser = argparse.ArgumentParser(description="Sideload a BAR to a BB10 device")
    parser.add_argument("bar")
    parser.add_argument("--host", default="169.254.0.1")
    parser.add_argument("--password-stdin", action="store_true",
                        help="read one password line from stdin instead of prompting")
    args = parser.parse_args()
    bar_path = os.path.abspath(args.bar)
    if not os.path.isfile(bar_path):
        parser.error("BAR not found: " + bar_path)
    password = (sys.stdin.readline().rstrip("\r\n") if args.password_stdin
                else getpass.getpass("BB10 device password: "))
    if not password:
        parser.error("empty device password")

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.minimum_version = ssl.TLSVersion.TLSv1
    context.maximum_version = ssl.TLSVersion.TLSv1
    context.set_ciphers("DEFAULT:@SECLEVEL=0")
    cookies = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookies),
        urllib.request.HTTPSHandler(context=context),
    )
    base = "https://%s/cgi-bin/" % args.host

    def request(path, data=None, content_type="application/x-www-form-urlencoded"):
        req = urllib.request.Request(
            base + path,
            data=data,
            headers={"User-Agent": "QNXWebClient/1.0", "Content-Type": content_type},
            method="POST" if data is not None else "GET",
        )
        try:
            return opener.open(req, timeout=180).read()
        except Exception as exc:
            # BB10's old HTTPS server may close without TLS close_notify after
            # sending a complete response. urllib normally preserves HTTPError
            # bodies, so use one if available.
            if hasattr(exc, "read"):
                body = exc.read()
                if body:
                    return body
            raise

    challenge = first_child(request("login.cgi?request_version=3"))
    if challenge is None or challenge.tag != "AuthChallenge":
        raise RuntimeError("unexpected login response")
    remaining = text(challenge, "RetriesRemaining", "unknown")
    digest = hash_password(
        password,
        bytes.fromhex(text(challenge, "Salt")),
        int(text(challenge, "ICount")),
        text(challenge, "Challenge"),
    )
    auth = first_child(request(
        "login.cgi?challenge_data=%s&request_version=3" % digest
    ))
    status = text(auth, "Status") if auth is not None else ""
    if auth is None or auth.tag != "Auth" or status not in ("Allowed", "Success"):
        raise RuntimeError("authentication failed (retries previously reported: %s)" % remaining)
    print("authenticated")

    size = os.path.getsize(bar_path)
    start_data = urllib.parse.urlencode({"mode": "bar", "size": str(size)}).encode()
    start = first_child(request("update.cgi", start_data))
    if start is None or start.tag != "UpdateStart":
        raise RuntimeError("device refused update start")
    print("start UpdateStart")

    with open(bar_path, "rb") as stream:
        payload = stream.read()
    sent = first_child(request("update.cgi?type=bar", payload, "application/octet-stream"))
    sent_status = text(sent, "Status") if sent is not None else ""
    print("send %s %s" % (sent.tag if sent is not None else "?", sent_status))
    if sent is None or sent.tag != "UpdateSend" or sent_status == "Error":
        raise RuntimeError("BAR upload rejected")

    for _ in range(180):
        progress = first_child(request("update.cgi", b""))
        state = text(progress, "Status") if progress is not None else ""
        percent = text(progress, "Progress") if progress is not None else ""
        print("poll %s %s %s" % (progress.tag if progress is not None else "?", state, percent))
        if state == "Success":
            finish_data = urllib.parse.urlencode({"status": "success"}).encode()
            finish = first_child(request("update.cgi", finish_data))
            finish_status = text(finish, "Status") if finish is not None else ""
            print("finish %s %s" % (finish.tag if finish is not None else "?", finish_status))
            return 0 if finish_status == "Success" else 6
        if state == "Error":
            print(ET.tostring(progress, encoding="unicode"), file=sys.stderr)
            return 5
        time.sleep(1)
    print("timed out waiting for installation", file=sys.stderr)
    return 7


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print("error: %s" % exc, file=sys.stderr)
        sys.exit(1)
