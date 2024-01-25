import clientPromise from "@/lib/mongodb";
import { NextApiRequest, NextApiResponse } from "next";
import fetch from "node-fetch";
import { ObjectId } from "mongodb";
export default async (req: NextApiRequest, res: NextApiResponse) => {
    try {
        const { trackedTopic } = req.body;
        if (!trackedTopic) throw new Error("No tracked topic provided");
        console.log("Adding new tracked topic to database");
        console.log("trackedTopic", trackedTopic);

        const client = await clientPromise;
        const db = client.db("NewsDive"); //client.db("NewsDive");
        const collection = db.collection("topics");

        if (!trackedTopic._id) trackedTopic._id = new ObjectId();

        await collection.insertOne(trackedTopic);
        console.log("Topics saved to database");
        res.setHeader("Content-Type", "application/json");
        res.setHeader("Cache-Control", "public, max-age=0");
        // res.end(JSON.stringify(topicsToSave));
        res.end(JSON.stringify([]));
    } catch (error) {
        console.error(error);
        res.status(500).end();
    }
};
