from dataclasses import dataclass
from pathlib import Path
import re
import shutil

# \subfile{content/1/section.tex}
RE_PART = re.compile(r"\\subfile{content/(?P<part>\d+)/section.tex}")
# \subfile{content/1/chapter1/0.tex}
RE_CH_SEC = re.compile(
    r"\\subfile{content/(?P<part>\d+)/chapter(?P<ch>\d+)/(?P<sec>\d+).tex}"
)


@dataclass
class Part:
    part_num: int
    title: str

    def old_path(self) -> Path:
        path = Path(f"content/{self.part_num}/section.tex")
        assert path.exists()
        return path

    def new_path(self):
        path = Path(f"content/part{self.part_num}.tex")
        return path
        path = Path(f"content/part{self.part_num}_modify.tex")
        return path


@dataclass
class Chapter:
    part_num: int
    ch_num: int
    title: str

    def old_path(self) -> Path:
        path = Path(f"content/{self.part_num}/chapter{self.ch_num}/0.tex")
        assert path.exists()
        return path

    def new_path(self):
        path = Path(f"content/part{self.part_num}/ch{self.ch_num}.tex")
        return path

    def old_folder(self):
        path = Path(f"content/{self.part_num}/chapter{self.ch_num}")
        return path

    def new_folder(self):
        path = Path(f"content/part{self.part_num}/ch{self.ch_num}")
        return path


@dataclass
class Section:
    part_num: int
    ch_num: int
    sec_num: int
    title: str

    def old_path(self) -> Path:
        path = Path(f"content/{self.part_num}/chapter{self.ch_num}/{self.sec_num}.tex")
        assert path.exists()
        return path

    def new_path(self):
        path = Path(
            f"content/part{self.part_num}/ch{self.ch_num}/sec{self.sec_num}.tex"
        )
        return path


curr_part = curr_ch = None

def modify_file(sth: Part | Chapter | Section):
    global curr_part, curr_ch
    if not sth.new_path().parent.exists():
        sth.new_path().parent.mkdir()
    match sth:
        case Part(_):
            curr_part = sth
            content = f"\\part{{{sth.title}}}\n" + sth.old_path().read_text()
            sth.new_path().write_text(content)
        case Chapter(_):
            curr_ch = sth
            content = f"\\chapter{{{sth.title}}}\n" + sth.old_path().read_text()
            sth.new_path().write_text(content)
            with curr_part.new_path().open("a") as f:
                f.write(f"\n\\subfile{{part{sth.part_num}/ch{sth.ch_num}.tex}}")
            if (sth.old_folder() / "images").exists():
                (sth.new_folder() / "images").mkdir(exist_ok=True)
                for img in (sth.old_folder() / "images").iterdir():
                    shutil.copy(img, sth.new_folder() / "images")
        case Section(_):
            content = f"\\section{{{sth.title}}}\n" + sth.old_path().read_text()
            sth.new_path().write_text(content)
            with curr_ch.new_path().open("a") as f:
                f.write(f"\n\\subfile{{ch{sth.ch_num}/sec{sth.sec_num}.tex}}")


def parse_toc(s: str):
    for line in s.splitlines():
        if "%" in line:
            continue
        if "\\section*" in line:
            title = line.split("：")[1].strip("}")
        if "\\subsection*" in line:
            title = line.split("0.5cm")[1].strip("}")
        if "\\subsubsection*" in line:
            title = line.split("0.2cm")[1].strip("}")
        if "\\subfile" in line:
            if (match := RE_PART.search(line)) is not None:
                yield Part(int(match.group("part")), title)
            elif (match := RE_CH_SEC.match(line)) is not None:
                sec = int(match.group("sec"))
                if sec == 0:
                    yield Chapter(
                        int(match.group("part")), int(match.group("ch")), title
                    )
                else:
                    yield Section(
                        int(match.group("part")), int(match.group("ch")), sec, title
                    )


if __name__ == "__main__":
    for part in parse_toc(Path("toc").read_text()):
        modify_file(part)
