import {Router} from "express"
import { upload } from "../../../middlewares/multer.middleware.js"
import { verifyJWT } from "../../../middlewares/auth.middleware.js"
import { Prescription } from "../../../models/prescription.models.js"
import {uploadPrescription , getPrescriptionStatus} from "../controllers/prescription.controller.js"

const router = Router()

router.route("/upload").post(verifyJWT ,upload.single("prescription") , uploadPrescription)
router.route("/:id/status").get(verifyJWT, getPrescriptionStatus)

export default router