import express from "express";
import cors from "cors";
import cookieParser from "cookie-parser";

const app = express();
app.user(cors({
    origin: process.env.CORS_ORIGIN || "http://localhost:3000",
    credentials: true
}))
app.use(express.json({ limit: "20kb" }));
app.use(express.urlencoded({ extended: true, limit: "20kb" }));
app.use(express.static("public"));
app.use(cookieParser());