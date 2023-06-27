import os
import sys
import re


class Processor:
    _insert = re.compile(r"^#addr\s+([^<>:\"\|\?]+?)$")
    _insert_cool = re.compile(r"^#add\s+([^<>:\"\|\?]+?)$")
    __slots__ = ['output']

    def _insert_directive(self, line: str):
        return self._generic_directive('#add ', line.strip()) + '.pnml'

    def _generic_directive(self, prefix, line: str):
        if line.startswith(prefix):
            content = line[len(prefix):].strip()
            return content
        return None

    def _insert_raw_directive(self, line: str):
        return self._generic_directive('#addr ', line.strip())

    def __init__(self):
        self.output = ''

    def process(self, input_fname: str) -> 'Processor':
        if not os.path.exists(input_fname):
            raise Exception(input_fname)
        with open(input_fname, 'r') as file:
            lines = file.readlines()

        for line in lines:
            filename = self._insert_directive(line) \
                or self._insert_raw_directive(line)
            if not filename:
                self.output += line
                continue

            if not os.path.exists(filename):
                raise Exception(filename)
            with open(filename) as file:
                self.output += file.read() + '\n'

        return self

    def into(self, out_fname: str):
        with open(out_fname, 'w') as f:
            f.write(self.output)

    def get(self):
        return self.output


class Program:
    @staticmethod
    def main():
        match sys.argv[1:]:
            case [inp_fname, out_fname]:
                Processor().process(inp_fname).into(out_fname)
            case ['help']:
                Program._usage()
            case _:
                Program._otherwise()

    @staticmethod
    def _usage():
        raise NotImplementedError

    @staticmethod
    def _otherwise(args: list[str]):
        print("Exception: ", end='')
        print("No input files"
              if len(args) == 0 else
              "Wrong number of input files, expected 2")
        print("Use 'help' to get help")


if __name__ == '__main__':
    Program.main()
