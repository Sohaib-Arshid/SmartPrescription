import { asyncHandler } from "../utils/AsyncHandler.js"
import { ApiError } from "../utils/ApiError.js"
import { ApiResponse } from "../utils/ApiResponse.js"
import { User } from "../models/user.models"
import jwt from "jsonwebtoken"
const verifyJWT = asyncHandler(async (req, res,next) => {

    try {
        const token = req.cookies?.accessToken || req.header("Authorization")?.replace("Bearer ", "");

        if (!token) {
            throw new ApiError(401, "unauthorized access")
        }

        const decoded = jwt.verify(token, process.env.ACCESS_TOKEN_SECRET)

        const user = await User.findById(decoded._id).select("-password")

        if (!user) {
            throw new ApiError(
                401, 'User not found'
            )
        }

        req.user = user
        next()
    } catch (error) {

        if (error.name === 'TokenExpiredError') {
            throw new ApiError(401, "Token expired. Please login again.");
        }
        if (error.name === 'JsonWebTokenError') {
            throw new ApiError(401, "Invalid token. Authentication failed.");
        }
        
        throw new ApiError(401, error?.message, "invalid accesss");
    }

    // return res
    //     .status(200)
    //     .json(
    //         new ApiResponse(
    //             200,
    //             updatedPlaylist,
    //             "middleware work successfully"
    //         )
    //     );
})