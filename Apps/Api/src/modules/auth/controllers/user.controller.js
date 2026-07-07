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
            new ApiResponse(200, {}, "user logout successfully")
        )
})

const refreshAccessToken = asyncHandler(async (req, res) => {

    const token = req.cookie?.refreshToken || req.body.refreshToken

    if (!token) {
        throw new ApiError(401, "unauthrized access")
    }

    const verifyedToken = jwt.veriy(token, proccess.env.REFRESH_TOKEN_SECRET)

    const user = await User.findById(verifyedToken._id).select("+refreshToken");

    if (incomingRefreshToken !== user.refreshToken) {
        throw new ApiError(401, "Refresh token is expired or used");
    }

    const { accessToken, refreshToken } = await generateAccessAndRefreshToken(user._id);

    const cookieOption = {
        httpOnly: true,
        secure: true
    }

    return res
        .status(200)
        .cookie("accessToken", accessToken, cookieOption)
        .cookie("refreshToken", refreshToken, cookieOption)
        .json(
            new ApiResponse(
                200,
                {
                    accessToken,
                    refreshToken
                },
                "Access token refreshed successfully"
            )
        );
})

const getCurrentUser = asyncHandler(async (req, res) => {
    return res.status(200).json(
        new ApiResponse(
            200,
            req.user,
            "Current user fetched successfully"
        )
    )
})

const updatePassword = asyncHandler(async (req, res) => {
    const { oldPassword, newPassword } = req.body

    if (!oldPassword || !newPassword) {
        throw new ApiError(400, "old Password and new password are required")
    }

    const user = await User.findById(req.user._id)
    if (!user) {
        throw new ApiError(401, "this user not exist")
    }

    const isPasswordCorrect = await user.isPasswordCorrect(oldPassword)

    if (!isPasswordCorrect) {
        throw new ApiError(401, "invalid credentials")
    }

    user.password = newPassword
    await user.save();

    return res
        .status(200)
        .json(
            new ApiResponse(200, "password change successfully")
        )
})

const updateAccountDetailes = asyncHandler(async (req, res) => {
    const { name, email } = req.body

    if (!name || !email) {
        throw new ApiError(400, "Email or password are required")
    }

    const user = await User.findByIdAndUpdate(req.user?._id, { $set: { name, email } }, { new: true }).select("-password")
    return res.status(200).json(
        new ApiResponse(200, user, "Account details updated successfully")
    )
})

export { register, login, logout, getCurrentUser, updatePassword ,updateAccountDetailes }