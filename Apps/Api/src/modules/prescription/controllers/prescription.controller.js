import { asyncHandler } from "../../../utils/AsyncHandler.js"
import { ApiError } from "../../../utils/ApiError.js"
import { ApiResponse } from "../../../utils/ApiResponse.js"
import { User } from "../../../models/user.models.js"
import { Prescription } from "../../../models/prescription.models.js"
import jwt from "jsonwebtoken";
import { uploadOnCloudinary } from "../../../utils/uploadOnCloudinary.js"

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
        throw new Error(500, "Error in uploading on  cloudinary");
    }

    const imageUrl = uploadFile?.url

    const prescription = await Prescription.create({
        user: user._id,
        imageUrl: imageUrl,
    })

    if (!prescription) {
        throw new ApiError(500, "Failed to create prescription");
    }

    return res
        .status(200)
        .json(
            new ApiResponse(
                200, prescription, "prescription created successfully"
            )
        )
})