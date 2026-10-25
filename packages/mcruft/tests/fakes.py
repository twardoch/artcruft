# this_file: packages/mcruft/tests/fakes.py
import mcruft
from PIL import Image


class Fake(mcruft.Engine):
    name, kind = "fake", "native"

    def __init__(self, *caps):
        self.caps, self.calls = caps, []

    def available(self):
        return True

    def version(self):
        return "1"

    def capabilities(self):
        return [mcruft.Capability(*c, "tested") for c in self.caps]

    def run(self, op, src, dst, *, policy, **opts):
        self.calls.append((op, src, dst, policy, opts))
        outputs = [dst]
        if dst.suffix == ".png":
            outputs = [dst.with_name(f"{dst.stem}-{opts['pages'][0]:04d}.png")]
            Image.new("RGB", (20, 30)).save(outputs[0])
        else:
            dst.write_bytes(src.read_bytes())
        return mcruft.Report(op, policy, self.name, "1", outputs, [mcruft.Loss("layout", op)], [op])
