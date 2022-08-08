import json
import logging
import os
import os.path
import pathlib
import pickle
import time
import typing
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.request import urlretrieve

import monty.json
from fake_useragent import UserAgent
from tqdm import tqdm

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


def download_file(url: str, destination: FilePath = None, progress_bar=True):
    def my_hook(t):
        last_b = [0]

        def inner(b=1, bsize=1, tsize=None):
            if tsize is not None:
                t.total = tsize
            if b > 0:
                t.update((b - last_b[0]) * bsize)
            last_b[0] = b

        return inner

    try:
        if progress_bar:
            with tqdm(unit='B', unit_scale=True, miniters=1, desc=destination) as t:
                filename, _ = urlretrieve(url, filename=destination, reporthook=my_hook(t))
        else:
            filename, _ = urlretrieve(url, filename=destination)
    except (HTTPError, URLError, ValueError) as e:
        raise e
    return filename


def download_file_fake_agent(url, saveas: FilePath):
    ua = UserAgent()
    fp = urlopen(Request(url, headers={'User-Agent': ua.chrome}))
    with open(saveas, 'wb') as f:
        f.write(fp.read())


def remove_url_query(url):
    return urlparse(url)._replace(query=None).geturl()
