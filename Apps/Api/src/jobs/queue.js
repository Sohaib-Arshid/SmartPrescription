import { Queue } from "bullmq"
import { redis } from "../config/redis"

const prescriptionQueue = new Queue(
    "prescription-processing",
    {
        connection: redis,
    }
)

export { prescriptionQueue };