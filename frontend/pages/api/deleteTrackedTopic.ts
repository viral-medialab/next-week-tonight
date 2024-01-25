import clientPromise from "@/lib/mongodb";
import { NextApiRequest, NextApiResponse } from "next";
import fetch from "node-fetch";
import { ObjectId } from "mongodb";
export default async (req: NextApiRequest, res: NextApiResponse) => {
    try {
        const { trackedTopicId, isPinnedTopic } = req.body;
        if (!trackedTopicId) throw new Error("No tracked topic provided");
        console.log("Deleting tracked topic from database");
        console.log("trackedTopicId", trackedTopicId);

        const client = await clientPromise;
        const db = client.db("NewsDive");//client.db("NewsExperiments");
        const collection = db.collection("topics");

        const query = { _id: new ObjectId(trackedTopicId) };

        if (isPinnedTopic) {
            await collection.updateOne(query, {
                $set: { isPinnedTopic: false },
            });
        } else await collection.deleteOne(query);

        console.log("Tracked topic deleted from database");
        res.setHeader("Content-Type", "application/json");
        res.setHeader("Cache-Control", "public, max-age=0");
        // res.end(JSON.stringify(topicsToSave));
        res.end(JSON.stringify([]));
    } catch (error) {
        console.error(error);
        res.status(500).end();
    }
};
