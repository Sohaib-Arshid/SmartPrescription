import express from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import { router } from "./modules/auth/routes/auth.routes";

const app = express();
app.use(cors({
    origin: process.env.CORS_ORIGIN || "http://localhost:3000",
    credentials: true
}))
app.use(express.json({ limit: "20kb" }));
app.use(express.urlencoded({ extended: true, limit: "20kb" }));
app.use(express.static("public"));
app.use(cookieParser());

app.use("api/v1/auth" , authRouter);

export { app };