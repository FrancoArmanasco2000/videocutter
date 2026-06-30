import ffmpeg


class Cutter:
    def cut(self, source: str, dest: str, start: float, end: float) -> None:
        if end <= start:
            raise ValueError(f"End time ({end}s) must be greater than start ({start}s).")

        duration = end - start

        (
            ffmpeg
            .input(source, ss=start, t=duration)
            .output(dest, c="copy")
            .overwrite_output()
            .run(quiet=True)
        )
