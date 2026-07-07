import { asyncHandler } from "../utils/AsyncHandler.js"
import { ApiError } from "../utils/ApiError.js"
import { ApiResponse } from "../utils/ApiResponse.js"
import { User } from "../models/user.models.js"

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
    const { email, name, password, role } = req.body

    if (!email || !name || !password || !role) {
        throw new ApiError(403, "these fields are required")
    }

    const existing = await User.findOne({ email })

    if (existing) {
        throw new ApiError(409, "User already exists");
    }
    const registerdUser = await User.create({
        name: name.trim(),
        email: email.trim(),
        password: password.trim(),
    })

    const { accessToken, refreshToken } = await generateAccessAndRefreshToken(registerdUser._id)

    const createdUser = await User.findById(registerdUser._id)
        .select("-password -refreshToken")

    if (!createdUser) {
        throw new ApiError(500, "Something went wrong while registering the user")
    }

    const cookieOption = {
        httpOnly: true,
        secure: true,
        sameSite: "strict",
        maxAge: 7 * 24 * 60 * 60 * 1000
    }

    return res.status(201)
        .cookie("accessToken", accessToken, cookieOption)
        .cookie("refreshToken", refreshToken, cookieOption)
        .json(
            new ApiResponse(201, createdUser,
                accessToken,
                refreshToken,
                "User registered successfully")
        )
})

const login = asyncHandler(async (req, res) => {
    const { email, password } = req.body

    if (!email || !password) {
        throw new ApiError(403, "these fields are required")
    }

    const user = await User.findOne({ email }).select("+refreshToken")

    if (!user) {
        throw new ApiError(401, "user not exist")
    }

    const isPasswordCorrect = await user.isPasswordCorrect(password)

    if (!isPasswordCorrect) {
        throw new ApiError(403, "Invalid credentials");
    }

    const { accessToken, refreshToken } = await generateAccessAndRefreshToken(user._id)

    const logedinUser = await User.findById(user._id).select("-password -refreshToken")

    const cookieOption = {
        httpOnly: true,
        secure: true,
        sameSite: "strict",
        maxAge: 7 * 24 * 60 * 60 * 1000
    }

    return res
        .status(201)
        .cookie("accessToken", accessToken, cookieOption)
        .cookie("refreshToken", refreshToken, cookieOption)
        .json(
            new ApiResponse(201, logedinUser,
                accessToken,
                refreshToken,
                "user loged in successfully")
        )
})

const logout = asyncHandler(async (req, res) => {
    await User.findByIdAndUpdate(
        req.user._id,
        {
            $unset: { accessToken: 1 }
        },
        {
            new: true
        }
    )

    const cookieOption = {
        httpOnly: true,
        secure: true,
    }

    return res 
    .status(200)
    .cookie("accessToken", cookieOption)
    .cookie("refreshToken", cookieOption)
    .json(
        new ApiResponse(200 ,{}, "user logout successfully")
    )
})
