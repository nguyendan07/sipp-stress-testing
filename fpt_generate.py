import random
import time
import urllib.request
import os
import requests

# Cấu hình API
url = 'https://api.fpt.ai/hmi/tts/v5'
API_KEY = ''  # Thay thế bằng API key của bạn

def tts(name, voice, payload, output_dir='audio_output'):
    """
    Chuyển đổi văn bản thành giọng nói bằng API FPT.AI
    
    Args:
        name (str): Tên file output
        voice (str): Loại giọng đọc
        payload (str): Nội dung văn bản cần chuyển đổi
        output_dir (str): Thư mục lưu file audio
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    # Tạo thư mục output nếu chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Chuẩn bị headers
    headers = {
        'api-key': API_KEY,
        'speed': str(round(random.uniform(0.8, 1.2), 1)),  # Tốc độ ngẫu nhiên từ 0.8-1.2
        'voice': voice,
        'format': 'wav'
    }
    
    try:
        # Gửi request đến API
        response = requests.request('POST', url, data=payload.encode('utf-8'), headers=headers)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        
        data_res = response.json()
        
        # Kiểm tra kết quả từ API
        if not data_res or not isinstance(data_res, dict) or "async" not in data_res:
            print(f"Lỗi khi xử lý '{name}': {data_res.get('message', 'Không có phản hồi hợp lệ')}")
            return False
        
        audio_url = data_res['async']
        if not audio_url.endswith('.wav'):
            print(f"URL không hợp lệ cho '{name}': {audio_url}")
            return False
            
        print(f"Đang xử lý '{name}' - URL: {audio_url}")
        
        # Thời gian chờ tỷ lệ với độ dài văn bản
        wait_time = 2 + len(payload) * 0.05  # 2 giây cơ bản + thêm thời gian theo độ dài
        print(f"Chờ {wait_time:.1f} giây để xử lý...")
        time.sleep(wait_time)
        
        # Tải file âm thanh
        output_path = os.path.join(output_dir, f'{name}.wav')
        urllib.request.urlretrieve(audio_url, output_path)
        print(f"Đã tạo file: {output_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối API cho '{name}': {e}")
        return False
    except urllib.error.URLError as e:
        print(f"Lỗi tải file cho '{name}': {e}")
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi xử lý '{name}': {e}")
        return False

def batch_generate(category, phrases, voices):
    """
    Tạo file audio cho một danh sách các cụm từ
    
    Args:
        category (str): Tên danh mục
        phrases (list): Danh sách các cụm từ
        voices (list): Danh sách giọng đọc
    """
    print(f"\n--- Đang xử lý danh mục: {category} ({len(phrases)} cụm từ) ---")
    success_count = 0
    
    for i, phrase in enumerate(phrases):
        voice = random.choice(voices)
        if tts(f'{category}_{i}', voice, phrase):
            success_count += 1
    
    print(f"Hoàn thành {category}: {success_count}/{len(phrases)} file")

# Danh sách các cụm từ
renewal = [
    "Tôi muốn gia hạn đóng tiền cước.",
    "Tôi chưa thanh toán ngay được, tôi muốn gia hạn thêm.",
    "Gia hạn thanh toán",
    "Tôi muốn gia hạn.",
    "Gia hạn.",
    "Đồng ý gia hạn thêm.",
    "Gia hạn thanh toán cho tôi.",
    "Giờ tôi muốn gia hạn thêm.",
    "Tôi muốn gia hạn thêm thì phải làm sao?",
]

confirm = [
    "Okey.",
    "Đúng rồi.",
    "Được rồi.",
    "Tôi biết rồi.",
    "Tôi xác nhận.",
    "Tôi đồng ý.",
    "Vâng.",
    "Được",
    "Hiểu rồi",
]

agent = [
    "Cho tôi gặp nhân viên tư vấn.",
    "Tôi muốn gặp người hỗ trợ.",
    "Tôi muốn nói chuyện với tổng đài viên.",
    "Kết nối với tổng đài viên giúp tôi.",
    "Gặp nhân viên.",
    "Ai có thể hỗ trợ tôi.",
    "Liên hệ với tổng đài viên.",
    "Chuyển máy cho nhân viên hỗ trợ.",
    "Tôi chưa rõ , cần gặp người hỗ trợ thêm",
    "Tôi chưa hiểu, cho tôi gặp tổng đài viên.",
]

# Danh sách giọng đọc
voices = [
    "banmai", "thuminh", "myan", "giahuy", "ngoclam", "leminh", "minhquang", "linhsan", "lannhi"
]

# Chạy chương trình chính
if __name__ == "__main__":
    # Tạo thư mục output
    output_dir = "audio_files"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Xử lý từng danh mục
    batch_generate("renewal", renewal, voices)
    batch_generate("confirm", confirm, voices)
    batch_generate("agent", agent, voices)
    
    print("\nĐã hoàn thành tất cả các tác vụ!")
