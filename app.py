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

# 9 قوالب معتمدة بإحداثياتها الهندسية الدقيقة
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
            "poster_face": {"type": "flat", "x": 195, "y": 170, "w": 525, "h": 745}
        }
    },
    "03_poster_hanging_clips": {
        "bg_image": "03_poster_hanging_clips.png",
        "placeholders": {
            "poster_face": {"type": "flat", "x": 296, "y": 207, "w": 410, "h": 585}
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
    """تحويل آمن ومضمون للصورة المستقبلة لضمان وجود 4 قنوات ألوان دائماً"""
    if "data:image" in base64_str:
        base64_str = base64_str.split(",")[1]
    img_data = base64.b64decode(base64_str)
    
    pil_img = Image.open(BytesIO(img_data)).convert("RGBA")
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGBA2BGRA)
    return cv_img

@app.route('/api/generate', methods=['POST'])
def generate_mockup():
    try:
        data = request.json
        template_key = data.get("templateKey")
        uploaded_images = data.get("images")

        if not template_key or template_key not in TEMPLATES_CONFIG:
            return jsonify({"success": False, "error": "Invalid template key"}), 400

        config = TEMPLATES_CONFIG[template_key]
        bg_path = config["bg_image"]

        if not os.path.exists(bg_path):
            return jsonify({"success": False, "error": f"Background image {bg_path} not found"}), 404

        base_img = cv2.imread(bg_path, cv2.IMREAD_UNCHANGED)
        if base_img is None:
            return jsonify({"success": False, "error": f"Failed to load background image"}), 500
            
        if len(base_img.shape) == 2 or base_img.shape[2] == 3:
            base_img = cv2.cvtColor(base_img, cv2.COLOR_BGR2BGRA)

        for ph_id, ph_config in config["placeholders"].items():
            if ph_id not in uploaded_images:
                continue

            user_img = decode_base64_image(uploaded_images[ph_id])
            h_user, w_user = user_img.shape[:2]

            if ph_config["type"] == "flat":
                x, y, w, h = ph_config["x"], ph_config["y"], ph_config["w"], ph_config["h"]
                
                resized_user = cv2.resize(user_img, (w, h), interpolation=cv2.INTER_AREA)
                bg_roi = base_img[y:y+h, x:x+w]
                
                if bg_roi.shape[:2] != resized_user.shape[:2]:
                    resized_user = cv2.resize(resized_user, (bg_roi.shape[1], bg_roi.shape[0]), interpolation=cv2.INTER_AREA)
                
                alpha = (resized_user[:, :, 3] / 255.0)[:, :, np.newaxis]
                user_rgb = resized_user[:, :, :3].astype(np.float32)
                bg_rgb = bg_roi[:, :, :3].astype(np.float32)
                
                blended_rgb = (user_rgb * alpha + bg_rgb * (1.0 - alpha)).astype(np.uint8)
                base_img[y:y+h, x:x+w, :3] = blended_rgb
            
            elif ph_config["type"] == "warp":
                pts_src = np.array([[0, 0], [w_user - 1, 0], [w_user - 1, h_user - 1], [0, h_user - 1]], dtype=np.float32)
                pts_dst = np.array(ph_config["coords"], dtype=np.float32)
                
                matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)
                warped_user = cv2.warpPerspective(user_img, matrix, (base_img.shape[1], base_img.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
                
                alpha_warped = (warped_user[:, :, 3] / 255.0)[:, :, np.newaxis]
                user_rgb = warped_user[:, :, :3].astype(np.float32)
                bg_rgb = base_img[:, :, :3].astype(np.float32)
                
                base_img[:, :, :3] = (user_rgb * alpha_warped + bg_rgb * (1.0 - alpha_warped)).astype(np.uint8)

        # حفظ النتيجة النهائية
        output_filename = f"mockup_{template_key}.png"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        cv2.imwrite(output_path, base_img)

        # نعيد المسار النسبي المباشر الذي يفهمه المتصفح ليعمل العرض والتحميل بنجاح
        return jsonify({"success": True, "downloadUrl": f"/outputs/{output_filename}"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 🌟 هذا هو المسار السحري الجديد الذي سيخدم الصور ويجعلها تظهر وتتحمل بنجاح!
@app.route('/outputs/<path:filename>')
def serve_output_files(filename):
    return send_from_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_DIR), filename)

@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename)
    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)