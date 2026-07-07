import { Router } from "express";
import {
    register,
    login,
    logout,
    refreshAccessToken,
    getCurrentUser,
    updatePassword,
    updateAccountDetailes
} from "../controllers/user.controller.js";

import { verifyJWT } from "../../../middlewares/auth.middleware.js";

const router = Router()

router.route("/register").post(register); 
router.route("/login").post(login);
router.route("/logout").post(verifyJWT,logout);
router.route("/refresh-token").post(refreshAccessToken);
router.route("/current-user").get(verifyJWT,getCurrentUser)
router.route("/change-password").patch(verifyJWT, updatePassword);

export {router}
