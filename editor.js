/* ===================================================
   Mockup-73 Core Workspace Operations & Dynamic Logic
   =================================================== */

// Mockup templates data configuration mapping
const mockupsData = {
    "01_business_cards": {
        name: "Business Cards (Double Face)",
        bgImage: "01_business_cards.png",
        placeholders: [
            { id: "card_top_face", name: "Top Card Face", aspectRatio: 16 / 9 },
            { id: "card_bottom_face", name: "Bottom Card Face", aspectRatio: 16 / 9 }
        ]
    },
    "02_poster_flat": {
        name: "Flat Table Poster (A4 Flat)",
        bgImage: "02_poster_flat.png",
        placeholders: [
            { id: "poster_face", name: "Poster Artwork Design", aspectRatio: 215 / 306 }
        ]
    },
    "03_poster_hanging_clips": {
        name: "Poster with Wall Hanging Clips",
        bgImage: "03_poster_hanging_clips.png",
        placeholders: [
            { id: "poster_face", name: "Hanging Poster Artwork", aspectRatio: 207 / 385 }
        ]
    },
    "04_trifold_brochure": {
        name: "Trifold Brochure (3 Panels)",
        bgImage: "04_trifold_brochure.png",
        placeholders: [
            { id: "left_panel", name: "Left Brochure Panel", aspectRatio: 85 / 225 },
            { id: "center_panel", name: "Center Brochure Panel", aspectRatio: 88 / 231 },
            { id: "right_panel", name: "Right Brochure Panel", aspectRatio: 88 / 228 }
        ]
    },
    "05_folded_card_standing": {
        name: "Standing Folded Card / Magazine",
        bgImage: "05_folded_card_standing.png",
        placeholders: [
            { id: "front_cover", name: "Front Cover Artwork", aspectRatio: 127 / 322 }
        ]
    },
    "06_paper_bag_white": {
        name: "Shopping Paper Bag (Clean White)",
        bgImage: "06_paper_bag_white.png",
        placeholders: [
            { id: "bag_front_face", name: "Bag Front Artwork", aspectRatio: 173 / 260 }
        ]
    },
    "07_paper_bag_kraft": {
        name: "Shopping Paper Bag (Rustic Kraft)",
        bgImage: "07_paper_bag_kraft.png",
        placeholders: [
            { id: "bag_front_face", name: "Bag Front Artwork", aspectRatio: 176 / 286 }
        ]
    },
    "08_book_thin": {
        name: "Standing Book / Thin Notebook Cover",
        bgImage: "08_book_thin.png",
        placeholders: [
            { id: "cover_face", name: "Book Cover Design", aspectRatio: 195 / 307 }
        ]
    },
    "10_rollup_banner": {
        name: "Vertical Rollup Stand Banner",
        bgImage: "10_rollup_banner.png",
        placeholders: [
            { id: "banner_face", name: "Banner Full Artwork", aspectRatio: 178 / 414 }
        ]
    }
};

let cropper = null;
let currentActiveInputId = null;
let croppedImagesStorage = {}; // Stores the final cropped images data (Base64)

// Initialize UI selectors dynamically on load
function initApp() {
    const selector = document.getElementById('mockupSelect');
    if (!selector) return;

    selector.innerHTML = '<option value="">-- Choose a Mockup Template --</option>';
    Object.keys(mockupsData).forEach(key => {
        const option = document.createElement('option');
        option.value = key;
        option.textContent = mockupsData[key].name;
        selector.appendChild(option);
    });

    selector.addEventListener('change', handleTemplateChange);
}

