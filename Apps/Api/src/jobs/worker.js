import { Worker } from "bullmq";
import { redis } from "../config/redis.js";
import { Prescription } from "../models/prescription.models.js";
import { processPrescription } from "../services/ml/ml.service.js";

const worker = new Worker(
    "prescription-processing",

    async (job) => {
        try {
            const { prescriptionId } = job.data;

            const updatedPrescription = await Prescription.findByIdAndUpdate(
                prescriptionId,
                { status: "PROCESSING", progress: 20 },
                { new: true }
            );

            if (!updatedPrescription) {
                throw new Error("Prescription not found");
            }

            const result = await processPrescription(
                updatedPrescription.imageUrl,
                updatedPrescription._id.toString()
            );

            updatedPrescription.rawText = result.rawText;
            updatedPrescription.parsedData = result.structuredData ?? null;

            if (result.structuredData?.medicines) {
                updatedPrescription.medicines = result.structuredData.medicines;
            }

            updatedPrescription.confidenceScore = result.structuredData?.overallConfidence ?? null;
            updatedPrescription.status = "COMPLETED";
            updatedPrescription.progress = 100;

            await updatedPrescription.save();

            console.log("Prescription Processed Successfully");
        } catch (error) {
            console.error("❌ Job failed:", error.message);
            console.error(error.stack);

            try {
                const prescription = await Prescription.findById(
                    job.data.prescriptionId
                );

                if (prescription) {
                    const isLastAttempt = job.attemptsMade >= (job.opts?.attempts ?? 1);

                    if (isLastAttempt) {
                        prescription.status = "FAILED";
                        prescription.errorMessage = error.message;
                        prescription.retryCount += 1;
                        await prescription.save();
                    }
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