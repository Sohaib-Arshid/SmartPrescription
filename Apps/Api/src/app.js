import express from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import { router } from "./modules/auth/routes/auth.routes.js";
import prescriptionRouter from "./modules/prescription/routes/prescription.route.js"

const app = express();
app.use(cors({
    origin: (origin, callback) => {
        const allowedOrigin = process.env.CORS_ORIGIN || "http://localhost:3000";
        if (allowedOrigin === "*" || !origin || origin === allowedOrigin) {
            callback(null, origin || "*");
        } else {
            callback(new Error("Not allowed by CORS"));
        }
    },
    credentials: true
}))
app.use(express.json({ limit: "20kb" }));
app.use(express.urlencoded({ extended: true, limit: "20kb" }));
app.use(express.static("public"));
app.use(cookieParser());

app.use("/api/v1/auth" , router);
app.use("/api/v1/prescription" , prescriptionRouter);

export { app };