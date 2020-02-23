#!/usr/bin/python3

from datetime import datetime
import json
import sys


def load_dict(path):
    with open(path) as f:
        doc = json.load(f)
        if not isinstance(doc, dict):
            raise Exception("%s must be JSON dictionary." % path)

        return doc


def pack_tree(matrix_node):
    dataset_node = {}
    for k, v in matrix_node.items():
        if isinstance(v, dict):
            ov = pack_tree(v)
        elif isinstance(v, str) and (len(v) > 1) and (v[0] == '@'):
            source_path = v[1:]
            if source_path == 'now()':
                ov = str(datetime.today())
            else:
                with open(source_path) as f:
                    ov = f.read()
        else:
            ov = v

        dataset_node[k] = ov

    return dataset_node


def pack_dataset(matrix_path, dataset_path):
    matrix_doc = load_dict(matrix_path)
    dataset_doc = pack_tree(matrix_doc)
    with open(dataset_path, 'w') as f:
        json.dump(dataset_doc, f, ensure_ascii=False)


def unpack_tree(matrix_node, dataset_node):
    for k, v in matrix_node.items():
        if isinstance(v, dict):
            ov = dataset_node.get(k)
            if ov and isinstance(ov, dict):
                unpack_tree(v, ov)
        elif isinstance(v, str) and (len(v) > 1) and (v[0] == '@'):
            target_path = v[1:]
            if target_path != 'now()':
                ov = dataset_node.get(k)
                if ov is None:
                    raise Exception("Matrix value %s not found in dataset." % k)

                if not isinstance(ov, str):
                    raise Exception("Type of %s is %s." % (k, type(ov)))

                with open(target_path, 'w') as f:
                    f.write(ov)


def unpack_dataset(matrix_path, dataset_path):
    matrix_doc = load_dict(matrix_path)
    dataset_doc = load_dict(dataset_path)
    unpack_tree(matrix_doc, dataset_doc)


def main():
    pack = None
    matrix = None
    dataset = None
    for a in sys.argv[1:]:
        if matrix is False:
            if not a:
                raise Exception("empty --matrix argument")

            matrix = a
        elif dataset is False:
            if not a:
                raise Exception("empty --dataset argument")

            dataset = a
        else:
            if a in ('-p', '--pack'):
                if pack is not None:
                    raise Exception("repeated --pack argument")

                pack = True
            elif a in ('-u', '--unpack'):
                if pack is not None:
                    raise Exception("repeated --unpack argument")

                pack = False
            elif a in ('-m', '--matrix'):
                if matrix:
                    raise Exception("repeated --matrix argument")

                matrix = False
            elif a in ('-d', '--dataset'):
                if dataset:
                    raise Exception("repeated --dataset argument")

                dataset = False

    if not matrix or not dataset:
        print("usage: " + sys.argv[0] + " [ -p | --pack | -u | --unpack ] { -m | --matrix } matrix.json { -d | --dataset } dataset.json")
        sys.exit(1)

    if pack:
        pack_dataset(matrix, dataset)
    else:
        unpack_dataset(matrix, dataset)


if __name__ == "__main__":
    main()
