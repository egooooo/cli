from terminaltables import AsciiTable
import collections
import enum
import typing
import dataclasses
import sys
import os


def sizeof_fmt(num, suffix='B'):
    if num is None:
        return "unknown size"
    for unit in ('', 'Kb', 'Mb', 'Gb', 'Tb', 'Pb', 'Eb', 'Zb'):
        if abs(num) < 1000:
            if unit != '':
                return "%3.1f%s" % (num, unit)
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1000
    return "%.1f%s%s" % (num, 'Yb', suffix)


@dataclasses.dataclass
class FileStats:
    code: int = 0
    comments: int = 0
    blank: int = 0


@dataclasses.dataclass
class TotalStats:
    code: int = 0
    comments: int = 0
    blank: int = 0
    size: int = 0
    files: int = 0


def analyze_python(lines: typing.List[str]) -> FileStats:
    s = FileStats()
    for line in lines:
        if line.strip().startswith('"""'):
            s.comments += 1
        for symbol in line:
            if symbol == "#":
                s.comments += 1

        if line == "\n" or line == "\r\n":
            s.blank += 1
        else:
            s.code += 1
    return s


def analyze_json(lines: typing.List[str]) -> FileStats:
    s = FileStats()
    for line in lines:
        if line == "\n" or line == "\r\n":
            s.blank += 1
        else:
            s.code += 1
    return s


def analyze_html(lines: typing.List[str]) -> FileStats:
    s = FileStats()
    for line in lines:
        if line.strip().startswith('<!--'):
            s.comments += 1
        if line == "\n" or line == "\r\n":
            s.blank += 1
        else:
            s.code += 1
    return s


class FileType(enum.Enum):
    UNKNOWN = 'UNKNOWN'

    PYTHON = 'Python'
    JSON = 'Json'
    HTML = 'html'


extensions = {
    'py': FileType.PYTHON,
    'json': FileType.JSON,
    'html': FileType.HTML,
}

analyzers = {
    FileType.PYTHON: analyze_python,
    FileType.JSON: analyze_json,
    FileType.HTML: analyze_html,
}


def walk(path) -> typing.Dict[FileType, TotalStats]:
    result = collections.defaultdict(TotalStats)

    for root, dirs, files in os.walk(path):
        for name in files:
            file_ext = name.split('.')[-1]
            file_type = extensions.get(file_ext, FileType.UNKNOWN)
            result[file_type].size += os.path.getsize(os.path.join(root, name))
            result[file_type].files += 1

            analyze = analyzers.get(file_type)
            if analyze is None:
                continue

            with open(os.path.join(root, name), "r") as f:
                lines = f.readlines()
                file_stats = analyze(lines)
                result[file_type].code += file_stats.code
                result[file_type].comments += file_stats.comments
                result[file_type].blank += file_stats.blank

    return dict(result)


def main():
    path = sys.argv[1]
    result = walk(path)

    table_data = [
        ['Language', 'Code', 'Comment', 'Blank', 'Files', 'Size']
    ]

    for lang, stats in result.items():
        table_data.append(
            [f'{lang.value}', f'{stats.code}', f'{stats.comments}',
             f'{stats.blank}', f'{stats.files}', f'{sizeof_fmt(stats.size)}']
        )

    table = AsciiTable(table_data)
    print(f"{table.table}")


if __name__ == '__main__':
    main()
