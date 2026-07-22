import {Router} from "express"
import { upload } from "../../../middlewares/multer.middleware.js"
import { verifyJWT } from "../../../middlewares/auth.middleware.js"
import {uploadPrescription , getPrescriptionStatus , conformPrescription , getAllPrescriptions , retry} from "../controllers/prescription.controller.js"

const router = Router()

router.route("/upload").post(verifyJWT ,upload.single("prescription") , uploadPrescription)
router.route("/:id/status").get(verifyJWT, getPrescriptionStatus)
router.route("/:id/confirm").post(verifyJWT, conformPrescription)
router.route("/prescription").get(verifyJWT, getAllPrescriptions)
router.route("/:id/retry").post(verifyJWT, retry)

export default router