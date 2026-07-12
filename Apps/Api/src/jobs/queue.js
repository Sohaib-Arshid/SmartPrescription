import { Queue } from "bullmq"
import { redis } from "../config/redis"

const prescriptionQueue = new Queue(
    "prescription-processing",
    {
        connection: redis,
    }
)

export const addPrescriptionJob = async (prescriptionId , imageUrl)=>{
    return await prescriptionQueue.add("process", {
        prescriptionId,
        imageUrl
    })
}
export { prescriptionQueue };