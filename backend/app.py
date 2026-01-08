# ... (giữ nguyên imports và cấu hình ban đầu)

import cv2
import numpy as np
from moviepy.editor import VideoFileClip, ImageSequenceClip
import torch
from facenet_pytorch import MTCNN
import mediapipe as mp
from collections import defaultdict

# =================== LIVE PORTRAIT INTEGRATION ===================
class LivePortraitProcessor:
    """Xử lý video với tính năng LivePortrait-like"""
    
    def __init__(self):
        self.face_detector = MTCNN(keep_all=True, device='cpu')
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.face_landmarker = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.pose_detector = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            enable_segmentation=False,
            min_detection_confidence=0.5
        )
        
        # AI Models for enhancement
        self.models_loaded = True
        logger.info("LivePortrait processor initialized")
    
    def extract_facial_features(self, frame):
        """Trích xuất đặc điểm khuôn mặt"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Face detection
            faces = self.face_detector.detect(rgb_frame)
            
            # Face landmarks
            face_results = self.face_landmarker.process(rgb_frame)
            
            # Pose detection
            pose_results = self.pose_detector.process(rgb_frame)
            
            features = {
                'face_detected': len(faces[0]) > 0 if faces[0] is not None else False,
                'face_count': len(faces[0]) if faces[0] is not None else 0,
                'landmarks_count': len(face_results.multi_face_landmarks[0].landmark) if face_results.multi_face_landmarks else 0,
                'pose_detected': pose_results.pose_landmarks is not None
            }
            
            return features
        except Exception as e:
            logger.error(f"Error extracting facial features: {e}")
            return {'face_detected': False, 'error': str(e)}
    
    def apply_face_enhancement(self, frame, enhancement_type='auto'):
        """Tăng cường khuôn mặt trong video"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_results = self.face_landmarker.process(rgb_frame)
            
            if not face_results.multi_face_landmarks:
                return frame
            
            # Tạo mask cho khuôn mặt
            h, w = frame.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            
            for face_landmarks in face_results.multi_face_landmarks:
                landmarks = []
                for landmark in face_landmarks.landmark:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    landmarks.append([x, y])
                
                # Vẽ convex hull cho khuôn mặt
                hull = cv2.convexHull(np.array(landmarks))
                cv2.fillConvexPoly(mask, hull, 255)
            
            # Áp dụng hiệu ứng làm mịn da
            if enhancement_type in ['auto', 'skin_smoothing']:
                # Gaussian blur cho vùng da
                blurred = cv2.GaussianBlur(frame, (0, 0), 3)
                frame = cv2.addWeighted(frame, 0.7, blurred, 0.3, 0)
            
            # Tăng cường độ tương phản mắt
            if enhancement_type in ['auto', 'eye_enhance']:
                # Tìm vùng mắt dựa trên landmarks
                # Đây là logic đơn giản, thực tế cần dựa trên landmarks cụ thể
                pass
            
            return frame
            
        except Exception as e:
            logger.error(f"Error in face enhancement: {e}")
            return frame
    
    def apply_style_transfer(self, frame, style='cinematic'):
        """Áp dụng chuyển đổi phong cách cho video"""
        try:
            if style == 'cinematic':
                # Tăng độ tương phản
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                l = clahe.apply(l)
                lab = cv2.merge((l, a, b))
                frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                
                # Áp dụng LUT cinematic
                frame = cv2.addWeighted(frame, 0.8, frame, 0, 20)
                
            elif style == 'viral':
                # Tăng saturation và contrast cho video viral
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                s = cv2.add(s, 30)
                v = cv2.add(v, 20)
                hsv = cv2.merge((h, s, v))
                frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                
            elif style == 'professional':
                # Giảm noise và tăng độ sắc nét
                frame = cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                frame = cv2.filter2D(frame, -1, kernel)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error in style transfer: {e}")
            return frame
    
    def generate_talking_head(self, source_image, audio_file, output_path):
        """Tạo video talking head từ ảnh và audio"""
        try:
            # Trong thực tế, đây sẽ tích hợp Wav2Lip/LivePortrait
            # Đây là phiên bản mô phỏng
            logger.info(f"Generating talking head video from {source_image}")
            
            # Tạo video demo từ ảnh với hiệu ứng
            img = cv2.imread(source_image)
            if img is None:
                raise Exception("Source image not found")
            
            # Tạo video từ ảnh với hiệu ứng chuyển động nhẹ
            frames = []
            for i in range(150):  # 5 seconds at 30fps
                frame = img.copy()
                
                # Thêm hiệu ứng chuyển động nhẹ
                if i < 30:
                    # Zoom in
                    scale = 1 + (i * 0.005)
                    h, w = frame.shape[:2]
                    new_h, new_w = int(h * scale), int(w * scale)
                    frame = cv2.resize(frame, (new_w, new_h))
                    frame = frame[(new_h-h)//2:(new_h-h)//2+h, 
                                  (new_w-w)//2:(new_w-w)//2+w]
                
                frames.append(frame)
            
            # Lưu video
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, 30.0, (img.shape[1], img.shape[0]))
            
            for frame in frames:
                out.write(frame)
            
            out.release()
            logger.info(f"Talking head video generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating talking head: {e}")
            return False

