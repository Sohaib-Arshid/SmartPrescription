import axios from 'axios';

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8001';
const ML_TIMEOUT_MS = parseInt(process.env.ML_TIMEOUT_MS || '120000', 10);

export const processPrescription = async (imageUrl, prescriptionId) => {
    const response = await axios.post(
        `${ML_SERVICE_URL}/api/v1/process`,
        { imageUrl, prescriptionId },
        { timeout: ML_TIMEOUT_MS }
    );

    const data = response.data;

    if (data.status === 'failed') {
        throw new Error(data.error || 'ML service returned a failure status');
    }

    return data;
};
