import "dotenv/config";
import connectdb from "./db/index.js";
import { app } from "./app.js";
import { worker } from "./jobs/worker.js"

connectdb()
    .then(() => {
        const port = process.env.PORT || 3000
        const server = app.listen(port, () => {
            console.log(`server is listing on ${port}`);
        })
        server.on("error", (error) => {
            console.log("Error in port", error);

        })
    }).catch((error) => {
        console.log("Mongodb connection failed !! ", error);

    })