import mongoose, { model, Schema } from "mongoose";

const medicineSchema = new Schema({
    name: { type: String, required: true, trim: true },
    genericName: { type: String, trim: true },
    dosage: { type: String, trim: true },
    frequency: { type: String, trim: true },
    duration: { type: String, trim: true },
    instructions: { type: String, trim: true },
    confidence: { type: Number, min: 0, max: 1 },
    needsReview: { type: Boolean, default: false },
}, { _id: true , timestamps: true });

const prescriptionSchema = new Schema({
    user: { type: Schema.Types.ObjectId, ref: "User", required: true, index: true },
    imageUrl: { type: String, required: true },
    thumbnailUrl: { type: String },
    rawText: { type: String },
    status: { type: String, enum: ["PENDING", "PROCESSING", "COMPLETED", "FAILED"], default: "PENDING", index: true },
    progress: { type: Number, default: 0, min: 0, max: 100 }, 
    confidenceScore: { type: Number, min: 0, max: 1 },
    errorMessage: { type: String },
    retryCount: { type: Number, default: 0 },                   
    reviewedByUser: { type: Boolean, default: false },               
    medicines: [medicineSchema],
    isDeleted: { type: Boolean, default: false, index: true },  
}, { timestamps: true });

const Prescription=model("Prescription",prescriptionSchema)

export {Prescription}