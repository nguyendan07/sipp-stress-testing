import subprocess
import os
import shutil
import argparse
import sys

def check_ffmpeg():
    """Kiểm tra xem ffmpeg có được cài đặt và nằm trong PATH không."""
    if shutil.which("ffmpeg") is None:
        print("LỖI: FFmpeg không được tìm thấy. Hãy cài đặt FFmpeg và đảm bảo nó nằm trong PATH hệ thống.", file=sys.stderr)
        return False
    print("Thông tin: FFmpeg đã được tìm thấy.")
    return True

def convert_audio(input_wav_path, output_path, codec):
    """
    Chuyển đổi file WAV sang định dạng audio khác sử dụng FFmpeg.

    Args:
        input_wav_path (str): Đường dẫn đến file WAV đầu vào.
        output_path (str): Đường dẫn đến file audio đầu ra.
        codec (str): Tên codec mong muốn ('pcma', 'pcmu', 'g722', 'ilbc', 'g729').
                    Phân biệt chữ hoa/thường sẽ được bỏ qua.

    Returns:
        bool: True nếu thành công, False nếu thất bại.

    Raises:
        FileNotFoundError: Nếu file WAV đầu vào không tồn tại (ít xảy ra nếu gọi từ batch).
        ValueError: Nếu codec không được hỗ trợ trong script này.
        RuntimeError: Nếu lệnh ffmpeg thất bại.
    """
    if not os.path.exists(input_wav_path):
        print(f"LỖI: File đầu vào không tồn tại: {input_wav_path}", file=sys.stderr)
        # raise FileNotFoundError(f"Lỗi: File đầu vào không tồn tại: {input_wav_path}") # Không raise để batch tiếp tục
        return False

    # --- Chuẩn bị lệnh FFmpeg ---
    ffmpeg_cmd = ["ffmpeg", "-y", "-i", input_wav_path]
    codec_lower = codec.lower()
    options = []

    # --- Cấu hình tùy chọn cho từng codec ---
    if codec_lower == 'pcma':
        options = ["-ar", "8000", "-ac", "1", "-acodec", "pcm_alaw"]
        print(f"   -> Đang chuyển đổi sang PCMA (A-law), 8kHz, Mono...")
    elif codec_lower == 'pcmu':
        options = ["-ar", "8000", "-ac", "1", "-acodec", "pcm_mulaw"]
        print(f"   -> Đang chuyển đổi sang PCMU (μ-law), 8kHz, Mono...")
    elif codec_lower == 'g722':
        options = ["-ar", "16000", "-ac", "1", "-acodec", "g722"]
        print(f"   -> Đang chuyển đổi sang G.722, 16kHz, Mono...")
    elif codec_lower == 'ilbc':
        options = ["-ar", "8000", "-ac", "1", "-acodec", "ilbc"] # Mặc định 15.2k
        # options = ["-ar", "8000", "-ac", "1", "-acodec", "ilbc", "-ab", "13.3k"] # Chế độ 30ms
        print(f"   -> Đang chuyển đổi sang iLBC, 8kHz, Mono...")
        print("      Lưu ý: FFmpeg cần được biên dịch với hỗ trợ iLBC (libilbc).")
    elif codec_lower == 'g729':
        options = ["-ar", "8000", "-ac", "1", "-acodec", "g729"]
        print(f"   -> Đang chuyển đổi sang G.729, 8kHz, Mono...")
        print("      CẢNH BÁO: Hỗ trợ mã hóa G.729 trong FFmpeg bị giới hạn bởi bằng sáng chế và có thể không có sẵn.")
    else:
        print(f"LỖI: Codec '{codec}' không được hỗ trợ trong script này.", file=sys.stderr)
        # raise ValueError(f"Lỗi: Codec '{codec}' không được hỗ trợ...") # Không raise để batch tiếp tục
        return False

    ffmpeg_cmd.extend(options)
    ffmpeg_cmd.append(output_path)

    # --- Thực thi lệnh FFmpeg ---
    try:
        # print(f"   Đang thực thi: {' '.join(ffmpeg_cmd)}") # Bỏ comment nếu muốn xem lệnh đầy đủ
        process = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        # print(f"   Chuyển đổi thành công: {os.path.basename(output_path)}") # Thông báo thành công đã có ở hàm gọi
        # print(process.stderr) # Bỏ comment để xem chi tiết output ffmpeg
        return True

    except subprocess.CalledProcessError as e:
        print(f"   LỖI: FFmpeg thất bại khi chuyển đổi sang {codec.upper()} (mã lỗi {e.returncode}).", file=sys.stderr)
        print(f"      Lệnh: {' '.join(e.cmd)}", file=sys.stderr)
        print("      --- FFmpeg stderr ---", file=sys.stderr)
        print(e.stderr.strip(), file=sys.stderr)
        print("      ---------------------", file=sys.stderr)
        if codec_lower == 'g729' and ('Unknown encoder' in e.stderr or 'g729' in e.stderr):
            print("\n      >>> Lỗi có thể do FFmpeg của bạn không được biên dịch với hỗ trợ bộ mã hóa G.729 (libg729).\n", file=sys.stderr)
        # raise RuntimeError(f"FFmpeg command failed: {' '.join(e.cmd)}") from e # Không raise để batch tiếp tục
        return False
    except Exception as e:
      print(f"   LỖI không mong muốn khi chuyển đổi sang {codec.upper()}: {e}", file=sys.stderr)
      # raise e # Không raise để batch tiếp tục
      return False

