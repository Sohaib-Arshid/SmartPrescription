import { cloudinary } from "../config/cloudinary.js";
import fs from "fs"

const uploadOnCloudinary = async (localfile) => {
    if (!localfile) return null

    try {
        const result = await cloudinary.uploader.upload(localfile)

        fs.unlinkSync(localfile)
        return result
    } catch (error) {
        if (fs.existsSync(localfile)) {
            fs.unlinkSync(localfile)
        }
        return null
    }
}

export { uploadOnCloudinary }