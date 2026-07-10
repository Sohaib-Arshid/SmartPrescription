import {Router} from "express"
import { upload } from "../../../middlewares/multer.middleware.js"
import { verifyJWT } from "../../../middlewares/auth.middleware.js"
import { Prescription } from "../../../models/prescription.models.js"
import {uploadPrescription} from "../controllers/prescription.controller.js"

const router = Router()

router.route("/upload").post(verifyJWT ,upload.single(Prescription) , uploadPrescription)

export default router