import { asyncHandler } from "../utils/AsyncHandler.js"
import { ApiError } from "../utils/ApiError.js"
import { ApiResponse } from "../utils/ApiResponse.js"
import { User } from "../models/user.models"

const generateAccessAndRefreshToken = async (userId) => {
    try {
        const user = await User.findById(userId)
        if (!user) {
            throw new ApiError(404, "User not found");
        }
        const accessToken = user.generateAccessToken()
        const refreshToken = user.generateRefreshToken()

        user.refreshToken = refreshToken
        await user.save({ validateBeforeSave: false })
        return { refreshToken, accessToken }
    } catch (error) {
        throw new ApiError(500, "Something went wrong while generating tokens")
    }
}

const register = asyncHandler(async (req, res) => {
    const {email , name , password , role} = req.body

    if(!email || !name || !password || !role){
        throw new ApiError(403 , "these fields are required" )
    }

    const registerUser = await User.create({
        name,
        email,
        password,
        role
    })

    const existing = await User.findOne({ email })
    if (existing) {
        throw new ApiError(409, "User already exists");
    }

    const createdUser = await User.findById(registeredUser._id)
        .select("-password -refreshToken")

    if (!createdUser) {
        throw new ApiError(500, "Something went wrong while registering the user")
    }

    return res.status(201).json(
        new ApiResponse(201, createdUser, "User registered successfully")
    )
})