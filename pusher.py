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


def get_first_attr(doc, attrs):
    for a in attrs:
        v = doc.get(a)
        if v:
            return v

    return None


def get_first_attr_mandatory(doc, attrs):
    v = get_first_attr(doc,attrs)
    if not v:
        raise Exception("none of %s found" % attrs)

    return v


def get_birth_date(doc):
    return get_first_attr(doc, ['Narozeni', 'Birthdate'])


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
        self.varyMode = cfg.get("varyModeOnError")

        source_dir = cfg.get("sourceDir", "json")
        self.mask = os.path.join(source_dir, "*.json")

    def get_all_files(self):
        return glob.glob(self.mask)

    def push_one(self, conn, fname, item_id):
        self.do_push_one(conn, fname, item_id, self.mode)
        os.remove(fname)

    def do_push_one(self, conn, fname, item_id, mode):
        body = b""
        with open(fname, 'rb') as f:
            for ln in f:
                body += ln

        path = "/api/v1/DatasetItem/%s/%s" % (self.dataset_id, item_id)
        if mode:
            path += "?mode="
            path += mode

        print("posting " + fname + "...")
        conn.request("POST", path, body, self.headers)

        rsp = conn.getresponse()
        if rsp.status != 200:
            raise Exception("unexpected status " + str(rsp.status))

        answer = rsp.read().decode('utf-8')
        d = json.loads(answer)
        if (d.get("id") != item_id) or d.get("error"):
            if (mode == 'merge') and self.varyMode:
                self.retry_one(conn, fname, item_id, body)
            else:
                raise Exception("unexpected answer " + answer)

    def retry_one(self, conn, fname, item_id, body):
        new_doc = json.loads(body.decode('utf-8'))
        new_birth = get_birth_date(new_doc)

        path = "/api/v1/DatasetItem/%s/%s" % (self.dataset_id, item_id)
        print("checking " + item_id + "...")
        conn.request("GET", path, None, self.headers)

        rsp = conn.getresponse()
        if rsp.status != 200:
            raise Exception("unexpected status " + str(rsp.status))

        answer = rsp.read().decode('utf-8')
        old_doc = json.loads(answer)
        if (old_doc.get("Id") != item_id) or old_doc.get("error"):
            raise Exception("unexpected answer " + answer)

        old_birth = get_birth_date(old_doc)

        if old_birth:
            if new_birth:
                if old_birth != new_birth:
                    raise Exception("birth date changed from %s to %s" % (old_birth, new_birth))
            else:
                print("recycling old match")
                old_id = old_doc.get('OsobaId')
                if old_id:
                    new_doc['OsobaId'] = old_id
                else:
                    new_doc['HsProcessType'] = 'person'
                    new_doc['Name'] = get_first_attr_mandatory(old_doc, ['Jmeno', 'Name'])
                    new_doc['Surname'] = get_first_attr_mandatory(old_doc, ['Prijmeni', 'Surname'])
                    new_doc['Birthdate'] = old_birth

                fname += '.tmp'
                with open(fname, 'w') as f:
                    json.dump(new_doc, f, ensure_ascii=False)
        else:
            if not new_birth:
                raise Exception("no person found to fail merge")

        self.do_push_one(conn, fname, item_id, 'rewrite')
        if fname.endswith('.tmp'):
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
