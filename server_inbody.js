const express = require('express');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

const upload = multer({ storage: multer.memoryStorage() });

app.post('/api/scan-inbody', upload.single('image'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'Please upload an InBody report image' });
        }

        
        const formData = new FormData();
        formData.append('file', req.file.buffer, {
            filename: req.file.originalname,
            contentType: req.file.mimetype,
        });

        const pythonResponse = await axios.post('http://127.0.0.1:8001/scan-inbody', formData, {
            headers: { ...formData.getHeaders() },
        });

        const ocrData = pythonResponse.data.data;

        // sent to front
        return res.json({
            status: "success",
            requires_user_confirmation: true,
            extracted_metrics: {
                weight_kg: ocrData.weight_kg,
                skeletal_muscle_mass_kg: ocrData.skeletal_muscle_mass_kg,
                body_fat_percent: ocrData.body_fat_percent,
                bmi: ocrData.bmi,
                total_body_water_l: ocrData.total_body_water_l,
                raw_extracted_text: ocrData.raw_text_easyocr
            }
        });

    } catch (error) {
        console.error("InBody Scanning Error:", error.message);
        return res.status(500).json({ 
            error: "error during InBody scanning",
            details: error.response?.data || error.message 
        });
    }
});

app.listen(5001, () => {
    console.log("Backend running on http://localhost:5001");
});