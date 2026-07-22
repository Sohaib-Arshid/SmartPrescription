import { asyncHandler } from "../../../utils/AsyncHandler.js"
import { ApiError } from "../../../utils/ApiError.js"
import { ApiResponse } from "../../../utils/ApiResponse.js"
import { User } from "../../../models/user.models.js"
import jwt from "jsonwebtoken";

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
        if (error instanceof ApiError) {
            throw error;
        }
        throw new ApiError(500, "Something went wrong while generating tokens")
    }
}

const register = asyncHandler(async (req, res) => {
    const { email, name, password, role } = req.body

    if (!email || !name || !password) {
        throw new ApiError(400, "these fields are required")
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
            new ApiResponse(201,
                {
                    user: createdUser,
                    accessToken,
                    refreshToken,
                },
                "User registered successfully")
        )
})

const login = asyncHandler(async (req, res) => {
    const { email, password } = req.body

    if (!email || !password) {
        throw new ApiError(400, "these fields are required")
    }

    const user = await User.findOne({ email }).select("+refreshToken")

    if (!user) {
        throw new ApiError(401, "user not exist")
    }

    const isPasswordCorrect = await user.isPasswordCorrect(password)

    if (!isPasswordCorrect) {
        throw new ApiError(401, "Invalid credentials");
    }

    const { accessToken, refreshToken } = await generateAccessAndRefreshToken(user._id)

    const loggedInUser = await User.findById(user._id).select("-password -refreshToken")

    const cookieOption = {
        httpOnly: true,
        secure: true,
        sameSite: "strict",
        maxAge: 7 * 24 * 60 * 60 * 1000
    }

    return res
        .status(200)
        .cookie("accessToken", accessToken, cookieOption)
        .cookie("refreshToken", refreshToken, cookieOption)
        .json(
            new ApiResponse(200,
                {
                    user: loggedInUser,
                    accessToken,
                    refreshToken
                },
                "user loged in successfully")
        )
})

const logout = asyncHandler(async (req, res) => {
    await User.findByIdAndUpdate(
        req.user._id,
        {
            $unset: { refreshToken: 1 }
        },
        {
            new: true
        }
    )

    const cookieOptions = {
        httpOnly: true,
        secure: true,
    }

    return res
        .status(200)
        .clearCookie("accessToken", cookieOptions)
        .clearCookie("refreshToken", cookieOptions)
        .json(
            new ApiResponse(200, null, "user logout successfully")
        )
})

const refreshAccessToken = asyncHandler(async (req, res) => {

    const token = req.cookies?.refreshToken || req.body.refreshToken

    if (!token) {
        throw new ApiError(401, "unauthrized access")
    }

    try {
        const verifyedToken = jwt.verify(token, process.env.REFRESH_TOKEN_SECRET)

        const user = await User.findById(verifyedToken._id).select("+refreshToken");

        if (!user) {
            throw new ApiError(401, "User not found");
        }

        if (token !== user.refreshToken) {
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
    } catch (error) {
        if (error instanceof ApiError) {
            throw error;
        }
        throw new ApiError(401, "Invalid or expired refresh token");
    }
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
            new ApiResponse(200, null, "Password changed successfully")
        )
})

const updateAccountDetailes = asyncHandler(async (req, res) => {
    const { name, email } = req.body

    if (!name && !email) {
        throw new ApiError(400, "Email or name are required")
    }

    try {
        const user = await User.findByIdAndUpdate(
            req.user?._id,
            { $set: { name, email } },
            { new: true }
        ).select("-password")
        return res.status(200).json(
            new ApiResponse(200, user, "Account details updated successfully")
        )
    } catch (error) {
        if (error.code === 11000) {
            throw new ApiError(409, "Email is already in use by another account");
        }
        throw error;
    }
})

export { register, login, logout, getCurrentUser, updatePassword, updateAccountDetailes, refreshAccessToken }