import os
import base64
import json
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from io import BytesIO
from PIL import Image

app = Flask(__name__)
CORS(app)

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 9 قوالب معتمدة بإحداثياتها الهندسية الدقيقة المستخرجة من كلود
TEMPLATES_CONFIG = {
    "01_business_cards": {
        "bg_image": "01_business_cards.png",
        "placeholders": {
            "card_top_face": {"type": "warp", "coords": [[473,191], [723,281], [538,426], [288,336]]},
            "card_bottom_face": {"type": "warp", "coords": [[391,373], [641,463], [456,608], [206,518]]}
        }
    },
    "02_poster_flat": {
        "bg_image": "02_poster_flat.png",
        "placeholders": {
            "poster_face": {"type": "flat", "x": 292, "y": 247, "w": 215, "h": 306}
        }
    },
    "03_poster_hanging_clips": {
        "bg_image": "03_poster_hanging_clips.png",
        "placeholders": {
            "poster_face": {"type": "flat", "x": 296, "y": 207, "w": 207, "h": 385}
        }
    },
    "04_trifold_brochure": {
        "bg_image": "04_trifold_brochure.png",
        "placeholders": {
            "left_panel": {"type": "warp", "coords": [[269,287], [354,271], [354,496], [269,512]]},
            "center_panel": {"type": "warp", "coords": [[354,271], [442,267], [442,498], [354,496]]},
            "right_panel": {"type": "warp", "coords": [[442,267], [530,287], [530,515], [442,498]]}
        }
    },
    "05_folded_card_standing": {
        "bg_image": "05_folded_card_standing.png",
        "placeholders": {
            "front_cover": {"type": "warp", "coords": [[436,239], [563,220], [563,542], [436,561]]}
        }
    },
    "06_paper_bag_white": {
        "bg_image": "06_paper_bag_white.png",
        "placeholders": {
            "bag_front_face": {"type": "warp", "coords": [[313,295], [486,270], [486,530], [313,555]]}
        }
    },
    "07_paper_bag_kraft": {
        "bg_image": "07_paper_bag_kraft.png",
        "placeholders": {
            "bag_front_face": {"type": "warp", "coords": [[312,284], [488,257], [488,543], [312,570]]}
        }
    },
    "08_book_thin": {
        "bg_image": "08_book_thin.png",
        "placeholders": {
            "cover_face": {"type": "warp", "coords": [[302,246], [497,220], [502,527], [307,553]]}
        }
    },
    "10_rollup_banner": {
        "bg_image": "10_rollup_banner.png",
        "placeholders": {
            "banner_face": {"type": "warp", "coords": [[311,193], [489,193], [489,607], [311,607]]}
        }
    }
}

def decode_base64_image(base64_str):
    """تحويل الصورة المستقبلة من الجافاسكربت (Base64) إلى مصفوفة OpenCV"""
    if "data:image" in base64_str:
        base64_str = base64_str.split(",")[1]
    img_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(img_data)).convert("RGBA")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGBA2BGRA)

@app.route('/api/generate', methods=['POST'])
def generate_mockup():
    try:
        data = request.json
        template_key = data.get("templateKey")
        uploaded_images = data.get("images")  # دكشنري يحتوي على { placeholder_id: base64_str }

        if not template_key or template_key not in TEMPLATES_CONFIG:
            return jsonify({"success": False, "error": "Invalid template key"}), 400

        config = TEMPLATES_CONFIG[template_key]
        bg_path = config["bg_image"]

        if not os.path.exists(bg_path):
            return jsonify({"success": False, "error": f"Background image {bg_path} not found"}), 404

        # قراءة صورة الخلفية النظيفة بصيغة RGBA
        base_img = cv2.imread(bg_path, cv2.IMREAD_UNCHANGED)
        if base_img.shape[2] == 3:
            base_img = cv2.cvtColor(base_img, cv2.COLOR_BGR2BGRA)

        # دمج كل طبقة مرفوعة في مكانها الصحيح
        for ph_id, ph_config in config["placeholders"].items():
            if ph_id not in uploaded_images:
                continue

            user_img = decode_base64_image(uploaded_images[ph_id])
            h_user, w_user = user_img.shape[:2]

            if ph_config["type"] == "flat":
                # الدمج المسطح العادي المباشر
                x, y, w, h = ph_config["x"], ph_config["y"], ph_config["w"], ph_config["h"]
                resized_user = cv2.resize(user_img, (w, h), interpolation=cv2.INTER_AREA)
                
                # فصل قنوات الألوان والشفافية بشكل آمن لمنع أخطاء الـ broadcasting
                alpha = resized_user[:, :, 3] / 255.0
                
                for c in range(0, 3):
                    base_img[y:y+h, x:x+w, c] = (resized_user[:, :, c] * alpha + 
                                                 base_img[y:y+h, x:x+w, c] * (1.0 - alpha)).astype(np.uint8)
            
            elif ph_config["type"] == "warp":
                # الدمج المائل ثنائي الأبعاد باستخدام المنظور (Perspective Transform)
                pts_src = np.array([[0, 0], [w_user - 1, 0], [w_user - 1, h_user - 1], [0, h_user - 1]], dtype=np.float32)
                pts_dst = np.array(ph_config["coords"], dtype=np.float32)
                
                # حساب مصفوفة التحويل الهندسية
                matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)
                
                # تحوير صورة المستخدم لتطابق المنظور المائل
                warped_user = cv2.warpPerspective(user_img, matrix, (base_img.shape[1], base_img.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
                
                # دمج الأجزاء المموهة الشفافة فوق الخلفية
                alpha_warped = warped_user[:, :, 3] / 255.0
                for c in range(0, 3):
                    base_img[:, :, c] = warped_user[:, :, c] * alpha_warped + base_img[:, :, c] * (1.0 - alpha_warped)

        # حفظ النتيجة النهائية
        output_filename = f"mockup_{template_key}.png"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        cv2.imwrite(output_path, base_img)

        return jsonify({"success": True, "downloadUrl": f"/outputs/{output_filename}"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
        
# تأكد أن دالة العرض تبحث في المجلد الصحيح وتمرر الملف مباشرة
# الدالة القديمة (اتركها كما هي)
@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

# 🌟 أضف هذه الدالة الجديدة تحتها مباشرة لخدمة كافة الملفات الأخرى
@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)