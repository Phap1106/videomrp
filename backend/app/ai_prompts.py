"""
AI Prompt Templates for video editing and content analysis
"""

from typing import Dict, List, Any
import json


class VideoPrompts:
    """Collection of AI prompts for different video types and platforms"""
    
    # ================ CONTENT ANALYSIS PROMPTS ================
    
    @staticmethod
    def get_content_analysis_prompt(transcript: str, platform: str, video_type: str) -> str:
        """Get prompt for analyzing video content"""
        platform_names = {
            "tiktok": "TikTok",
            "youtube": "YouTube",
            "facebook": "Facebook",
            "instagram": "Instagram",
            "douyin": "Douyin",
            "twitter": "Twitter/X"
        }
        
        video_type_names = {
            "short": "Short Form (15-60 seconds)",
            "highlight": "Highlight Reel (2-5 minutes)",
            "viral": "Viral Content (30-90 seconds)",
            "meme": "Meme Video (15-30 seconds)",
            "full": "Full Length (original duration)",
            "reel": "Reel/Story (15-90 seconds)"
        }
        
        platform_name = platform_names.get(platform.lower(), platform.upper())
        video_type_name = video_type_names.get(video_type.lower(), video_type)
        
        return f"""
        Bạn là một chuyên gia phân tích video với 10 năm kinh nghiệm cho nền tảng {platform_name}.
        
        NHIỆM VỤ CỦA BẠN:
        1. Phân tích transcript video dưới đây
        2. Đề xuất cách cắt ghép để tạo video kiểu {video_type_name}
        3. Đánh giá rủi ro bản quyền
        4. Gợi ý hashtag và tiêu đề phù hợp với {platform_name}
        5. Xác định các khoảnh khắc quan trọng nhất
        
        TRANSCRIPT VIDEO:
        {transcript[:3000]}...
        
        YÊU CẦU ĐẦU RA (JSON FORMAT):
        {{
            "summary": "Tóm tắt nội dung video (50-100 từ)",
            "category": "Thể loại chính (giải trí, giáo dục, tin tức, âm nhạc, hài, gameplay, review, vlog, cooking, travel, fashion, beauty)",
            "subcategory": "Thể loại phụ (nếu có)",
            "mood": "Tâm trạng chính (vui, buồn, kích thích, thư giãn, hài hước, nghiêm túc, lãng mạn, hành động)",
            "key_moments": [
                {{
                    "start": seconds,
                    "end": seconds,
                    "description": "Mô tả chi tiết cảnh này",
                    "importance": "high/medium/low",
                    "reason": "Tại sao đây là khoảnh khắc quan trọng (hook, emotional peak, surprising moment, etc.)",
                    "suggested_action": "keep/cut/enhance/speed_up"
                }}
            ],
            "sensitive_content": ["Danh sách nội dung nhạy cảm nếu có (violence, nudity, political, etc.)"],
            "copyright_hints": ["Dấu hiệu bản quyền: nhạc nền, logo thương hiệu, watermark, đoạn hội thoại đặc trưng"],
            "viral_potential": 0-100,
            "recommended_duration": seconds,
            "best_clips": [
                {{
                    "start": seconds,
                    "end": seconds,
                    "reason": "Lý do nên giữ lại clip này"
                }}
            ],
            "editing_style": "fast_paced/medium/slow_cinematic",
            "hashtag_suggestions": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"],
            "title_suggestions": ["Tiêu đề 1", "Tiêu đề 2", "Tiêu đề 3"],
            "thumbnail_ideas": ["Ý tưởng thumbnail 1", "Ý tưởng thumbnail 2"],
            "platform_specific_notes": "Ghi chú đặc biệt cho {platform_name}",
            "engagement_tips": ["Mẹo tăng engagement 1", "Mẹo tăng engagement 2"],
            "cta_suggestions": ["Call-to-action đề xuất"]
        }}
        
        QUAN TRỌNG CHO {platform_name.upper()}:
        - Tuân thủ chính sách cộng đồng của {platform_name}
        - Tránh vi phạm bản quyền bằng mọi giá
        - Ưu tiên các khoảnh khắc gây ấn tượng mạnh trong 3 giây đầu
        - Đảm bảo video có hook (mở đầu thu hút) và CTA (kêu gọi hành động) rõ ràng
        - Tối ưu cho thuật toán {platform_name}
        
        LƯU Ý CHO {video_type_name.upper()}:
        - Độ dài lý tưởng: {VideoPrompts._get_ideal_duration(video_type)}
        - Nhịp độ: {VideoPrompts._get_pacing(video_type)}
        - Phong cách: {VideoPrompts._get_style(video_type)}
        """
    
    # ================ VIDEO EDITING INSTRUCTION PROMPTS ================
    
    @staticmethod
    def get_editing_instructions_prompt(analysis: Dict[str, Any], platform: str, video_type: str) -> str:
        """Get prompt for generating video editing instructions"""
        
        templates = {
            "tiktok_short": """
            TẠO VIDEO TIKTOK SHORT (15-60s) - CÔNG THỨC THÀNH CÔNG:
            
            1. THỜI LƯỢNG: 15-60 giây (lý tưởng: 21-34s)
            2. TỐC ĐỘ: Nhanh (1.2x-1.5x)
            3. TEXT OVERLAY: Lớn, dễ đọc, emoji phù hợp
            4. CHUYỂN CẢNH: Nhanh, hiệu ứng mượt (zoom, slide, fade)
            5. ÂM THANH: Trending sound hoặc nhạc viral
            6. TỶ LỆ: 9:16 (dọc) - 1080x1920
            7. HOOK: 3 giây đầu phải gây tò mò/sốc
            8. CTA: Kết thúc bằng like, follow, comment, share
            9. HASHTAG: 3-5 hashtag trending + niche
            10. LOẠI BỎ: Đoạn chậm, nhàm chán, dead air
            
            CẤU TRÚC VIDEO:
            - 0-3s: HOOK mạnh (question, surprising fact, before/after)
            - 3-15s: CONTENT chính (giá trị chính)
            - 15-25s: DEVELOPMENT (phát triển nội dung)
            - 25-30s: PAYOFF (kết quả, twist)
            - 30-35s: CTA + HASHTAG
            
            HIỆU ỨNG ĐỀ XUẤT:
            - Text pop-up với timing chính xác
            - Zoom in trên khuôn mặt khi nói điều quan trọng
            - Sound effects: whoosh, ding, swoosh
            - Transition: glitch, zoom, slide
            """,
            
            "youtube_highlight": """
            TẠO YOUTUBE HIGHLIGHT (3-10 phút) - CHUYÊN NGHIỆP:
            
            1. THỜI LƯỢNG: 3-10 phút (lý tưởng: 5-8 phút)
            2. INTRO: 5-10 giây, brand intro
            3. CHAPTERS: Chia chapters rõ ràng
            4. END SCREEN: 10-15 giây cuối
            5. ÂM THANH: Chất lượng cao, background music nhẹ
            6. TỶ LỆ: 16:9 (ngang) - 1920x1080
            7. THUMBNAIL: Thiết kế hấp dẫn, click-worthy
            8. MÔ TẢ: SEO optimized, timestamps, links
            9. CTA: Subscribe, like, bell notification
            10. QUALITY: 1080p 60fps, HDR nếu có
            
            CẤU TRÚC VIDEO:
            - 0-10s: INTRO (hook + giá trị hứa hẹn)
            - 10-60s: TEASER (best moments preview)
            - 1-4p: CONTENT chính (chia thành 3-4 phần)
            - 4-5p: CONCLUSION (tóm tắt + insights)
            - 5-5:30p: OUTRO (CTA + end screen)
            
            KỸ THUẬT EDITING:
            - J-cuts và L-cuts cho chuyển cảnh mượt
            - B-roll footage để minh họa
            - Lower thirds cho thông tin quan trọng
            - Color grading đồng nhất
            - Sound design chuyên nghiệp
            """,
            
            "viral_content": """
            TẠO VIDEO VIRAL (30-90s) - CÔNG THỨC LAN TRUYỀN:
            
            1. HOOK: 3 giây đầu phải gây SHOCK/TÒ MÒ
            2. EMOTION: Kích thích cảm xúc mạnh (cười, ngạc nhiên, tức giận)
            3. STORYTELLING: Cấu trúc 3 hồi rõ ràng
            4. SHAREABILITY: Khiến người xem MUỐN chia sẻ
            5. RELATABILITY: Liên quan đến trải nghiệm chung
            6. TRENDING: Kết hợp trend hiện tại
            7. CTA: Share, tag bạn bè, duet
            8. THỜI LƯỢNG: 30-90 giây (tối ưu retention)
            
            CÔNG THỨC VIRAL:
            - 0-3s: CÂU HỎI/SỐC (Làm thế nào...? Bạn sẽ không tin...)
            - 3-15s: XÂY DỰNG (Tình huống, vấn đề)
            - 15-45s: CAO TRÀO (Giải pháp, twist, bất ngờ)
            - 45-60s: KẾT THÚC + CTA (Bài học, kêu gọi)
            
            YẾU TỐ VIRAL:
            - Unexpected twist
            - Emotional rollercoaster
            - Practical value
            - Social currency
            - Public visibility
            """,
            
            "meme_video": """
            TẠO VIDEO MEME (15-30s) - HÀI HƯỚC + SHAREABLE:
            
            1. CAPTION: Hài hước, dễ hiểu, relatable
            2. EFFECTS: Zoom, shake, freeze frame
            3. MUSIC: Meme sounds (oh no, sad violin, etc.)
            4. TIMING: Chính xác với nhạc/beat
            5. TEMPLATE: Sử dụng meme template phổ biến
            6. PUNCHLINE: Bất ngờ, hài hước
            7. DURATION: 15-30 giây (ngắn gọn)
            8. END: Kết thúc đột ngột hoặc loop
            
            TEMPLATE PHỔ BIẾN:
            1. Surprised Pikachu: 😮 + twist
            2. Distracted Boyfriend: 👀 + temptation
            3. Drake Hotline Bling: 👍👎 comparison
            4. Change My Mind: 🪑 + controversial opinion
            5. Two Buttons: 🤔 + difficult choice
            
            CẤU TRÚC MEME:
            - 0-5s: SETUP (tình huống bình thường)
            - 5-20s: PUNCHLINE (yếu tố bất ngờ/hài)
            - 20-25s: REACTION (phản ứng cường điệu)
            - 25-30s: END SCREEN (text hoặc loop)
            
            HIỆU ỨNG:
            - Text-to-speech giọng robot
            - Subtitles với timing chính xác
            - Green screen effects
            - Sound effects exaggerated
            """,
            
            "facebook_reel": """
            TẠO FACEBOOK REEL (15-90s) - TỐI ƯU ENGAGEMENT:
            
            1. DURATION: 15-90 giây (tối ưu: 30-45s)
            2. RATIO: 9:16 hoặc 1:1
            3. TEXT: Overlay lớn, đọc nhanh
            4. MUSIC: Trending trên Facebook
            5. HASHTAG: #viral #fyp #trending + niche
            6. CTA: Share, follow page, visit link
            7. MOBILE: Tối ưu cho mobile viewing
            8. AUTOPLAY: Hook trong 1-2s đầu
            
            ĐẶC ĐIỂM FACEBOOK:
            - Thuật toán ưu tiên video native
            - Engagement > Views (reactions, comments, shares)
            - Giá trị giải trí hoặc thông tin hữu ích
            - Cộng đồng tập trung theo interest
            
            CẤU TRÚC:
            - 0-2s: VISUAL HOOK (hình ảnh ấn tượng)
            - 2-10s: VALUE PROPOSITION (lý do xem)
            - 10-30s: CONTENT DELIVERY (nội dung chính)
            - 30-40s: ENGAGEMENT ASK (kêu gọi tương tác)
            - 40-45s: CTA CLEAR (follow, share, link)
            """
        }
        
        # Xác định template key
        template_key = f"{platform.lower()}_{video_type.lower()}" 
        if template_key not in templates:
            if platform.lower() == "youtube":
                template_key = "youtube_highlight"
            else:
                template_key = "tiktok_short"
        
        base_template = templates[template_key]
        
        return f"""
        {base_template}
        
        PHÂN TÍCH NỘI DUNG HIỆN CÓ:
        {json.dumps(analysis, ensure_ascii=False, indent=2)}
        
        TẠO INSTRUCTION CHỈNH SỬA VIDEO:
        
        Yêu cầu trả về JSON với format:
        {{
            "total_duration_target": seconds,
            "aspect_ratio": "9:16/16:9/1:1/4:5",
            "target_resolution": "1080x1920/1920x1080/1080x1080",
            "clips": [
                {{
                    "clip_id": 1,
                    "start_time": seconds,
                    "end_time": seconds,
                    "duration": seconds,
                    "action": "keep/cut/speed_up/slow_down/reverse/duplicate",
                    "speed_factor": 1.0,
                    "reason": "Lý do chọn clip này",
                    "effects": ["zoom_in", "text_overlay", "color_filter"],
                    "text_overlay": {{
                        "text": "Nội dung text",
                        "position": "top/center/bottom",
                        "duration": seconds,
                        "style": "large_bold/small_subtle"
                    }},
                    "audio_instruction": {{
                        "action": "keep/replace/enhance/mute",
                        "music": "tên nhạc nếu thay thế",
                        "volume": 0.8,
                        "sound_effects": ["whoosh", "ding"]
                    }},
                    "importance_score": 0-1
                }}
            ],
            "order": [1, 2, 3, ...],
            "transitions": [
                {{
                    "from_clip": 1,
                    "to_clip": 2,
                    "type": "cut/fade/zoom/slide",
                    "duration": 0.5
                }}
            ],
            "platform_specific_settings": {{
                "aspect_ratio": "9:16/16:9/1:1",
                "max_duration": seconds,
                "watermark_removal": true/false,
                "audio_normalization": true/false,
                "caption_style": "burned/separate_file",
                "output_format": "mp4/mov/webm"
            }},
            "final_instructions": [
                "Bước 1: Tải video gốc",
                "Bước 2: Cắt các clip theo timeline",
                "Bước 3: Áp dụng hiệu ứng và text overlay",
                "Bước 4: Thêm nhạc nền và sound effects",
                "Bước 5: Xuất video với settings trên"
            ],
            "quality_checks": [
                "Kiểm tra âm thanh không bị clip",
                "Đảm bảo text readable trên mobile",
                "Kiểm tra màu sắc đồng nhất",
                "Đảm bảm không có watermark",
                "Kiểm tra độ phân giải đúng"
            ]
        }}
        
        LƯU Ý QUAN TRỌNG:
        1. Đảm bảo tổng thời lượng không vượt quá giới hạn của {platform.upper()}
        2. Tuân thủ chính sách bản quyền của {platform.upper()}
        3. Ưu tiên các cảnh có engagement cao (khuôn mặt, cảm xúc, hành động)
        4. Đảm bảo video có flow logic từ đầu đến cuối
        5. Thêm yếu tố bất ngờ để tăng retention rate
        6. Tối ưu cho mobile viewing nếu {platform.upper()} chủ yếu trên mobile
        """
    
    # ================ COPYRIGHT AVOIDANCE PROMPTS ================
    
    @staticmethod
    def get_copyright_avoidance_prompt(content: str) -> str:
        """Get prompt for avoiding copyright issues"""
        return f"""
        PHÂN TÍCH VÀ ĐỀ XUẤT TRÁNH VI PHẠM BẢN QUYỀN:
        
        NỘI DUNG CẦN KIỂM TRA:
        {content[:2000]}...
        
        KIỂM TRA CÁC YẾU TỐ SAU:
        1. NHẠC NỀN: Có sử dụng nhạc có bản quyền không?
        2. HÌNH ẢNH/LOGO: Có logo thương hiệu, sản phẩm nào không?
        3. ĐOẠN HỘI THOẠI: Có trích dẫn phim, chương trình TV không?
        4. WATERMARK: Có watermark của nền tảng khác không?
        5. CONTENT ID: Có nội dung đã đăng ký Content ID không?
        6. VISUAL CONTENT: Có hình ảnh/clip từ nguồn có bản quyền không?
        
        ĐỀ XUẤT CHỈNH SỬA ĐỂ TRÁNH BẢN QUYỀN:
        - Thay thế nhạc bằng nhạc không bản quyền (royalty-free)
        - Blur hoặc crop logo thương hiệu
        - Cắt bỏ watermark hoặc thay thế
        - Thay đổi pitch/tempo của audio gốc
        - Thêm commentary/transformative elements
        - Sử dụng fair use justification
        - Thay đổi context để trở thành transformative work
        
        Trả về JSON:
        {{
            "copyright_risks": [
                {{
                    "type": "music/logo/dialogue/watermark/visual",
                    "timestamp": "vị trí trong video",
                    "description": "Mô tả chi tiết",
                    "severity": "high/medium/low/critical",
                    "confidence": 0-100,
                    "original_source": "Nguồn gốc nếu biết",
                    "suggestion": "Cách xử lý cụ thể",
                    "priority": "immediate/high/medium/low"
                }}
            ],
            "transformative_suggestions": [
                "Thêm commentary phân tích",
                "Thêm text overlay giải thích/giáo dục",
                "Thêm meme elements để biến đổi",
                "Thay đổi context thành review/critique",
                "Sử dụng cho mục đích giáo dục"
            ],
            "safe_to_use_score": 0-100,
            "required_modifications": ["mod1", "mod2", "mod3"],
            "fair_use_arguments": [
                "Purpose: Transformative use for commentary",
                "Nature: Factual/educational content",
                "Amount: Using only necessary portions",
                "Effect: No market harm to original"
            ],
            "alternative_content": [
                "Alternative music suggestions",
                "Alternative visual replacements",
                "Public domain alternatives"
            ]
        }}
        """
    
    # ================ HASHTAG & TITLE GENERATION ================
    
    @staticmethod
    def get_hashtag_generation_prompt(content: str, platform: str) -> str:
        """Get prompt for generating hashtags and titles"""
        platform_hashtag_styles = {
            "tiktok": "Trending hashtags, niche-specific, challenge hashtags, viral sounds",
            "youtube": "SEO-focused, category-based, long-tail keywords, tutorial-focused",
            "facebook": "Community-focused, location-based, interest-based, group-specific",
            "instagram": "Aesthetic, brand-specific, campaign hashtags, photography",
            "douyin": "Chinese trending, local challenges, popular phrases, e-commerce",
            "twitter": "News-focused, trending topics, conversation starters"
        }
        
        platform_name = platform.upper()
        hashtag_style = platform_hashtag_styles.get(platform, "general")
        
        return f"""
        TẠO HASHTAG VÀ TIÊU ĐỀ TỐI ƯU CHO {platform_name}:
        
        NỘI DUNG: {content[:1000]}...
        
        YÊU CẦU TỐI ƯU:
        1. HASHTAG STRATEGY: {hashtag_style}
        2. TITLE: Hấp dẫn, click-worthy, dưới 100 ký tự
        3. DESCRIPTION: SEO-optimized, 150-200 từ, có keywords
        4. KEYWORDS: Từ khóa chính và phụ cho thuật toán
        5. CTA: Call-to-action phù hợp với {platform_name}
        
        FORMAT OUTPUT (JSON):
        {{
            "platform": "{platform}",
            "hashtags": {{
                "trending": ["#hashtag1", "#hashtag2"],
                "niche": ["#hashtag3", "#hashtag4"],
                "brand": ["#hashtag5"],
                "recommended_order": ["#main", "#trending", "#niche"]
            }},
            "titles": [
                {{
                    "title": "Tiêu đề 1",
                    "style": "question/shock/value_proposition",
                    "click_through_rate": "high/medium/low"
                }},
                {{
                    "title": "Tiêu đề 2",
                    "style": "how_to/number_list/secrets",
                    "click_through_rate": "high/medium/low"
                }}
            ],
            "description": "Mô tả video tối ưu SEO...",
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "cta_suggestions": [
                "Like & Follow for more",
                "Comment your thoughts below",
                "Share with friends who need this",
                "Save for later reference"
            ],
            "optimal_posting_time": "Thời gian đăng tốt nhất theo nghiên cứu",
            "engagement_tips": [
                "Mẹo 1: Ask question in first comment",
                "Mẹo 2: Use pinned comment effectively",
                "Mẹo 3: Engage with comments quickly"
            ],
            "seo_optimization": {{
                "meta_description": "SEO meta description",
                "focus_keyphrase": "Từ khóa chính",
                "latent_semantic_indexing": ["LSI keyword 1", "LSI keyword 2"]
            }}
        }}
        
        QUAN TRỌNG CHO {platform_name}:
        - Hashtag phải đang trending trên {platform_name}
        - Tiêu đề phải thu hút click (clickbait nhưng authentic)
        - Tối ưu cho thuật toán {platform_name}
        - Phù hợp với đối tượng người dùng {platform_name}
        - Tuân thủ guidelines của {platform_name}
        """
    
    # ================ HELPER METHODS ================
    
    @staticmethod
    def _get_ideal_duration(video_type: str) -> str:
        durations = {
            "short": "15-60 seconds",
            "highlight": "2-5 minutes",
            "viral": "30-90 seconds",
            "meme": "15-30 seconds",
            "full": "Original duration",
            "reel": "15-90 seconds"
        }
        return durations.get(video_type, "15-60 seconds")
    
    @staticmethod
    def _get_pacing(video_type: str) -> str:
        pacing = {
            "short": "Fast (quick cuts, high energy)",
            "highlight": "Medium (balanced pacing)",
            "viral": "Variable (build up to climax)",
            "meme": "Fast (precise timing with music)",
            "full": "Original pacing",
            "reel": "Medium-fast (engaging throughout)"
        }
        return pacing.get(video_type, "Medium")
    
    @staticmethod
    def _get_style(video_type: str) -> str:
        styles = {
            "short": "Energetic, trending, mobile-optimized",
            "highlight": "Professional, cinematic, informative",
            "viral": "Emotional, surprising, shareable",
            "meme": "Humorous, relatable, template-based",
            "full": "Original style",
            "reel": "Visually appealing, story-driven"
        }
        return styles.get(video_type, "Energetic and engaging")