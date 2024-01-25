const express = require("express");
const cors = require("cors");
require("dotenv").config();
console.log("app: ", process.env);
const bodyParser = require("body-parser");
const { processTopics } = require("./processTopics");
const { getTopics } = require("./getTopics");
const { getChangeStream } = require("./mongoClient");
const app = express();
const PORT = process.env.PORT || 4000;

//Middleware
app.use(bodyParser.json());
app.use(cors());

let topics;
let processingTopics = false;
let debounceTimeout = null;
const dbChangeTasks = [];
const callToProccessTopicsTasks = [];
let isTestNewDB = true;

if (isTestNewDB) {
    db = "NewsDive";
} else {
    db = "NewsExperiments";
}

const setupChangeStream = async () => {
    const topicsChangeStream = await getChangeStream(
        db,
        "topics"
    );
    console.log("Change stream is set up");

    topicsChangeStream.on("change", async (change) => {
        console.log("DB change detected");
        // If debounceTimeout exists, clear it to start a new debounce
        if (debounceTimeout) {
            console.log("Clearing debounce timeout");
            clearTimeout(debounceTimeout);
        }

        // Set a new timeout for calling processTopics after a delay
        debounceTimeout = setTimeout(async () => {
            debounceTimeout = null; // Reset the timeout
            if (!dbChangeTasks.length) {
                dbChangeFunction();
            } else {
                // If a task is running, enqueue the new change for processing
                dbChangeTasks.push("job");
                console.log(
                    `Enqueued job. Queue length: ${dbChangeTasks.length}`
                );
            }
        }, 2000); // Adjust the delay time as needed
    });
};

// Call the async function to set up the change stream
setupChangeStream().catch((error) => {
    console.error("Error setting up change stream:", error);
});

const dbChangeFunction = async () => {
    console.log(`Processing task from dbChangeTasks`);
    await processTopics();
    const job = dbChangeTasks.shift();
    if (job) {
        dbChangeFunction();
    }
};

const callToProcessTopicsFunction = async () => {
    console.log(`Processing task from callToProcessTopicsTasks`);
    //await getTopics();
    await processTopics();
    const job = callToProccessTopicsTasks.shift();
    if (job) {
        callToProcessTopicsFunction();
    }
};

// Endpoint to create and process all topics - it is GET because it is an indepotent operation (it does not change beyond the first call)
app.get("/process-topics", async (req, res) => {
    console.log("/process-topics called");
    try {
        if (!callToProccessTopicsTasks.length) {
            callToProcessTopicsFunction();
        } else {
            // If a task is running, enqueue the new change for processing
            callToProccessTopicsTasks.push("job");
            console.log(`Enqueued job. Queue length: ${dbChangeTasks.length}`);
        }

        res.json({ message: "Topics processed successfully" });
    } catch (err) {
        console.log(err);
        res.status(500).json({ message: "Internal server error" });
    }
});

// // Endpoint to get all topics
// app.get("/topics", async (req, res) => {
//     try {
//         const allTopics = await topics.find().toArray();
//         res.json(allTopics);
//     } catch (err) {
//         console.log(err);
//         res.status(500).json({ message: "Internal server error" });
//     }
// });

// // Endpoint to add a new topic
// app.post("/topics", async (req, res) => {
//     const newTopic = req.body;
//     try {
//         const result = await topics.insertOne(newTopic);
//         newTopic._id = result.insertedId;
//         res.status(201).json(newTopic);
//     } catch (err) {
//         console.log(err);
//         res.status(500).json({ message: "Internal server error" });
//     }
// });

// // Endpoint to modify a topic
// app.put("/topics/:id", async (req, res) => {
//     const topicId = req.params.id;
//     const updatedTopic = req.body;
//     try {
//         const result = await topics.findOneAndUpdate(
//             { _id: topicId },
//             { $set: updatedTopic },
//             { returnOriginal: false }
//         );
//         if (result.value) {
//             res.json(result.value);
//         } else {
//             res.status(404).json({ message: "Topic not found" });
//         }
//     } catch (err) {
//         console.log(err);
//         res.status(500).json({ message: "Internal server error" });
//     }
// });

// // Endpoint to delete a topic
// app.delete("/topics/:id", async (req, res) => {
//     const topicId = req.params.id;
//     try {
//         const result = await topics.findOneAndDelete({ _id: topicId });
//         if (result.value) {
//             res.json(result.value);
//         } else {
//             res.status(404).json({ message: "Topic not found" });
//         }
//     } catch (err) {
//         console.log(err);
//         res.status(500).json({ message: "Internal server error" });
//     }
// });

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
