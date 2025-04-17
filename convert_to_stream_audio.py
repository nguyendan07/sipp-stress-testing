import ffmpeg
import os
import sys
from pathlib import Path


def convert_audio(input_path, output_dir):
    codecs = {
        'pcma': ('alaw', 'g711a.wav'),        # G.711 A-law
        'pcmu': ('mulaw', 'g711u.wav'),       # G.711 µ-law
        'g722': ('g722', 'g722.wav'),
        'ilbc': ('ilbc', 'ilbc.wav'),
        # 'g729': ('g729', 'g729.wav'),
    }

    os.makedirs(output_dir, exist_ok=True)

    for codec_key, (codec_name, extension) in codecs.items():
        out_file = output_dir / f"{input_path.stem}_{extension}"
        try:
            (
                ffmpeg
                .input(str(input_path))
                .output(str(out_file), acodec=codec_name, ac=1, ar=8000)
                .overwrite_output()
                .run(quiet=True)
            )
            print(f"[✓] {input_path.name} → {codec_key.upper()} → {out_file.name}")
        except ffmpeg.Error as e:
            print(f"[✗] Failed {input_path.name} to {codec_key.upper()}: {e.stderr.decode()}")


def convert_directory(input_dir):
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        print(f"[!] Directory not found: {input_dir}")
        return

    output_dir = input_dir / "converted"
    wav_files = list(input_dir.glob("*.wav"))

    if not wav_files:
        print("[!] No .wav files found in the directory.")
        return

    print(f"[•] Converting {len(wav_files)} .wav files in '{input_dir}'...")
    for wav_file in wav_files:
        convert_audio(wav_file, output_dir)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_audio_batch.py <input_directory>")
        sys.exit(1)

    convert_directory(sys.argv[1])
