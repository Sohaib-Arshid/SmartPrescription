import { redis } from "../config/redis";
import { Worker } from "bullmq";
import { Prescription } from "../models/prescription.models";
import { ApiError } from "../../../utils/ApiError.js"

const worker = new Worker(
    "prescription-processing",
    async (job) => {
        const { prescriptionId } = job.data
        
        const prescription = await Prescription.findById(prescriptionId)
        if(!prescription){
            throw new ApiError(401 , null , "prescription not found")
        }
        prescription.status = "PROCESSING",
        prescription.progress = 20
        await prescription.save()
    }
)