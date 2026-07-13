import {Router} from "express"
import { upload } from "../../../middlewares/multer.middleware.js"
import { verifyJWT } from "../../../middlewares/auth.middleware.js"
import { Prescription } from "../../../models/prescription.models.js"
import {uploadPrescription , getPrescriptionStatus , conformPrescription , getAllPrescriptions} from "../controllers/prescription.controller.js"

const router = Router()

router.route("/upload").post(verifyJWT ,upload.single("prescription") , uploadPrescription)
router.route("/:id/status").get(verifyJWT, getPrescriptionStatus)
router.route("/:id/confirm").post(verifyJWT, conformPrescription)
router.route("/prescription").get(verifyJWT, getAllPrescriptions)

export default router