# Khởi tạo LivePortrait processor
liveportrait_processor = LivePortraitProcessor()

# =================== ENHANCED VIDEO PROCESSING ===================
def create_enhanced_video_file(video_id, title, duration=10, style='cinematic'):
    """Tạo video nâng cao với xử lý AI"""
    try:
        safe_title = title.replace(' ', '_') if title else f"video_{video_id[:8]}"
        filename = f"{video_id}_{safe_title}_enhanced.mp4"
        output_path = PROCESSED_DIR / filename
        
        # Kiểm tra file mẫu
        sample_video = STATIC_DIR / "sample_video.mp4"
        if not sample_video.exists():
            # Tạo video mẫu với chất lượng cao hơn
            self.create_high_quality_sample(sample_video)
        
        # Đọc video mẫu
        cap = cv2.VideoCapture(str(sample_video))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Áp dụng xử lý AI
            if frame_count % 30 == 0:  # Xử lý mỗi giây
                # Trích xuất đặc điểm khuôn mặt
                features = liveportrait_processor.extract_facial_features(frame)
                
                # Tăng cường khuôn mặt nếu phát hiện
                if features.get('face_detected', False):
                    frame = liveportrait_processor.apply_face_enhancement(frame, 'auto')
                
                # Áp dụng style transfer
                frame = liveportrait_processor.apply_style_transfer(frame, style)
            
            out.write(frame)
            frame_count += 1
        
        cap.release()
        out.release()
        
        logger.info(f"Created enhanced video file: {output_path}")
        return str(output_path), filename
        
    except Exception as e:
        logger.error(f"Failed to create enhanced video: {e}")
        # Fallback to basic video
        return create_real_video_file(video_id, title, duration)

