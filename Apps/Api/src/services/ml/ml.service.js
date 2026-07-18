import axios from 'axios';

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8001';

export const processPrescription = async (imageUrl, prescriptionId) => {
    const response = await axios.post(`${ML_SERVICE_URL}/api/v1/process`, {
        imageUrl,
        prescriptionId
    });
    return response.data;
};