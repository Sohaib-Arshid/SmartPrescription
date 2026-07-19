import { Worker } from "bullmq";
import { redis } from "../config/redis.js";
import { Prescription } from "../models/prescription.models.js";
import { processPrescription } from "../services/ml/ml.service.js";

const worker = new Worker(
    "prescription-processing",

    async (job) => {
        try {
            const { prescriptionId } = job.data;

            const prescription = await Prescription.findById(prescriptionId);

            if (!prescription) {
                throw new Error("Prescription not found");
            }

            prescription.status = "PROCESSING";
            prescription.progress = 20;

            await prescription.save();

            const result = await processPrescription(
                prescription.imageUrl,
                prescription._id.toString()
            );

            prescription.rawText = result.rawText;

            prescription.parsedData = result.parsedData
            
            if (result.parsedData?.medicines) {
                prescription.medicines = result.parsedData.medicines;
            }

            prescription.confidenceScore = result.confidenceScore ?? 1;

            prescription.status = "COMPLETED";
            prescription.progress = 100;

            await prescription.save();
            console.log(result);
            

            console.log("Prescription Processed Successfully");
        } catch (error) {
            console.error("❌ Job failed:", error.message);
            console.error(error.stack);

            try {
                const prescription = await Prescription.findById(
                    job.data.prescriptionId
                );

                if (prescription) {
                    prescription.status = "FAILED";
                    prescription.errorMessage = error.message;
                    prescription.retryCount += 1;

                    await prescription.save();
                }
            } catch (dbError) {
                console.error("Failed to update DB:", dbError);
            }

            throw error;
        }
    },

    {
        connection: redis,
    }
);

export { worker };