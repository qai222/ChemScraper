import json
import logging
import os
import os.path
import pathlib
import pickle
import time
import typing

import monty.json

FilePath = typing.Union[pathlib.Path, os.PathLike, str]


def file_exists(fn: FilePath):
    return os.path.isfile(fn) and os.path.getsize(fn) > 0


def json_dump(o, fn: FilePath):
    with open(fn, "w") as f:
        json.dump(o, f, cls=monty.json.MontyEncoder)


def json_load(fn: FilePath, warning=False):
    if warning:
        logging.warning("loading file: {}".format(fn))
    with open(fn, "r") as f:
        o = json.load(f, cls=monty.json.MontyDecoder)
    return o


def strip_extension(p: FilePath):
    return os.path.splitext(p)[0]


def get_folder(path: typing.Union[pathlib.Path, str]):
    return os.path.dirname(os.path.abspath(path))


def get_basename(path: FilePath):
    return strip_extension(os.path.basename(os.path.abspath(path)))


def get_extension(path: FilePath):
    return os.path.splitext(path)[-1][1:]


def pkl_dump(o, fn: FilePath, print_timing=True) -> None:
    ts1 = time.perf_counter()
    with open(fn, "wb") as f:
        pickle.dump(o, f)
    ts2 = time.perf_counter()
    if print_timing:
        print("dumped {} in: {:.4f} s".format(os.path.basename(fn), ts2 - ts1))


def pkl_load(fn: FilePath, print_timing=True):
    ts1 = time.perf_counter()
    with open(fn, "rb") as f:
        d = pickle.load(f)
    ts2 = time.perf_counter()
    if print_timing:
        print("loaded {} in: {:.4f} s".format(os.path.basename(fn), ts2 - ts1))
    return d


def createdir(directory):
    """
    mkdir
    :param directory:
    :return:
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def removefile(what: FilePath):
    try:
        os.remove(what)
    except OSError:
        pass


def removefolder(what: FilePath):
    try:
        os.rmdir(what)
    except OSError:
        pass


def read_smi(smifile: FilePath):
    with open(smifile, "r") as f:
        lines = f.readlines()
    return [smi.strip() for smi in lines if len(smi.strip()) > 0]


def write_smi(smis: list[str], outfile: FilePath):
    with open(outfile, "w") as f:
        for smi in smis:
            f.write(smi + "\n")
