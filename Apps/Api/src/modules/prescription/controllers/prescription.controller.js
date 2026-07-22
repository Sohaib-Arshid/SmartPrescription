import { asyncHandler } from "../../../utils/AsyncHandler.js"
import { ApiError } from "../../../utils/ApiError.js"
import { ApiResponse } from "../../../utils/ApiResponse.js"
import { Prescription } from "../../../models/prescription.models.js"
import { uploadOnCloudinary } from "../../../utils/uploadOnCloudinary.js"
import { addPrescriptionJob } from "../../../jobs/queue.js"

const uploadPrescription = asyncHandler(async (req, res) => {
    const user = req.user

    if (!user) {
        throw new ApiError(401, "unauthrized access")
    }

    const imageFile = req.file?.path

    if (!imageFile) {
        throw new ApiError(400, "prescription image file is requierd");
    }

    const uploadFile = await uploadOnCloudinary(imageFile)

    if (!uploadFile) {
        throw new ApiError(500, "Error in uploading on  cloudinary");
    }

    const imageUrl = uploadFile?.url
    const cloudinaryPublicId = uploadFile?.public_id

    let prescription
    try {
        prescription = await Prescription.create({
            user: user._id,
            imageUrl: imageUrl,
        })
    } catch (dbError) {
        if (cloudinaryPublicId) {
            try {
                const { cloudinary } = await import("../../../config/cloudinary.js")
                await cloudinary.uploader.destroy(cloudinaryPublicId)
            } catch (_) {
                // best-effort cleanup — do not mask the original error
            }
        }
        throw new ApiError(500, "Failed to create prescription");
    }

    try {
        await addPrescriptionJob(prescription._id, prescription.imageUrl)
    } catch (queueError) {
        await Prescription.findByIdAndUpdate(prescription._id, {
            status: "FAILED",
            errorMessage: "Failed to queue processing job. Please retry."
        })
        throw new ApiError(500, "Failed to queue prescription for processing");
    }

    return res
        .status(202)
        .json(
            new ApiResponse(
                202,
                {
                    id: prescription._id,
                    status: prescription.status,
                    message: "Processing started"
                },
                "prescription created successfully"
            )
        )
})

const getPrescriptionStatus = asyncHandler(async (req, res) => {
    const prescriptionId = req.params.id
    if (!prescriptionId) {
        throw new ApiError(400, "prescriptionId not found")
    }

    const user = req.user
    if (!user) {
        throw new ApiError(401, "unauthorized")
    }

    const prescription = await Prescription.findOne({
        _id: prescriptionId,
        isDeleted: false
    })

    if (!prescription) {
        throw new ApiError(404, "prescription not found")
    }

    if (prescription.user.toString() !== user._id.toString()) {
        throw new ApiError(403, "Unauthorized")
    }

    return res
        .status(200)
        .json(
            new ApiResponse(200, {
                id: prescription._id,
                status: prescription.status,
                progress: prescription.progress,
                medicines: prescription.medicines,
                reviewedByUser: prescription.reviewedByUser
            }, "Prescription status fetched")
        )
})

const conformPrescription = asyncHandler(async (req, res) => {
    const prescriptionId = req.params.id
    if (!prescriptionId) {
        throw new ApiError(400, "prescriptionId not found")
    }

    const user = req.user
    if (!user) {
        throw new ApiError(401, "unauthorized")
    }

    const prescription = await Prescription.findOne({
        _id: prescriptionId,
        isDeleted: false
    })

    if (!prescription) {
        throw new ApiError(404, "prescription not found")
    }

    if (prescription.user.toString() !== user._id.toString()) {
        throw new ApiError(403, "Unauthorized")
    }

    if (prescription.status !== "COMPLETED") {
        throw new ApiError(400, "Prescription not processed yet")
    }

    const { medicines } = req.body
    if (!medicines || !Array.isArray(medicines) || medicines.length === 0) {
        throw new ApiError(400, "Medicines array required")
    }

    prescription.medicines = medicines
    prescription.reviewedByUser = true
    await prescription.save()

    return res
        .status(200)
        .json(
            new ApiResponse(200, {
                id: prescription._id,
                reviewedByUser: true,
                medicines: prescription.medicines
            },
                "conformed by user")
        )
})

const getAllPrescriptions = asyncHandler(async (req, res) => {
    const userId = req.user._id

    const ALLOWED_SORT_FIELDS = new Set(["createdAt", "updatedAt", "status"]);

    const {
        page = 1,
        limit = 10,
        sortBy = "createdAt",
        sortType = "desc"
    } = req.query

    if (!ALLOWED_SORT_FIELDS.has(sortBy)) {
        throw new ApiError(400, "Invalid sortBy field");
    }

    const pageNum = Math.max(1, parseInt(page) || 1)
    const limitNum = Math.min(100, Math.max(1, parseInt(limit) || 10))
    const skip = (pageNum - 1) * limitNum

    const sortOrder = sortType === "asc" ? 1 : -1
    const sortStage = { [sortBy]: sortOrder }

    const prescriptions = await Prescription
        .find({
            user: userId,
            isDeleted: false
        })
        .sort(sortStage)
        .skip(skip)
        .limit(limitNum)

    const total = await Prescription.countDocuments({
        user: userId,
        isDeleted: false
    })

    return res.status(200).json(
        new ApiResponse(200, {
            prescriptions,
            total,
            page: pageNum,
            limit: limitNum,
            totalPages: Math.ceil(total / limitNum)
        }, "Prescriptions fetched successfully")
    )
})

const retry = asyncHandler(async (req, res) => {
    const prescriptionId = req.params.id
    if (!prescriptionId) {
        throw new ApiError(400, "prescriptionId not found")
    }

    const user = req.user
    if (!user) {
        throw new ApiError(401, "unauthorized")
    }

    const prescription = await Prescription.findOne({
        _id: prescriptionId,
        isDeleted: false
    })

    if (!prescription) {
        throw new ApiError(404, "prescription not found")
    }

    if (prescription.user.toString() !== user._id.toString()) {
        throw new ApiError(403, "Unauthorized")
    }

    if (
        prescription.status === "COMPLETED" ||
        prescription.status === "PENDING" ||
        prescription.status === "PROCESSING"
    ) {
        throw new ApiError(400, "Only failed prescriptions can be retried")
    }

    if (prescription.retryCount >= 3) {
        throw new ApiError(400, "Max retry limit exceeded (3)")
    }

    prescription.status = "PENDING"
    prescription.progress = 0
    prescription.errorMessage = null
    await prescription.save()

    await addPrescriptionJob(prescription._id, prescription.imageUrl)

    return res.status(202).json(
        new ApiResponse(202, {
            id: prescription._id,
            status: "PENDING",
            message: "Retry started"
        }, "Prescription retry initiated")
    )

})

export { uploadPrescription, getPrescriptionStatus, conformPrescription, getAllPrescriptions, retry }