#!/usr/bin/python3

import glob
import http.client as httplib
import json
import os
import re

def get_mandatory(cfg, name):
    v = cfg.get(name)
    if v is None:
        raise Exception("define %s in config.json" % name)

    return v

class Pusher:
    def __init__(self):
        with open("config.json") as cf:
            cfg = json.load(cf)

        token = get_mandatory(cfg, "token")
        self.headers = {
            "Content-type": "application/json",
            "Authorization": "Token %s" % token
        }

        self.dataset_id = get_mandatory(cfg, "datasetId")
        self.mode = cfg.get("mode")

        source_dir = cfg.get("sourceDir", "json")
        self.mask = os.path.join(source_dir, "*.json")

    def get_all_files(self):
        return glob.glob(self.mask)

    def push_one(self, conn, fname, item_id):
        body = b""
        with open(fname, 'rb') as f:
            for ln in f:
                body += ln

        path = "/api/v1/DatasetItem/%s/%s" % (self.dataset_id, item_id)
        if self.mode:
            path += "?mode="
            path += self.mode

        print("posting " + fname + "...")
        conn.request("POST", path, body, self.headers)

        rsp = conn.getresponse()
        if rsp.status != 200:
            raise Exception("unexpected status " + str(rsp.status))

        answer = rsp.read().decode('utf-8')
        d = json.loads(answer)
        if (d.get("id") != item_id) or d.get("error"):
            raise Exception("unexpected answer " + answer)

        os.remove(fname)

def main():
    pusher = Pusher()
    all_files = pusher.get_all_files()
    conn = httplib.HTTPSConnection("www.hlidacstatu.cz")
    try:
        regex = re.compile("([^/\\\\]+)[.]json$")
        for fname in all_files:
            m = regex.search(fname)
            if m:
                pusher.push_one(conn, fname, m.group(1))
            else:
                print("skipping " + fname)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