def batch_convert_folder(input_folder, output_folder, codecs_to_convert):
    """
    Quét thư mục đầu vào, tìm các file .wav và chuyển đổi chúng sang các codec được chỉ định,
    lưu kết quả vào thư mục đầu ra.

    Args:
        input_folder (str): Đường dẫn đến thư mục chứa các file .wav.
        output_folder (str): Đường dẫn đến thư mục để lưu các file đã chuyển đổi.
        codecs_to_convert (list): Danh sách các codec mong muốn (vd: ['pcma', 'pcmu']).
    """
    if not check_ffmpeg():
        sys.exit(1) # Thoát nếu không có ffmpeg

    if not os.path.isdir(input_folder):
        print(f"LỖI: Thư mục đầu vào không tồn tại: {input_folder}", file=sys.stderr)
        sys.exit(1)

    # Tạo thư mục output nếu chưa có, không báo lỗi nếu đã tồn tại
    os.makedirs(output_folder, exist_ok=True)
    print(f"Thông tin: Thư mục đầu ra: {output_folder}")

    # Định nghĩa phần mở rộng file cho output
    output_extensions = {
        "pcma": ".alaw", "pcmu": ".ulaw", "g722": ".g722",
        "ilbc": ".lbc", "g729": ".g729"
    }

    wav_files_found = 0
    successful_conversions = 0
    failed_conversions = 0

    print(f"\nBắt đầu quét thư mục đầu vào: {input_folder}")
    # Duyệt qua tất cả các file trong thư mục đầu vào
    for filename in os.listdir(input_folder):
        input_file_path = os.path.join(input_folder, filename)

        # Chỉ xử lý các file .wav
        if os.path.isfile(input_file_path) and filename.lower().endswith('.wav'):
            wav_files_found += 1
            base_filename = os.path.splitext(filename)[0]
            print(f"\nĐang xử lý file: {filename}")

            # Thực hiện chuyển đổi cho từng codec được yêu cầu
            for codec in codecs_to_convert:
                codec_lower = codec.lower()
                if codec_lower not in output_extensions:
                    print(f"   Cảnh báo: Bỏ qua codec không xác định '{codec}' cho file {filename}", file=sys.stderr)
                    continue

                output_filename = f"{base_filename}_{codec_lower}{output_extensions[codec_lower]}"
                output_file_path = os.path.join(output_folder, output_filename)

                try:
                    if convert_audio(input_file_path, output_file_path, codec_lower):
                        print(f"   -> Thành công: {output_filename}")
                        successful_conversions += 1
                    else:
                        # Lỗi đã được in bên trong convert_audio
                        failed_conversions += 1
                        # Tùy chọn: xóa file output nếu tạo ra nhưng bị lỗi (ffmpeg có thể tạo file 0 byte)
                        if os.path.exists(output_file_path):
                            try:
                                os.remove(output_file_path)
                                print(f"      Đã xóa file output lỗi: {output_filename}")
                            except OSError as remove_err:
                                print(f"      Cảnh báo: Không thể xóa file output lỗi {output_filename}: {remove_err}", file=sys.stderr)

                except Exception as e: # Bắt các lỗi không mong muốn khác từ convert_audio
                    print(f"   LỖI không mong muốn khi xử lý {filename} sang {codec.upper()}: {e}", file=sys.stderr)
                    failed_conversions += 1

    print("\n" + "="*30)
    print("Hoàn tất quá trình chuyển đổi hàng loạt.")
    print(f"Tổng số file .wav tìm thấy: {wav_files_found}")
    print(f"Số lượt chuyển đổi thành công: {successful_conversions}")
    print(f"Số lượt chuyển đổi thất bại: {failed_conversions}")
    print("="*30)

# --- Xử lý tham số dòng lệnh và chạy ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chuyển đổi hàng loạt file .wav sang các codec audio khác bằng FFmpeg.")
    parser.add_argument("input_dir", help="Thư mục chứa các file .wav đầu vào.")
    parser.add_argument("output_dir", help="Thư mục để lưu các file audio đã chuyển đổi.")
    parser.add_argument("-c", "--codecs", nargs='+',
                        default=["pcma", "pcmu", "g722", "ilbc", "g729"],
                        help="Danh sách các codec cần chuyển đổi (ví dụ: pcma pcmu g722). Mặc định là tất cả.")

    # Kiểm tra nếu không có đối số nào được cung cấp
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        # Hướng dẫn sử dụng cơ bản
        print("\nVí dụ sử dụng:")
        print(f"  python {os.path.basename(__file__)} /path/to/wav_files /path/to/output")
        print(f"  python {os.path.basename(__file__)} /path/to/wav_files /path/to/output -c pcma pcmu")
        sys.exit(1)

    args = parser.parse_args()

    # Chuẩn hóa danh sách codec thành chữ thường
    codecs_list = [c.lower() for c in args.codecs]

    batch_convert_folder(args.input_dir, args.output_dir, codecs_list)