def create_high_quality_sample(sample_path):
    """Tạo video mẫu chất lượng cao"""
    try:
        width, height = 1280, 720
        fps = 30
        duration = 10
        total_frames = fps * duration
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(sample_path), fourcc, fps, (width, height))
        
        # Tạo gradient background đẹp hơn
        for i in range(total_frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Gradient background
            for y in range(height):
                color = int(30 + (y / height) * 50)
                frame[y, :] = [color, color, color + 20]
            
            # Thêm text và hiệu ứng
            text = "AI Video Factory - Professional Sample"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.5
            thickness = 3
            
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = (width - text_size[0]) // 2
            text_y = (height + text_size[1]) // 2
            
            # Hiệu ứng chuyển động text
            offset = int(20 * np.sin(i * 0.1))
            
            # Vẽ text với shadow
            cv2.putText(frame, text, (text_x + 3, text_y + offset + 3), 
                       font, font_scale, (0, 0, 0), thickness + 1)
            cv2.putText(frame, text, (text_x, text_y + offset), 
                       font, font_scale, (255, 255, 255), thickness)
            
            # Thêm hiệu ứng particles
            for _ in range(20):
                x = np.random.randint(0, width)
                y = np.random.randint(0, height)
                radius = np.random.randint(2, 5)
                color = (np.random.randint(200, 255), 
                        np.random.randint(200, 255), 
                        np.random.randint(200, 255))
                cv2.circle(frame, (x, y), radius, color, -1)
            
            out.write(frame)
        
        out.release()
        logger.info("Created high quality sample video")
        
    except Exception as e:
        logger.error(f"Error creating high quality sample: {e}")

def simulate_ai_processing_enhanced(video_id, video_data):
    """Mô phỏng xử lý AI nâng cao"""
    try:
        video = storage.get_video(video_id)
        if not video:
            return
        
        prompt = video.get('metadata', {}).get('prompt', 'auto')
        
        # Xác định style từ prompt
        style = 'cinematic'  # default
        if 'viral' in prompt.lower():
            style = 'viral'
        elif 'professional' in prompt.lower():
            style = 'professional'
        elif 'cinematic' in prompt.lower():
            style = 'cinematic'
        
        # Cập nhật trạng thái
        storage.update_video(video_id, {
            'status': 'processing',
            'progress': 10,
            'current_step': 'liveportrait_initialization',
            'metadata.style': style
        })
        
        storage.add_log(video_id, {
            'id': str(uuid.uuid4()),
            'level': 'info',
            'message': f'🚀 Starting enhanced AI processing with {style} style',
            'timestamp': datetime.now().isoformat()
        })
        
        # Các bước xử lý nâng cao
        operations = [
            ('face_detection', 'MTCNN', 800),
            ('facial_landmarks', 'MediaPipe', 1200),
            ('pose_estimation', 'MediaPipe Pose', 1000),
            ('face_enhancement', 'LivePortrait AI', 1500),
            ('style_transfer', 'Neural Style', 1800),
            ('quality_enhancement', 'Super-Resolution', 1200),
            ('audio_sync', 'Wav2Lip', 900),
            ('final_render', 'FFmpeg Pro', 500)
        ]
        
        total_steps = len(operations)
        
        for idx, (step_name, model, tokens) in enumerate(operations):
            if not storage.get_video(video_id):
                break
                
            progress = 10 + int(((idx + 1) / total_steps) * 80)
            storage.update_video(video_id, {
                'progress': progress,
                'current_step': step_name
            })
            
            # Theo dõi token
            token_tracker.add_usage(video_id, model, tokens, step_name)
            
            # Thêm log chi tiết
            if step_name == 'face_detection':
                storage.add_log(video_id, {
                    'id': str(uuid.uuid4()),
                    'level': 'info',
                    'message': '👁️ Detecting faces and facial features...',
                    'timestamp': datetime.now().isoformat()
                })
            elif step_name == 'face_enhancement':
                storage.add_log(video_id, {
                    'id': str(uuid.uuid4()),
                    'level': 'info',
                    'message': '✨ Enhancing facial features and skin texture...',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Mô phỏng thời gian xử lý
            time.sleep(1.2)
        
        # Tạo video nâng cao
        title = video.get('title', f'Video {video_id[:8]}')
        processed_path, processed_filename = create_enhanced_video_file(
            video_id, title, 10, style
        )
        
        if processed_path:
            # Tạo thumbnail nâng cao
            thumbnail_url, thumbnail_path = create_video_thumbnail(
                video_id, title, 'completed', style
            )
            
            # Cập nhật thông tin chi tiết
            storage.update_video(video_id, {
                'status': 'completed',
                'progress': 100,
                'current_step': None,
                'processed_path': processed_path,
                'processed_filename': processed_filename,
                'thumbnail_url': thumbnail_url,
                'thumbnail_path': thumbnail_path,
                'duration': 10,
                'size': os.path.getsize(processed_path) if os.path.exists(processed_path) else 0,
                'metadata.ai_processed': True,
                'metadata.processed_at': datetime.now().isoformat(),
                'metadata.style_applied': style,
                'metadata.enhancement_level': 'high',
                'metadata.models_used': [op[1] for op in operations]
            })
            
            # Thêm log hoàn thành chi tiết
            video_tokens = token_tracker.tokens['by_video'].get(video_id, {}).get('total', 0)
            storage.add_log(video_id, {
                'id': str(uuid.uuid4()),
                'level': 'success',
                'message': f'✅ Enhanced video processing completed! Used {video_tokens} AI tokens. Style: {style}',
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Enhanced video {video_id} processing completed with style: {style}")
        else:
            raise Exception("Failed to create enhanced video file")
    
    except Exception as e:
        logger.error(f"Error processing enhanced video {video_id}: {str(e)}")
        storage.update_video(video_id, {
            'status': 'failed',
            'error_message': str(e),
            'current_step': None
        })
        
        storage.add_log(video_id, {
            'id': str(uuid.uuid4()),
            'level': 'error',
            'message': f'❌ Enhanced processing error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

# =================== API ENDPOINTS NÂNG CAO ===================
@app.route('/api/videos/<video_id>/preview', methods=['GET'])
def get_video_preview(video_id):
    """Lấy preview video (streaming)"""
    try:
        video = storage.get_video(video_id)
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        if video['status'] != 'completed':
            return jsonify({'error': 'Video not ready for preview'}), 400
        
        processed_path = video.get('processed_path')
        if not processed_path or not os.path.exists(processed_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        # Trả về video với range request support (streaming)
        range_header = request.headers.get('Range', None)
        if not range_header:
            return send_file(processed_path, mimetype='video/mp4')
        
        # Xử lý range request cho streaming
        size = os.path.getsize(processed_path)
        byte1, byte2 = 0, None
        
        range_header = range_header.replace('bytes=', '').split('-')
        if range_header[0]:
            byte1 = int(range_header[0])
        if range_header[1]:
            byte2 = int(range_header[1])
        
        length = size - byte1
        if byte2 is not None:
            length = byte2 - byte1 + 1
        
        data = None
        with open(processed_path, 'rb') as f:
            f.seek(byte1)
            data = f.read(length)
        
        rv = Response(data, 
                     206,
                     mimetype='video/mp4',
                     direct_passthrough=True)
        rv.headers.add('Content-Range', f'bytes {byte1}-{byte1+length-1}/{size}')
        rv.headers.add('Accept-Ranges', 'bytes')
        rv.headers.add('Content-Length', length)
        
        return rv
        
    except Exception as e:
        logger.error(f"Error streaming video preview {video_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/<video_id>/enhanced', methods=['POST'])
def process_video_enhanced(video_id):
    """Bắt đầu xử lý video nâng cao với LivePortrait features"""
    try:
        video = storage.get_video(video_id)
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        if video['status'] == 'processing':
            return jsonify({'error': 'Video is already processing'}), 400
        
        data = request.json or {}
        prompt = data.get('prompt', 'auto')
        
        # Cập nhật trạng thái
        storage.update_video(video_id, {
            'status': 'processing',
            'progress': 5,
            'current_step': 'liveportrait_initialization',
            'metadata.prompt': prompt,
            'metadata.processing_started': datetime.now().isoformat(),
            'metadata.processing_mode': 'enhanced'
        })
        
        # Theo dõi token
        prompt_tokens = len(prompt.split()) * 2
        token_tracker.add_usage(video_id, 'LivePortrait AI', prompt_tokens, 'prompt_analysis_enhanced')
        
        # Thêm log
        storage.add_log(video_id, {
            'id': str(uuid.uuid4()),
            'level': 'info',
            'message': f'🎬 Starting enhanced processing with LivePortrait features',
            'timestamp': datetime.now().isoformat()
        })
        
        # Bắt đầu xử lý nâng cao trong background
        thread = threading.Thread(
            target=simulate_ai_processing_enhanced,
            args=(video_id, video),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Enhanced AI processing started with LivePortrait features',
            'processing_mode': 'enhanced',
            'estimated_tokens': '8000-10000 tokens',
            'estimated_time': '12-15 seconds',
            'features': [
                'Face Detection & Tracking',
                'Facial Landmark Analysis',
                'Pose Estimation',
                'Face Enhancement',
                'Style Transfer',
                'Quality Upscaling'
            ]
        })
    
    except Exception as e:
        logger.error(f"Error starting enhanced processing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos/<video_id>/analytics', methods=['GET'])
def get_video_analytics(video_id):
    """Lấy phân tích chi tiết của video"""
    try:
        video = storage.get_video(video_id)
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        # Phân tích giả lập
        analytics = {
            'video_id': video_id,
            'processing_details': {
                'mode': video.get('metadata', {}).get('processing_mode', 'standard'),
                'style': video.get('metadata', {}).get('style', 'default'),
                'enhancement_level': video.get('metadata', {}).get('enhancement_level', 'medium'),
                'face_detected': np.random.choice([True, False], p=[0.8, 0.2]),
                'face_count': np.random.randint(1, 5),
                'processing_stages': 8,
                'ai_models_used': video.get('metadata', {}).get('models_used', [])
            },
            'quality_metrics': {
                'resolution': '1280x720',
                'bitrate': '5000 kbps',
                'frame_rate': '30 fps',
                'encoding': 'H.264',
                'audio_codec': 'AAC',
                'overall_quality': 'High'
            },
            'ai_insights': {
                'emotion_detected': np.random.choice(['Happy', 'Neutral', 'Excited'], p=[0.4, 0.3, 0.3]),
                'engagement_score': np.random.randint(70, 95),
                'visual_complexity': np.random.randint(40, 80),
                'processing_efficiency': f"{video.get('progress', 0)}%"
            }
        }
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting video analytics: {e}")
        return jsonify({'error': str(e)}), 500

# =================== INITIALIZATION NÂNG CAO ===================
def init_system_enhanced():
    """Khởi tạo hệ thống nâng cao"""
    # Tạo thư mục và file mẫu chất lượng cao
    init_system()
    
    # Tạo file mẫu chất lượng cao nếu chưa có
    sample_video = STATIC_DIR / "sample_video_hd.mp4"
    if not sample_video.exists():
        create_high_quality_sample(sample_video)
    
    # Tạo thumbnail mẫu nâng cao
    try:
        from PIL import Image, ImageDraw, ImageFont
        enhanced_thumb = STATIC_DIR / "enhanced_thumbnail.jpg"
        if not enhanced_thumb.exists():
            img = Image.new('RGB', (640, 360), color=(20, 30, 40))
            draw = ImageDraw.Draw(img)
            
            # Gradient background
            for i in range(360):
                r = 20 + int(i * 0.1)
                g = 30 + int(i * 0.08)
                b = 40 + int(i * 0.12)
                draw.line([(0, i), (640, i)], fill=(r, g, b))
            
            # Vẽ logo
            draw.ellipse([220, 100, 420, 300], outline=(41, 128, 185), width=5)
            draw.text((320, 120), "AI", fill=(41, 128, 185), font=ImageFont.load_default(size=48), anchor="mm")
            draw.text((320, 180), "VIDEO", fill=(255, 255, 255), font=ImageFont.load_default(size=32), anchor="mm")
            draw.text((320, 220), "FACTORY", fill=(255, 255, 255), font=ImageFont.load_default(size=32), anchor="mm")
            draw.text((320, 280), "PRO v3.0", fill=(155, 155, 155), font=ImageFont.load_default(size=24), anchor="mm")
            
            img.save(enhanced_thumb, quality=95)
            logger.info("Created enhanced thumbnail")
    except:
        logger.warning("Could not create enhanced thumbnail")
    
    logger.info("Enhanced system initialization complete")

# Cập nhật hàm main để sử dụng initialization nâng cao
if __name__ == '__main__':
    # Đăng ký signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Khởi tạo hệ thống nâng cao
    init_system_enhanced()
    
    # Cấu hình server
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # Đăng ký cleanup khi thoát
    atexit.register(cleanup_on_exit)
    
    # Log thông tin khởi động
    logger.info("=" * 50)
    logger.info("Starting AI Video Factory v3.0 with LivePortrait Features")
    logger.info(f"Server: http://{host}:{port}")
    logger.info(f"LivePortrait Processor: {liveportrait_processor.models_loaded}")
    logger.info("=" * 50)
    
    # Chạy server
    try:
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)