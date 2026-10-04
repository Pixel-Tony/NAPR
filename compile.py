#!/usr/bin/python3
import subprocess
import os.path as path
import sys
import shutil
import re

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler, FileModifiedEvent, DirModifiedEvent)


def abspath(filename: str):
    return path.abspath(path.join(path.dirname(__file__), filename))


partials = [
    "src/header.pnml",
    "src/wagon/Budd Amfleet.pnml",
    "src/steam/PRR tenders.pnml",
    "src/steam/PRR K4s.pnml"
    # "src/EMU/MP54.pnml",
    # "src/EMU/Budd Metroliner I.pnml",
    # "src/EMU/Arrow III.pnml",
    # "src/Diesel/SPV-2000.pnml",
    # "src/Push-Pull.pnml",
    # "src/Push-Pull 2.pnml",
    # "src/Diesel/EMD F3.pnml",
    # "src/EMU/Highliner I.pnml",
    # "src/EMU/Highliner II.pnml",
    # "src/Wagons/Horizon.pnml",
    # "src/Diesel/EMD E7.pnml",
    # "src/Diesel/EMD E8.pnml",
    # "src/Diesel/EMD E9.pnml",
    # "src/Diesel/Budd RDC.pnml",
    # "src/EMU/Silverliner II.pnml",
    # "src/EMU/MN M2.pnml",
    # "src/EMU/Canada MR-90.pnml",
    # "src/Wagons/Budd Superliner I.pnml",
    # "src/Push-Pull 3.pnml",
    # "src/DMU/RTG Turboliner.pnml",
    # "src/Diesel/ALCO PA.pnml",
    # "src/EMU/MN M7.pnml",
    # "src/EMU/MN M8.pnml",
    # "src/EMU/Acela Express.pnml",
    # "src/EMU/Canada CN EMU.pnml",
    # "src/Wagons/NYC Heavyweight.pnml",
    # "src/DMU/Pioneer Zephyr.pnml",
    # "src/Diesel/EMD F7.pnml",
    # "src/Wagons/NYC 20th ltd.pnml",
    # "src/Wagons/Budd Lightweight.pnml",
    # "src/Wagons/Amtrak Baggage.pnml",
    # "src/Diesel/EMD FP45.pnml",
    # "src/Diesel/EMD F9.pnml",
    # "src/Steam/SP GS-4.pnml",
    # "src/Electric/PRR GG1.pnml",
    # "src/DMU/UAC Turbotrain.pnml",
    # "src/Wagons/The Canadian.pnml",
    # "src/Steam/NYC Hudson.pnml",
    # "src/EMU/Erie Lackawanna.pnml",
    # "src/Electric/NYC S-Motor.pnml",
    # "src/Steam/PRR K4s.pnml",
    # "src/Wagons/PRR HW.pnml",
    # "src/EMU/Budd M1(a)-M3(a).pnml",
    # "src/refined/sort.pnml"
]


partials = [abspath(item) for item in partials]


class WatchHandler(FileSystemEventHandler):
    def __init__(self, partials: list[str], newgrf_dir: str | None):
        super().__init__()
        self.partials = {partial: path.getmtime(partial)
                         for partial in partials}
        self.newgrf_dir = newgrf_dir
        self.recompile(reassemble=True, write=True)

    def find_sprites(self, assembly: str):
        return map(abspath,
                   re.findall(r'(?<=")[a-zA-Z_0-9./ ]+.png(?=")', assembly))

    def on_modified(self, event: FileModifiedEvent):
        if event.is_directory:
            return
        filepath = abspath(event.src_path)
        if (filepath in self.partials
            and self.check_newer(filepath, self.partials)) \
                or filepath.endswith("compile.py"):
            print(f"Partial '{filepath}' modified, "
                  "running assembly and recompiling...")
            self.recompile(reassemble=True, write=True)

        if filepath in self.sprites:
            if not self.check_newer(filepath, self.sprites):
                return
            print(f"Graphics file '{filepath}' modified, recompiling...")
            self.recompile(reassemble=False, write=False)

        if filepath.endswith('.lng'):
            print(f"Language file '{filepath}' modified, recompiling...")
            self.recompile(reassemble=False, write=False)

    def check_newer(self, filepath: str, collection: dict[str, float]):
        mtime = path.getmtime(filepath)
        if mtime <= collection[filepath]:
            return False
        collection[filepath] = mtime
        return True

    def recompile(self, reassemble: bool, write: bool):
        if reassemble:
            self.assembly = get_assembly()
            self.sprites = {sprite: path.getmtime(sprite)
                            for sprite in self.find_sprites(self.assembly)}

        naprs_compile(self.assembly if write else None, self.newgrf_dir)


def watch(newgrf_dir: str = None):
    handler = WatchHandler(partials, newgrf_dir)
    observer = Observer()
    observer.schedule(handler, ".", recursive=True,
                      event_filter=[FileModifiedEvent])
    print("Watching the source directory for file changes...")
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        print(flush=True)
        print("Stopping the watcher...")
    finally:
        observer.stop()
        observer.join()


def get_assembly():
    def load(filename: str):
        with open(filename, "r", encoding="utf8") as file:
            return file.read().strip()
    return "\n".join(load(filename) for filename in partials)


def naprs_compile(assembly: str = None, newgrf_dir: str = None):
    if assembly is not None:
        with open("NAPR.nml", "w", encoding="utf8") as file:
            file.write(assembly)

    subprocess.run(["nmlc", "-c", "--grf", "NAPR.grf", "NAPR.nml"])
    if newgrf_dir is not None:
        subprocess.run(["cp", "NAPR.grf", newgrf_dir])


def print_help():
    print("Usage: compile.py [help | --watch] [NEWGRFDIR]\n"
          "assemble full file from partials and compile\n\n"
          "CMD can be one of:\n"
          " help        display this message \n"
          " --watch     watch for file changes and recompile"
          " NEWGRFDIR   optional newgrf directory to copy result to\n\n"
          "without arguments assembles and compiles the result")


def main(argv):
    watch_ = False
    newgrf_dir = None
    for arg in argv:
        if newgrf_dir == "":
            newgrf_dir = arg
            assert path.isdir(newgrf_dir), "Not a directory"
            continue
        match arg:
            case "help" | "--help" | "-h":
                return print_help()
            case "--watch":
                assert not watch_, "Duplicate 'watch' argument"
                watch_ = True
                newgrf_dir = ""
            case _:
                raise ValueError(f"Unexpected argument {arg}")

    newgrf_dir = newgrf_dir or None
    if watch_:
        return watch(newgrf_dir=newgrf_dir)
    return naprs_compile(assemble=get_assembly())


if __name__ == "__main__":
    main(sys.argv[1:])
