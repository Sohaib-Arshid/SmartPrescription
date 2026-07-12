import { redis } from "../config/redis";
import { Worker } from "bullmq";
import { Prescription } from "../models/prescription.models";
import { ApiError } from "../../../utils/ApiError.js"
import { processPrescription } from "../services/ml/mockML.js"

const worker = new Worker(
    "prescription-processing",
    async (job) => {
        const { prescriptionId } = job.data

        const prescription = await Prescription.findById(prescriptionId)
        if (!prescription) {
            throw new ApiError(401, null, "prescription not found")
        }
        prescription.status = "PROCESSING",
            prescription.progress = 20
        await prescription.save()

        try {
            const result = await processPrescription(prescription.imageUrl)

            prescription.medicines = result.medicines
            prescription.rawText = result.rawText
            prescription.confidenceScore = result.confidenceScore

            prescription.status = "COMPLETED"
            prescription.progress = 100
            await prescription.save()

        } catch (error) {
            prescription.status = "FAILED"
            prescription.errorMessage = error.message
            prescription.retryCount += 1
            await prescription.save()
            throw error
        }
    },
{
    connection: redis
}
)