// Handle switching templates and generating specific input rows
function handleTemplateChange(e) {
    const templateKey = e.target.value;
    const container = document.getElementById('uploadInputsContainer');
    const generateBtn = document.getElementById('generateBtn');
    const canvas = document.getElementById('workspaceCanvas');
    
    // Reset state
    container.innerHTML = "";
    croppedImagesStorage = {}; 
    generateBtn.disabled = true;

    if (!templateKey) {
        container.innerHTML = '<p class="placeholder-text">Please select a mockup template first.</p>';
        canvas.innerHTML = '<p class="canvas-hint">Your mockup live preview will be displayed here</p>';
        return;
    }

    const template = mockupsData[templateKey];
    
    // Show mockup template background image inside preview workspace
    canvas.innerHTML = `<img src="${template.bgImage}" alt="Template Preview" style="max-width:100%; max-height:100%; object-fit:contain;">`;

    // Create file upload rows based on placeholders needed
    template.placeholders.forEach(ph => {
        const row = document.createElement('div');
        row.className = 'upload-row';
        
        const label = document.createElement('label');
        label.className = 'upload-label';
        label.textContent = ph.name;
        
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.className = 'styled-file-input';
        
        fileInput.addEventListener('change', (event) => {
            if(event.target.files.length > 0) {
                openCropModal(event.target.files[0], ph.aspectRatio, ph.id);
            }
        });

        row.appendChild(label);
        row.appendChild(fileInput);
        container.appendChild(row);
    });
}

// Cropper JS Open Handler Modal
function openCropModal(file, aspect, placeholderId) {
    currentActiveInputId = placeholderId;
    const modal = document.getElementById('cropModal');
    const imageElement = document.getElementById('imageToCrop');
    
    const fileReader = new FileReader();
    fileReader.onload = function(e) {
        imageElement.src = e.target.result;
        modal.classList.add('active');
        
        if (cropper) cropper.destroy();
        
        cropper = new Cropper(imageElement, {
            aspectRatio: aspect,
            viewMode: 1,
            background: false
        });
    };
    fileReader.readAsDataURL(file);
}

// Modal Actions Triggers
document.getElementById('cancelCropBtn').addEventListener('click', () => {
    document.getElementById('cropModal').classList.remove('active');
    if (cropper) cropper.destroy();
});

document.getElementById('saveCropBtn').addEventListener('click', () => {
    if (!cropper) return;
    
    const canvasResult = cropper.getCroppedCanvas();
    const base64Image = canvasResult.toDataURL('image/png');
    
    // Save image asset data safely
    croppedImagesStorage[currentActiveInputId] = base64Image;
    document.getElementById('cropModal').classList.remove('active');
    cropper.destroy();

    // Verify if all required template layers are uploaded to unlock generation button
    const currentSelectedKey = document.getElementById('mockupSelect').value;
    const requiredLayers = mockupsData[currentSelectedKey].placeholders;
    const allUploaded = requiredLayers.every(ph => croppedImagesStorage[ph.id]);
    
    if(allUploaded) {
        document.getElementById('generateBtn').disabled = false;
    }
});

// Run application setup
document.addEventListener('DOMContentLoaded', initApp);


// استماع لحدث الضغط على زر التوليد وإرسال البيانات للباك اند
document.getElementById('generateBtn').addEventListener('click', async () => {
    const currentSelectedKey = document.getElementById('mockupSelect').value;
    const generateBtn = document.getElementById('generateBtn');
    const canvas = document.getElementById('workspaceCanvas');
    
    generateBtn.disabled = true;
    generateBtn.textContent = "Generating...";

    try {
        const response = await fetch('/api/generate', {  // تم تبسيط الرابط ليعمل داخلياً تلقائياً!
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            templateKey: currentSelectedKey,
            images: croppedImagesStorage
        })
    });

        const result = await response.json();

        if (result.success) {
            generateBtn.textContent = "Generate Mockup";
            generateBtn.disabled = false;
            
            // عرض النتيجة النهائية المدمجة في مساحة العمل فوراً للمستخدم ليعاينها!
            canvas.innerHTML = `
                <div style="text-align:center; width:100%; height:100%;">
                    <img src="https://studious-space-orbit-97x4x44wpw692xqqv-5000.app.github.dev/${result.downloadUrl}" alt="Final Mockup" style="max-width:100%; max-height:85%; object-fit:contain;">
                    <br>
                    <a href="https://studious-space-orbit-97x4x44wpw692xqqv-5000.app.github.dev/${result.downloadUrl}" download class="btn btn-purple" style="width:auto; margin-top:10px; padding: 6px 20px;">Download High-Res Mockup</a>
                </div>
            `;
        } else {
            alert("Generation failed: " + result.error);
            generateBtn.textContent = "Generate Mockup";
            generateBtn.disabled = false;
        }
    } catch (error) {
        console.error(error);
        alert("Error connecting to backend server.");
        generateBtn.textContent = "Generate Mockup";
        generateBtn.disabled = false;
    }
});