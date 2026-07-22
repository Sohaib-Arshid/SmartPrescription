import mongoose from "mongoose";
import { DB_NAME } from "../constants/index.js";

export const connectdb = async () => {
    try {
       const connectiondb = await mongoose.connect(`${process.env.MONGODB_URI}/${DB_NAME}`)
       console.log(`Database are connectd !! HOST ${connectiondb.connection.host}`);
    } catch (error) {
        console.error("Error", error)
        process.exit(1)
    }
}

export default connectdb