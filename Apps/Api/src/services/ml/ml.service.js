import axios from "axios";

const processPrescription = async (imageUrl, prescriptionId) => {
    const response = await axios.post(`${process.env.ML_SERVICE_URL}/process`,
        {
            imageUrl,
            prescriptionId
        }
    )
    return response.data
}

export {processPrescription}