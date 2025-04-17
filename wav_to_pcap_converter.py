#!/usr/bin/env python3
"""
WAV to PCAP Converter for SIPp Testing
--------------------------------------
This script converts WAV audio files to PCAP format for use with SIPp.
It properly encapsulates the audio data in RTP packets as required by SIPp.
"""

import os
import sys
import wave
import struct
import argparse
from scapy.all import wrpcap, Ether, IP, UDP, Raw


class RTPPacket:
    """Class to create RTP packet headers and encapsulate audio data"""

    def __init__(self, payload_type=0, seq_num=1, timestamp=0, ssrc=0xABCDEF01):
        self.version = 2  # RTP version 2
        self.padding = 0
        self.extension = 0
        self.csrc_count = 0
        self.marker = 0
        self.payload_type = payload_type  # 0 for PCMU/G.711 μ-law
        self.seq_num = seq_num
        self.timestamp = timestamp
        self.ssrc = ssrc  # Synchronization source identifier

    def build_header(self):
        """Build the 12-byte RTP header"""
        # First byte: V=2|P=0|X=0|CC=0
        first_byte = (
            (self.version << 6)
            | (self.padding << 5)
            | (self.extension << 4)
            | self.csrc_count
        )
        # Second byte: M=0|PT
        second_byte = (self.marker << 7) | self.payload_type

        # Pack the header in network byte order (big-endian)
        header = struct.pack(
            "!BBHII", first_byte, second_byte, self.seq_num, self.timestamp, self.ssrc
        )
        return header


def convert_wav_to_pcap(
    wav_file,
    pcap_file,
    src_ip="210.245.0.142",
    dst_ip="118.69.115.150",
    src_port=18130,
    dst_port=18130,
    payload_type=0,
    packet_size=160,
):
    """
    Convert a WAV file to PCAP format with RTP packets

    Args:
        wav_file (str): Path to input WAV file
        pcap_file (str): Path to output PCAP file
        src_ip (str): Source IP address for the packets
        dst_ip (str): Destination IP address for the packets
        src_port (int): Source UDP port
        dst_port (int): Destination UDP port
        payload_type (int): RTP payload type (0=PCMU, 8=PCMA)
        packet_size (int): Audio data bytes per packet
    """
    if not os.path.exists(wav_file):
        print(f"Error: File {wav_file} not found")
        return False

    try:
        # Open and read the WAV file
        with wave.open(wav_file, "rb") as wav:
            print(f"Processing: {wav_file}")
            print(f"  - Channels: {wav.getnchannels()}")
            print(f"  - Sample width: {wav.getsampwidth()} bytes")
            print(f"  - Frame rate: {wav.getframerate()} Hz")
            print(f"  - Total frames: {wav.getnframes()}")

            # For proper RTP timing with G.711
            samples_per_packet = packet_size
            sampling_freq = wav.getframerate()

            # Ensure mono audio for RTP
            if wav.getnchannels() != 1:
                print("Warning: WAV file is not mono. This may cause issues with SIPp.")

            # Read all audio data
            audio_data = wav.readframes(wav.getnframes())

            # Create packets list for scapy
            packets = []
            seq_num = 1
            timestamp = 0

            # Process audio data in chunks
            for i in range(0, len(audio_data), packet_size):
                chunk = audio_data[i : i + packet_size]

                # If the last chunk is smaller than packet_size, pad it with silence
                if len(chunk) < packet_size:
                    padding_needed = packet_size - len(chunk)
                    chunk += b"\x7f" * padding_needed  # G.711 silence value

                # Create RTP packet
                rtp = RTPPacket(
                    payload_type=payload_type, seq_num=seq_num, timestamp=timestamp
                )
                rtp_header = rtp.build_header()
                rtp_payload = rtp_header + chunk

                # Create network packet with scapy layers
                packet = (
                    Ether()
                    / IP(src=src_ip, dst=dst_ip)
                    / UDP(sport=src_port, dport=dst_port)
                    / Raw(load=rtp_payload)
                )

                packets.append(packet)

                # Update for next packet
                seq_num += 1
                if seq_num > 65535:  # RTP sequence number is 16 bits
                    seq_num = 0

                timestamp += samples_per_packet

            # Write the packets to a PCAP file
            wrpcap(pcap_file, packets)
            print(f"Created: {pcap_file} ({len(packets)} RTP packets)")
            return True

    except Exception as e:
        print(f"Error processing {wav_file}: {str(e)}")
        return False


def batch_convert(input_dir, output_dir, file_pattern=None):
    """
    Convert all WAV files in a directory to PCAP format

    Args:
        input_dir (str): Directory containing WAV files
        output_dir (str): Directory to save PCAP files
        file_pattern (str, optional): Only process files matching this pattern
    """
    if not os.path.exists(input_dir):
        print(f"Input directory {input_dir} not found")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    success_count = 0
    failed_count = 0

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".wav"):
            continue

        if file_pattern and file_pattern not in filename:
            continue

        wav_path = os.path.join(input_dir, filename)
        pcap_path = os.path.join(output_dir, filename.replace(".wav", ".pcap"))

        if convert_wav_to_pcap(wav_path, pcap_path):
            success_count += 1
        else:
            failed_count += 1

    print(f"\nConversion complete: {success_count} successful, {failed_count} failed")


def main():
    parser = argparse.ArgumentParser(
        description="Convert WAV files to PCAP format for SIPp"
    )

    parser.add_argument(
        "-i", "--input", required=True, help="Input WAV file or directory"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output PCAP file or directory"
    )
    parser.add_argument(
        "-p", "--pattern", help="Process only files matching this pattern"
    )
    parser.add_argument(
        "--src-ip",
        default="192.168.1.1",
        help="Source IP address (default: 192.168.1.1)",
    )
    parser.add_argument(
        "--dst-ip",
        default="192.168.1.2",
        help="Destination IP address (default: 192.168.1.2)",
    )
    parser.add_argument(
        "--src-port", type=int, default=10000, help="Source UDP port (default: 10000)"
    )
    parser.add_argument(
        "--dst-port",
        type=int,
        default=20000,
        help="Destination UDP port (default: 20000)",
    )
    parser.add_argument(
        "--payload-type",
        type=int,
        default=0,
        help="RTP payload type: 0=PCMU, 8=PCMA (default: 0)",
    )
    parser.add_argument(
        "--packet-size",
        type=int,
        default=160,
        help="Audio bytes per packet (default: 160)",
    )

    args = parser.parse_args()

    # Check if input is a file or directory
    if os.path.isdir(args.input):
        batch_convert(args.input, args.output, args.pattern)
    else:
        # Ensure output directory exists
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        success = convert_wav_to_pcap(
            args.input,
            args.output,
            src_ip=args.src_ip,
            dst_ip=args.dst_ip,
            src_port=args.src_port,
            dst_port=args.dst_port,
            payload_type=args.payload_type,
            packet_size=args.packet_size,
        )
        if success:
            print("Conversion completed successfully")
        else:
            print("Conversion failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
